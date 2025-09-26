"""
Authentication views.

Handles HTTP requests and delegates business logic to services.
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request

from user_service.utils import APIResponse
from .serializers import UserRegistrationInputSerializer, UserRegistrationOutputSerializer
from .services import UserRegistrationService, ValidationError

class UserRegistrationView(APIView):
    """
    API view for user registration.

    Handles POST requests to create new user accounts.
    Delegates business logic to UserRegistrationService.
    """
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """
        Create a new user account.

        Args:
            request: HTTP request containing user registration data

        Returns:
            Response: Standardized API response
        """
        # Validate input
        input_serializer = UserRegistrationInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return APIResponse.validation_error(
                "Invalid input data",
                details=input_serializer.errors
            )

        try:
            # Process registration through service layer
            validated_data = input_serializer.validated_data
            user = UserRegistrationService.register_user(
                email=validated_data['email'],
                password=validated_data['password'],
                display_name=validated_data['display_name']
            )

            # Format successful response
            output_serializer = UserRegistrationOutputSerializer({'user': user})
            return APIResponse.created(
                data=output_serializer.data,
                message="User registered successfully"
            )

        except ValidationError as e:
            return APIResponse.bad_request(str(e))
