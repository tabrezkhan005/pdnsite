import phonenumbers
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status, views, response, permissions
from rest_framework.throttling import AnonRateThrottle
from .models import User
from .otp import OTPService
from .serializers import (
    OTPRequestSerializer,
    OTPVerifySerializer,
    LoginSerializer,
    UserSerializer,
)


class OTPRequestThrottle(AnonRateThrottle):
    rate = '5/hour'

class LoginThrottle(AnonRateThrottle):
    rate = '10/hour'


def normalize_phone(phone: str) -> str:
    try:
        parsed = phonenumbers.parse(phone, "IN")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return phone


class RequestOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = normalize_phone(serializer.validated_data["phone"])
        
        # We process it whether the user exists or not, so we never reveal if a phone exists
        OTPService.generate_and_send(phone)
        
        return response.Response({"detail": "OTP sent successfully."})


class VerifyOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = normalize_phone(serializer.validated_data["phone"])
        otp = serializer.validated_data["otp"]
        
        if not OTPService.verify(phone, otp):
            return response.Response(
                {"detail": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Log the user in if they exist
        try:
            user = User.objects.get(phone=phone)
            login(request, user)
            
            # Log audit
            from .services import log_audit_event
            log_audit_event(actor=user, action="OTP_LOGIN", ip_address=request.META.get('REMOTE_ADDR'))
            
            return response.Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return response.Response(
                {"detail": "Phone number verified, but no account exists."},
                status=status.HTTP_404_NOT_FOUND
            )


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginThrottle]

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data["user"]
        login(request, user)
        
        from .services import log_audit_event
        log_audit_event(actor=user, action="PASSWORD_LOGIN", ip_address=request.META.get('REMOTE_ADDR'))
        
        return response.Response(UserSerializer(user).data)


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class MeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return response.Response(UserSerializer(request.user).data)


class CSRFView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return response.Response({"detail": "CSRF cookie set"})
