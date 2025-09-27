"""
Authentication views.

Handles HTTP requests and delegates business logic to services.
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiResponse

from user_service.utils import APIResponse
from .serializers import (
    UserRegistrationInputSerializer,
    UserRegistrationOutputSerializer,
    UserLoginInputSerializer,
    UserLoginOutputSerializer
)
from .services import UserRegistrationService, UserLoginService, ValidationError

@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationView(APIView):
    """
    API view for user registration.

    Handles POST requests to create new user accounts.
    Delegates business logic to UserRegistrationService.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register new user",
        description="Create a new user account with email, password, and display name",
        request=UserRegistrationInputSerializer,
        responses={
            201: OpenApiResponse(response=UserRegistrationOutputSerializer, description="User registered successfully"),
            400: OpenApiResponse(description="Invalid input data or validation error"),
        },
        tags=["Authentication"]
    )
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


@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    """
    API view for user login.

    Handles POST requests to authenticate users and generate tokens.
    Delegates business logic to UserLoginService.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="User login",
        description="Authenticate user with email and password, returns JWT tokens and session profile",
        request=UserLoginInputSerializer,
        responses={
            200: OpenApiResponse(response=UserLoginOutputSerializer, description="Login successful"),
            400: OpenApiResponse(description="Invalid input data"),
            401: OpenApiResponse(description="Invalid email or password"),
            403: OpenApiResponse(description="Account is disabled"),
            429: OpenApiResponse(description="Too many failed login attempts"),
        },
        tags=["Authentication"]
    )
    def post(self, request: Request) -> Response:
        """
        Authenticate user and generate login tokens.

        Args:
            request: HTTP request containing login credentials

        Returns:
            Response: Standardized API response
        """
        # Validate input
        input_serializer = UserLoginInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return APIResponse.validation_error(
                "Invalid input data",
                details=input_serializer.errors
            )

        try:
            # Get client metadata
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Process login through service layer
            validated_data = input_serializer.validated_data
            user, tokens, session_profile = UserLoginService.login_user(
                request=request,
                email=validated_data['email'],
                password=validated_data['password'],
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Format successful response - pass objects directly
            output_serializer = UserLoginOutputSerializer(
                user=user,
                tokens=tokens,
                session_profile=session_profile
            )
            return APIResponse.success(
                data=output_serializer.data,
                message="Login successful"
            )

        except ValidationError as e:
            error_message = str(e)

            # Return specific status codes based on error type
            if "too many failed" in error_message.lower():
                return APIResponse.too_many_requests(error_message)
            elif "invalid email or password" in error_message.lower():
                return APIResponse.unauthorized(error_message)
            elif "account is disabled" in error_message.lower():
                return APIResponse.forbidden(error_message)
            else:
                return APIResponse.bad_request(error_message)

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.

        Args:
            request: HTTP request

        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
