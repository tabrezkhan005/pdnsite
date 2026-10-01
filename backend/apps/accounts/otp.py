import logging
import random
from typing import Protocol
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class OTPDelivery(Protocol):
    def send_otp(self, phone: str, otp: str) -> None:
        ...

class ConsoleOTPDelivery:
    def send_otp(self, phone: str, otp: str) -> None:
        if settings.DEBUG:
            logger.info(f"OTP for {phone}: {otp}")

class WhatsAppOTPDelivery:
    def send_otp(self, phone: str, otp: str) -> None:
        raise NotImplementedError("WhatsApp OTP delivery not implemented yet (Phase 4).")


def get_otp_delivery() -> OTPDelivery:
    """Factory to get the correct delivery mechanism."""
    if settings.DEBUG:
        return ConsoleOTPDelivery()
    return WhatsAppOTPDelivery()


class OTPService:
    CACHE_TIMEOUT = 300  # 5 minutes
    MAX_ATTEMPTS = 5

    @classmethod
    def generate_and_send(cls, phone: str) -> bool:
        """
        Generate a 6-digit OTP, store hashed in Redis, and send it.
        Return False if rate-limited, True otherwise.
        """
        # Throttling is handled at the DRF view level, but we could add more here
        otp = f"{random.randint(0, 999999):06d}"
        
        # Store OTP and attempt counter in cache
        # Note: We should hash the OTP in production, but for simplicity
        # we just store it securely in redis. Redis is private.
        # But instructions say "stored hashed". Let's hash it.
        from django.contrib.auth.hashers import make_password
        hashed_otp = make_password(otp)
        
        cache.set(f"otp_hash_{phone}", hashed_otp, timeout=cls.CACHE_TIMEOUT)
        cache.set(f"otp_attempts_{phone}", 0, timeout=cls.CACHE_TIMEOUT)
        
        delivery = get_otp_delivery()
        delivery.send_otp(phone, otp)
        return True

    @classmethod
    def verify(cls, phone: str, otp: str) -> bool:
        """
        Verify the given OTP.
        """
        attempts = cache.get(f"otp_attempts_{phone}", default=None)
        if attempts is None or attempts >= cls.MAX_ATTEMPTS:
            # Expired or max attempts reached
            return False
            
        hashed_otp = cache.get(f"otp_hash_{phone}")
        if not hashed_otp:
            return False
            
        from django.contrib.auth.hashers import check_password
        if check_password(otp, hashed_otp):
            # Single use: delete after successful verification
            cache.delete(f"otp_hash_{phone}")
            cache.delete(f"otp_attempts_{phone}")
            return True
        else:
            # Increment attempts
            cache.incr(f"otp_attempts_{phone}")
            return False
