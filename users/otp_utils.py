from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import EmailOTP

# Tunable settings
OTP_COOLDOWN_SECONDS = 60        # minimum gap between 2 OTPs
OTP_WINDOW_MINUTES = 15          # window period
OTP_MAX_PER_WINDOW = 3           # max OTPs per 15 mins


def check_otp_rate_limit(user):
    now = timezone.now()

    # last OTP
    last_otp = EmailOTP.objects.filter(user=user).order_by("-created_at").first()

    # cooldown
    if last_otp:
        diff_seconds = (now - last_otp.created_at).total_seconds()
        if diff_seconds < OTP_COOLDOWN_SECONDS:
            wait = int(OTP_COOLDOWN_SECONDS - diff_seconds)
            raise ValidationError(f"Please wait {wait} seconds before requesting another OTP.")

    # window based limit
    window_start = now - timedelta(minutes=OTP_WINDOW_MINUTES)
    count = EmailOTP.objects.filter(user=user, created_at__gte=window_start).count()

    if count >= OTP_MAX_PER_WINDOW:
        raise ValidationError(
            f"Maximum {OTP_MAX_PER_WINDOW} OTPs allowed in {OTP_WINDOW_MINUTES} minutes. Try again later."
        )

