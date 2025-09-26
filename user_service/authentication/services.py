"""
Authentication service layer.

Contains reusable business logic for authentication operations.
"""
import re
import hashlib
from datetime import timedelta
from typing import Optional, Tuple
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.models import Session
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserSessionProfile
from .tokens import TokenPair

User = get_user_model()

class ValidationError(Exception):
    """Custom validation error for business logic."""
    pass

class ValidationService:
    """Reusable validation functions for user data."""

    @staticmethod
    def validate_email_format(email: str, raise_error: bool = False) -> bool:
        """
        Validate email format using basic pattern.

        Args:
            email: Email to validate
            raise_error: If True, raise ValidationError instead of returning False

        Returns:
            bool: True if valid format

        Raises:
            ValidationError: If raise_error=True and validation fails
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))

        if not is_valid and raise_error:
            raise ValidationError("Invalid email format")

        return is_valid

    @staticmethod
    def validate_password_strength(password: str, raise_error: bool = False) -> bool:
        """
        Validate password strength requirements.

        Args:
            password: Password to validate
            raise_error: If True, raise ValidationError instead of returning False

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If raise_error=True and validation fails
        """
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters")

        patterns = [
            (r'[A-Z]', 'Password must contain at least one uppercase letter'),
            (r'[a-z]', 'Password must contain at least one lowercase letter'),
            (r'[0-9]', 'Password must contain at least one number'),
            (r'[!@#$%^&*(),.?":{}|<>]', 'Password must contain at least one special character')
        ]

        for pattern, message in patterns:
            if not re.search(pattern, password):
                errors.append(message)

        is_valid = len(errors) == 0

        if not is_valid and raise_error:
            raise ValidationError('; '.join(errors))

        return is_valid

    @staticmethod
    def validate_display_name_format(display_name: str, raise_error: bool = False) -> bool:
        """
        Validate display name format.

        Args:
            display_name: Display name to validate
            raise_error: If True, raise ValidationError instead of returning False

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If raise_error=True and validation fails
        """
        if not (2 <= len(display_name) <= 50):
            if raise_error:
                raise ValidationError('Display name must be 2-50 characters')
            return False

        pattern = r'^[a-zA-Z0-9\s\-_]+$'
        if not re.match(pattern, display_name):
            if raise_error:
                raise ValidationError(
                    'Display name can only contain alphanumeric characters, spaces, hyphens, and underscores'
                )
            return False

        return True

    @staticmethod
    def validate(email: str, password: str, display_name: str) -> None:
        """
        Validate all user registration data.

        Args:
            email: Email to validate
            password: Password to validate
            display_name: Display name to validate

        Raises:
            ValidationError: If any validation fails
        """
        ValidationService.validate_email_format(email, raise_error=True)
        ValidationService.validate_password_strength(password, raise_error=True)
        ValidationService.validate_display_name_format(display_name, raise_error=True)

class UserRegistrationService:
    """Business logic for user registration."""

    @staticmethod
    def register_user(email: str, password: str, display_name: str) -> AbstractUser:
        """
        Register a new user with comprehensive validation.

        Args:
            email: User's email
            password: User's password
            display_name: User's display name

        Returns:
            User: Created user instance

        Raises:
            ValidationError: If validation fails or user already exists
        """
        # Normalize email
        email = email.lower().strip()

        # Validate all fields (raises ValidationError if invalid)
        ValidationService.validate(email, password, display_name)

        # Check if user already exists
        if User.objects.email_exists(email):
            raise ValidationError('User with this email already exists')

        # Create user using model manager
        try:
            user = User.objects.create_user_account(email, password, display_name)
            return user
        except IntegrityError:
            raise ValidationError('User with this email already exists')


class RateLimitService:
    """Service for handling rate limiting."""

    @staticmethod
    def get_login_attempt_key(ip_address: str) -> str:
        """Generate cache key for login attempts."""
        return f"login_attempts:{ip_address}"

    @staticmethod
    def is_rate_limited(ip_address: str) -> bool:
        """
        Check if IP address is rate limited for login attempts.

        Args:
            ip_address: Client IP address

        Returns:
            bool: True if rate limited, False otherwise
        """
        key = RateLimitService.get_login_attempt_key(ip_address)
        attempts = cache.get(key, 0)
        return attempts >= 5

    @staticmethod
    def increment_login_attempts(ip_address: str) -> int:
        """
        Increment failed login attempts for IP address.

        Args:
            ip_address: Client IP address

        Returns:
            int: Current number of attempts
        """
        key = RateLimitService.get_login_attempt_key(ip_address)
        attempts = cache.get(key, 0) + 1
        cache.set(key, attempts, 900)  # 15 minutes
        return attempts

    @staticmethod
    def reset_login_attempts(ip_address: str) -> None:
        """
        Reset failed login attempts for IP address.

        Args:
            ip_address: Client IP address
        """
        key = RateLimitService.get_login_attempt_key(ip_address)
        cache.delete(key)

class SessionService:
    """Service for managing user sessions using Django sessions + UserSessionProfile."""

    @staticmethod
    def generate_tokens(user: AbstractUser) -> TokenPair:
        """
        Generate JWT access and refresh tokens for user.

        Args:
            user: User instance

        Returns:
            TokenPair: Token pair dataclass with access and refresh tokens
        """
        return TokenPair.generate_for_user(user)

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token for secure storage.

        Args:
            token: Token to hash

        Returns:
            str: Hashed token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    @transaction.atomic
    def create_session_with_profile(
        request,
        user: AbstractUser,
        tokens: TokenPair,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSessionProfile:
        """
        Create a new user session using Django sessions + UserSessionProfile.

        Args:
            request: Django request object
            user: User instance
            tokens: TokenPair with access and refresh tokens
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            UserSessionProfile: Created session profile
        """
        # Invalidate existing active sessions for single concurrent session
        SessionService.invalidate_user_sessions(user)

        # Create Django session by logging in the user
        login(request, user)

        # Set session expiry to 30 days
        request.session.set_expiry(timedelta(days=30))

        # Get the created Django session
        django_session = Session.objects.get(session_key=request.session.session_key)

        # Create UserSessionProfile linked to Django session
        session_profile = UserSessionProfile.objects.create(
            user=user,
            session=django_session,
            refresh_token_hash=SessionService.hash_token(tokens.refresh_token),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return session_profile

    @staticmethod
    def invalidate_user_sessions(user: AbstractUser) -> None:
        """
        Invalidate all sessions for a user.

        Args:
            user: User instance
        """
        # Get all session profiles for the user
        session_profiles = UserSessionProfile.objects.filter(user=user, is_active=True)

        # Invalidate each session profile (this will also delete Django sessions)
        for profile in session_profiles:
            profile.invalidate()

    @staticmethod
    def get_session_profile_by_key(session_key: str) -> Optional[UserSessionProfile]:
        """
        Get session profile by Django session key.

        Args:
            session_key: Django session key

        Returns:
            UserSessionProfile or None: Session profile if found
        """
        try:
            django_session = Session.objects.get(session_key=session_key)
            return UserSessionProfile.objects.get(session=django_session, is_active=True)
        except (Session.DoesNotExist, UserSessionProfile.DoesNotExist):
            return None

    @staticmethod
    def update_session_activity(session_key: str) -> bool:
        """
        Update last activity for a session.

        Args:
            session_key: Django session key

        Returns:
            bool: True if updated successfully
        """
        session_profile = SessionService.get_session_profile_by_key(session_key)
        if session_profile:
            session_profile.update_activity()
            return True
        return False


class UserLoginService:
    """Business logic for user login."""

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[AbstractUser]:
        """
        Authenticate user with email and password.

        Args:
            email: User's email (normalized)
            password: User's password

        Returns:
            User instance if authenticated, None otherwise
        """
        user = authenticate(username=email, password=password)
        return user

    @staticmethod
    def login_user(
        request,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[AbstractUser, TokenPair, UserSessionProfile]:
        """
        Process user login with comprehensive validation and security measures.

        Args:
            request: Django request object
            email: User's email
            password: User's password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple[AbstractUser, TokenPair, UserSessionProfile]: User instance, token pair, and session profile

        Raises:
            ValidationError: If validation fails or authentication fails
        """
        # Normalize email
        email = email.lower().strip()

        # Check rate limiting
        if ip_address and RateLimitService.is_rate_limited(ip_address):
            raise ValidationError('Too many failed login attempts. Please try again later.')

        # Validate email format
        ValidationService.validate_email_format(email, raise_error=True)

        # Check password is not empty
        if not password or not password.strip():
            raise ValidationError('Password is required.')

        # Authenticate user
        user = UserLoginService.authenticate_user(email, password)

        if not user:
            # Increment failed attempts
            if ip_address:
                RateLimitService.increment_login_attempts(ip_address)
            raise ValidationError('Invalid email or password.')

        # Check if user is active
        if not user.is_active:
            raise ValidationError('User account is disabled.')

        # Reset failed attempts on successful login
        if ip_address:
            RateLimitService.reset_login_attempts(ip_address)

        # Generate tokens
        tokens = SessionService.generate_tokens(user)

        # Create session with Django sessions + profile
        session_profile = SessionService.create_session_with_profile(
            request=request,
            user=user,
            tokens=tokens,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return user, tokens, session_profile