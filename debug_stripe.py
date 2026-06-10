import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import stripe
from django.conf import settings

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock')
print(f"Using Stripe Key: {stripe.api_key[:10]}...")

price_id = getattr(settings, 'STRIPE_PRICE_START', 'price_mock_start')
print(f"Using Price ID: {price_id}")

try:
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url="http://localhost:5173/dashboard?success=true",
        cancel_url="http://localhost:5173/dashboard?canceled=true",
    )
    print("Success! URL:", session.url)
except Exception as e:
    import traceback
    traceback.print_exc()

