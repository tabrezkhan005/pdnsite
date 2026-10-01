from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "phone", "role"]


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        # In Django, authenticate usually takes username.
        # We need a custom backend if we authenticate with email directly,
        # or we find the user by email first and authenticate.
        # But for simplicity, assuming user is found by email:
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist as e:
            raise serializers.ValidationError("Invalid email or password.") from e

        user = authenticate(username=user_obj.username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        data["user"] = user
        return data
