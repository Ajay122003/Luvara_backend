from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, EmailOTP
from utils.email_sender import generate_otp, send_otp_email

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "password", "username"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        username = validated_data["username"]

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            is_email_verified=False,
        )

        # Generate OTP
        otp = generate_otp()

        # Store OTP
        EmailOTP.objects.create(user=user, otp=otp)

        # Send OTP email
        send_otp_email(email, otp)

        return user


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data["email"]
        otp = data["otp"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        try:
            otp_obj = EmailOTP.objects.filter(user=user).latest("created_at")
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("OTP not found")

        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP expired")

        if otp_obj.otp != otp:
            raise serializers.ValidationError("Invalid OTP")

        user.is_email_verified = True
        user.save()
        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data["email"]
        password = data["password"]

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_email_verified:
            raise serializers.ValidationError("Email not verified. Please verify OTP.")

        return user
