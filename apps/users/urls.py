from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'register', views.UserRegistrationViewSet, basename='user-register')
router.register(r'login', views.UserLoginViewSet, basename='user-login')
router.register(r'logout', views.UserLogoutViewSet, basename='user-logout')
router.register(r'profile', views.UserProfileViewSet, basename='user-profile')
router.register(r'change-password', views.ChangePasswordViewSet, basename='change-password')
router.register(r'status', views.UserStatusViewSet, basename='user-status')

app_name = 'users'

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # JWT Token refresh (using DRF SimpleJWT's built-in view)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

