from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated, AllowAny,IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserCreateSerializer

# Create your views here.

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action == 'me':
            return [IsAuthenticated()]
        if self.action == 'list':
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    # Current user data
    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
