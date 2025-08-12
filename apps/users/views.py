from rest_framework import status, viewsets, permissions
from django.shortcuts import get_object_or_404

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    UserStatusSerializer,
    LogoutSerializer
)
from django.contrib.auth import get_user_model


User = get_user_model()

@extend_schema_view(
    create=extend_schema(
        summary="Register a new user",
        description="Create a new user account with email verification",
        request=UserRegistrationSerializer,
        responses={201: UserRegistrationSerializer}
    )
)
class UserRegistrationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user registration
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['post']
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            response_data = {
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(access_token),
                }
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    create=extend_schema(
        summary="User login",
        description="Authenticate user and return JWT tokens",
        request=UserLoginSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user': {'$ref': '#/components/schemas/UserProfile'},
                    'tokens': {
                        'type': 'object',
                        'properties': {
                            'access': {'type': 'string'},
                            'refresh': {'type': 'string'}
                        }
                    }
                }
            }
        }
    )
)
class UserLoginViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user login
    """
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['post']
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            
            if user:
                if user.is_active:
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    access_token = refresh.access_token
                    
                    response_data = {
                        'message': 'Login successful',
                        'user': UserProfileSerializer(user).data,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(access_token),
                        }
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {'error': 'Account is disabled'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            else:
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user logout (no blacklist)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer
    http_method_names = ['post']

    def create(self, request):
        return Response(
            {'message': 'Logout successful (token will expire automatically)'},
            status=status.HTTP_200_OK
        )

@extend_schema_view(
    retrieve=extend_schema(
        summary="Get user profile",
        description="Retrieve authenticated user's profile",
        responses={200: UserProfileSerializer}
    ),
    partial_update=extend_schema(
        summary="Update user profile",
        description="Update authenticated user's profile information",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    )
)
class UserProfileViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user profile management:
    - GET  /api/users/profile/me/    -> retrieve current user
    - PATCH /api/users/profile/me/   -> partial update current user
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # used by serializer.save() when calling .save() without passing instance
        return self.request.user

    @extend_schema(
        summary="Get user profile",
        description="Retrieve authenticated user's profile",
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update user profile",
        description="Update authenticated user's profile information",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['patch'], url_path='me')
    def partial_update_me(self, request):
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)



@extend_schema_view(
    create=extend_schema(
        summary="Change user password",
        description="Change authenticated user's password",
        request=ChangePasswordSerializer,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
)
class ChangePasswordViewSet(viewsets.GenericViewSet):
    """
    ViewSet for changing user password
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if user.check_password(serializer.validated_data['old_password']):
                # Set new password
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                return Response(
                    {'message': 'Password changed successfully'}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Old password is incorrect'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="Get current user status",
        description="Return the authenticated user's status (reads only the fields defined in the serializer).",
        responses={200: "UserStatusSerializer"},
    ),
    retrieve=extend_schema(
        summary="Get user status by id",
        description="Retrieve a user's status by id. Non-staff users can only retrieve their own status.",
        parameters=[
            OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH)
        ],
        responses={200: "UserStatusSerializer"},
    ),
)
class UserStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly viewset that returns only the fields defined in UserStatusSerializer.
    - list -> returns current authenticated user
    - retrieve -> return a user by id (only self or staff)
    """
    serializer_class = UserStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    queryset = User.objects.all()
    lookup_field = "id"  

    def get_queryset(self):
        """
        Keep a permissive queryset for schema generation, but restrict in runtime:
        - for list: only the current user
        - for retrieve: leave queryset as-is (we'll check permission in retrieve)
        """
        if self.action == "list":
            return self.queryset.filter(id=self.request.user.id)
        return self.queryset

    def list(self, request, *args, **kwargs):
        """Return the authenticated user's status using the serializer instance (not dict)."""
        serializer = self.get_serializer(request.user)  # pass instance
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, id: int = None, *args, **kwargs):
        """
        Retrieve by id. Only allow if:
          - requested id == request.user.id  OR
          - request.user.is_staff
        """
        user = get_object_or_404(self.queryset, id=id)

        if user.id != request.user.id and not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(user)  
        return Response(serializer.data, status=status.HTTP_200_OK)