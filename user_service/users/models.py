from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.validators import EmailValidator
import uuid

class CustomUserManager(UserManager):
    """Custom manager for User model with additional helper methods."""

    def email_exists(self, email: str) -> bool:
        """
        Check if user exists by email (case-insensitive).

        Args:
            email: Email to check

        Returns:
            True if user exists, False otherwise
        """
        return self.filter(email__iexact=email).exists()

    def create_user_account(self, email: str, password: str, display_name: str):
        """
        Create a new user account with normalized data.

        Args:
            email: User's email address (will be normalized)
            password: User's password (will be hashed)
            display_name: User's display name

        Returns:
            User instance

        Raises:
            IntegrityError: If email already exists
        """
        return self.create_user(
            username=email,
            email=email.lower(),
            password=password,
            first_name=display_name,
            is_verified=False
        )

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.

    Adds UUID primary key, email verification status, and timestamps.
    Uses email as the primary authentication field instead of username.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the user"
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text="Required. Enter a valid email address."
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Optional phone number"
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="User's date of birth"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the user account was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the user account was last updated"
    )

    # Use custom manager
    objects = CustomUserManager()

    # Use email as username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        """String representation of the user."""
        full_name = self.get_full_name()
        return f"{self.email} ({full_name})" if full_name else self.email
    