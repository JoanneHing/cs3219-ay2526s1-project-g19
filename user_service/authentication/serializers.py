"""
Authentication serializers.

Thin validation layer for API input/output.
Business logic is handled in services layer.
"""
from rest_framework import serializers
from users.serializers import UserMeSerializer

class UserRegistrationInputSerializer(serializers.Serializer):
    """
    Input serializer for user registration.

    Performs basic field validation only.
    Business logic validation is handled in services.
    """
    email = serializers.EmailField(
        required=True,
        help_text="Valid email address"
    )
    password = serializers.CharField(
        required=True,
        min_length=1,  # Basic validation, detailed in service
        write_only=True,
        help_text="User password"
    )
    display_name = serializers.CharField(
        required=True,
        min_length=1,  # Basic validation, detailed in service
        max_length=100,  # Liberal limit, detailed in service
        help_text="User display name"
    )

class UserRegistrationOutputSerializer(serializers.Serializer):
    """
    Output serializer for user registration response.

    Takes User object and formats it properly.
    """
    user = UserMeSerializer(read_only=True)
    # access_token = serializers.CharField(read_only=True)  # Future JWT token


class UserLoginInputSerializer(serializers.Serializer):
    """
    Input serializer for user login.

    Performs basic field validation only.
    Business logic validation is handled in services.
    """
    email = serializers.EmailField(
        required=True,
        help_text="Valid email address"
    )
    password = serializers.CharField(
        required=True,
        min_length=1,
        write_only=True,
        help_text="User password"
    )

    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower().strip()


class TokensSerializer(serializers.Serializer):
    """
    Serializer for JWT tokens.

    Can serialize both TokenPair dataclass and dictionary formats.
    """
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        """
        Convert TokenPair dataclass or dict to serialized representation.

        Args:
            instance: TokenPair dataclass or dictionary

        Returns:
            dict: Serialized token data
        """
        if hasattr(instance, 'to_dict'):
            # TokenPair dataclass
            return instance.to_dict()
        else:
            # Regular dictionary
            return super().to_representation(instance)


class SessionProfileSerializer(serializers.Serializer):
    """
    Serializer for user session profile information.
    """
    profile_id = serializers.UUIDField(read_only=True)
    session_key = serializers.CharField(source='session.session_key', read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    login_at = serializers.DateTimeField(read_only=True)
    last_activity_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class UserLoginOutputSerializer(serializers.Serializer):
    """
    Output serializer for user login response.

    Returns user profile data, authentication tokens, and session info.
    Can be initialized with either a dict or individual objects.
    """
    user = UserMeSerializer(read_only=True)
    tokens = TokensSerializer(read_only=True)
    session_profile = SessionProfileSerializer(read_only=True)

    def __init__(self, instance=None, user=None, tokens=None, session_profile=None, **kwargs):
        """
        Initialize serializer with either dict or individual objects.

        Args:
            instance: Dict with user, tokens, session_profile keys (traditional way)
            user: User object (direct way)
            tokens: TokenPair object (direct way)
            session_profile: UserSessionProfile object (direct way)
        """
        if instance is None and all(x is not None for x in [user, tokens, session_profile]):
            # Direct object passing
            instance = {
                'user': user,
                'tokens': tokens,
                'session_profile': session_profile
            }
        super().__init__(instance, **kwargs)


