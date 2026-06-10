from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from ragaas.api.serializers.core import RegisterSerializer, TenantSettingsSerializer, TenantSettingsUpdateSerializer
from ragaas.models import Tenant

class RegisterView(generics.CreateAPIView):
    queryset = Tenant.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response({"status": "success", "user": serializer.data}, status=status.HTTP_201_CREATED)
        response.set_cookie(key='access_token', value=str(refresh.access_token), httponly=True, secure=False, samesite='Lax', max_age=7*24*60*60)
        return response

class LoginView(views.APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            response = Response({"status": "success"})
            response.set_cookie(key='access_token', value=str(refresh.access_token), httponly=True, secure=False, samesite='Lax', max_age=7*24*60*60)
            return response
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(views.APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        response = Response({"status": "logged_out"})
        response.delete_cookie('access_token')
        return response

class TenantSettingsView(views.APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        return Response(TenantSettingsSerializer(request.user).data)
    def patch(self, request):
        serializer = TenantSettingsUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(TenantSettingsSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
