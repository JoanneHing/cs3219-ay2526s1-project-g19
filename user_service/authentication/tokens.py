"""
Token data structures and utilities.

Contains dataclasses and utilities for JWT token management.
"""
from dataclasses import dataclass
from typing import Dict
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken


@dataclass
class TokenPair:
    """
    Dataclass for JWT token pair (access + refresh).

    Provides a clean structure for passing tokens around
    and converting to different formats.
    """
    access_token: str
    refresh_token: str

    def to_dict(self) -> Dict[str, str]:
        """
        Convert token pair to dictionary format.

        Returns:
            Dict[str, str]: Dictionary with access_token and refresh_token keys
        """
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token
        }

    @classmethod
    def generate_for_user(cls, user: AbstractUser, session_profile_id: str) -> 'TokenPair':
        """
        Generate a new token pair for a user with session tracking.

        Args:
            user: User instance to generate tokens for
            session_profile_id: Session profile ID to include in both tokens

        Returns:
            TokenPair: New token pair instance with profile_session_id embedded
        """
        refresh = RefreshToken.for_user(user)

        # Add session profile ID to token payload (appears in both access and refresh tokens)
        refresh['profile_session_id'] = session_profile_id

        return cls(
            access_token=str(refresh.access_token),
            refresh_token=str(refresh)
        )

    def __str__(self) -> str:
        """String representation showing truncated tokens."""
        return f"TokenPair(access={self.access_token[:20]}..., refresh={self.refresh_token[:20]}...)"