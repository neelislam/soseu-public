from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Profile

class PhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1. Check if the 'username' looks like a phone number
        try:
            # Try to find a Profile with this phone number
            profile = Profile.objects.get(phone=username)
            user = profile.user
        except Profile.DoesNotExist:
            # If not found by phone, try standard username check
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        # 2. Check the password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None