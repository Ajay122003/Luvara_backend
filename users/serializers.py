from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, EmailOTP
from utils.email_sender import generate_otp, send_otp_email
from .otp_utils import check_otp_rate_limit

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"]
        )
        user.is_email_verified = False
        user.save()
        return user





class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data["email"]
        password = data["password"]

        # Authenticate
        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        # If email not verified → send OTP now
        if not user.is_email_verified:
            otp = generate_otp()
            EmailOTP.objects.create(user=user, otp=otp)
            send_otp_email(email, otp)

            raise serializers.ValidationError(
                "Email not verified. OTP has been sent. Please verify to continue."
            )

        return user


class LoginOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        email = data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        # Rate limit
        check_otp_rate_limit(user)

        # Generate & store OTP
        otp = generate_otp()
        EmailOTP.objects.create(user=user, otp=otp)

        # Send email
        send_otp_email(email, otp)

        data["user"] = user
        return data


class LoginOTPVerifySerializer(serializers.Serializer):
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

        # mark email verified on first OTP success
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save()

        data["user"] = user
        return data