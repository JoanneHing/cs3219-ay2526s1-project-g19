import re
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.Serializer):
    """DRF serializer for user registration with built-in validation"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=8, write_only=True)
    display_name = serializers.CharField(required=True, min_length=2, max_length=50)

    def validate_email(self, value):
        """Validate email format and uniqueness"""
        email = value.lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("User with this email already exists")
        return email

    def validate_password(self, value):
        """Validate password strength using DRF validation"""
        patterns = [
            (r'[A-Z]', 'Password must contain at least one uppercase letter'),
            (r'[a-z]', 'Password must contain at least one lowercase letter'),
            (r'[0-9]', 'Password must contain at least one number'),
            (r'[!@#$%^&*(),.?":{}|<>]', 'Password must contain at least one special character')
        ]

        for pattern, message in patterns:
            if not re.search(pattern, value):
                raise serializers.ValidationError(message)

        return value

    def validate_display_name(self, value):
        """Validate display name format"""
        pattern = r'^[a-zA-Z0-9\s\-_]+$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Display name can only contain alphanumeric characters, spaces, hyphens, and underscores"
            )
        return value

    def create(self, validated_data):
        """Create user using validated data"""
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['display_name'],
            is_verified=False
        )
        return user

    def to_representation(self, instance):
        """Custom output representation"""
        return {
            'id': str(instance.id),
            'email': instance.email,
            'display_name': instance.first_name,
            'is_verified': instance.is_verified,
            'created_at': instance.created_at.isoformat()
        }