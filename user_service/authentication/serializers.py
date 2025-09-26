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