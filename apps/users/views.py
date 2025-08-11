from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, extend_schema_view
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    UserStatusSerializer,
    LogoutSerializer
)


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
    ViewSet for user profile management
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request):
        """Get user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request):
        """Update user profile"""
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        summary="Get user status",
        description="Get current user status and basic information",
        responses={200: UserStatusSerializer}
    )
)
class UserStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user status information
    """
    serializer_class = UserStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    def list(self, request):
        """Get current user status"""
        data = {
            'user_id': request.user.id,
            'username': request.user.username,
            'is_authenticated': True,
            'is_active': request.user.is_active,
            'date_joined': request.user.date_joined,
            'last_login': request.user.last_login,
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)