"""
Authentication service layer.

Contains reusable business logic for authentication operations.
"""
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError

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