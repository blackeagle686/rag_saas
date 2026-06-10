import stripe
from django.conf import settings
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from ragaas.models import Tenant
import uuid
import logging

logger = logging.getLogger(__name__)

# Retrieve keys from settings (which pulls from .env)
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock')
webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_mock')
frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

class CreateCheckoutSessionView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        plan_id = request.data.get('plan_id')
        
        prices = {
            'start': getattr(settings, 'STRIPE_PRICE_START', 'price_mock_start'),
            'mid': getattr(settings, 'STRIPE_PRICE_MID', 'price_mock_mid'),
            'prime': getattr(settings, 'STRIPE_PRICE_PRIME', 'price_mock_prime'),
        }
        
        price_id = prices.get(plan_id)
        if not price_id:
            return Response({"error": "Invalid plan selected"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Pass the tenant ID securely to Stripe so it returns in the webhook
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{frontend_url}/dashboard?success=true",
                cancel_url=f"{frontend_url}/dashboard?canceled=true",
                client_reference_id=request.user.id.hex, 
            )
            return Response({'url': session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StripeWebhookView(views.APIView):
    permission_classes = (AllowAny,)
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 1. Handle Successful Subscription Purchase
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            tenant_id = session.get('client_reference_id')
            subscription_id = session.get('subscription')
            customer_id = session.get('customer')
            
            if not tenant_id:
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
                
            try:
                tenant = Tenant.objects.get(id=uuid.UUID(tenant_id))
                subscription = stripe.Subscription.retrieve(subscription_id)
                price_id = subscription['items']['data'][0]['price']['id']
                
                prices = {
                    getattr(settings, 'STRIPE_PRICE_START', 'price_mock_start'): 'start',
                    getattr(settings, 'STRIPE_PRICE_MID', 'price_mock_mid'): 'mid',
                    getattr(settings, 'STRIPE_PRICE_PRIME', 'price_mock_prime'): 'prime',
                }
                new_plan = prices.get(price_id, 'free')
                
                tenant.stripe_customer_id = customer_id
                tenant.stripe_subscription_id = subscription_id
                tenant.plan = new_plan
                tenant.can_deploy_api = new_plan != 'free' # Enable API deployments
                tenant.save()
                logger.info(f"Tenant {tenant.email} upgraded to {new_plan}")
            except Exception as e:
                logger.error(f"Error processing webhook upgrade: {e}")
                
        # 2. Handle Subscription Cancellation
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            try:
                tenant = Tenant.objects.get(stripe_subscription_id=subscription['id'])
                tenant.plan = 'free'
                tenant.can_deploy_api = False
                tenant.stripe_subscription_id = None
                tenant.save()
                logger.info(f"Tenant {tenant.email} downgraded to free")
            except Tenant.DoesNotExist:
                pass

        return Response({'status': 'success'}, status=status.HTTP_200_OK)
