from django.conf import settings
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from recipes.models import Follow, Tag
from api.serializers import (ChangePasswordSerializer, CreateUserSerializer,
                             FollowSerializer, TagSerializer, UserSerializer)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, )
    pagination_class = LimitOffsetPagination
    http_method_names = ('get', 'post', 'delete', 'head', 'put')

    def get_permission(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserSerializer

    @action(detail=False, methods=['post'], permission_classes=(IsAuthenticated,), url_path='set_password')
    def set_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=(IsAuthenticated,), url_path='me')
    def me(self, request):
        user = request.uset
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], permission_classes=(IsAuthenticated,), url_path='me/avatar')
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                avatar_url = f"{settings.MEDIA_URL}{serializer.data.get('avatar')}"
                response_data = {"avatar": avatar_url}
                return Response(response_data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if not user.avatar:
                return Response({'error': 'Аватар не найден.'}, status=status.HTTP_400_BAD_REQUEST)
            user.avatar.delete(save=True)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=(IsAuthenticated,), url_path='subscriptions')
    def subscriptions(self, request):
        user = request.user
        follows = User.objects.filter(following__user=user)
        serializer = FollowSerializer(follows, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            existing_user_serializer = self.get_serializer(existing_user)
            return Response(existing_user_serializer.data, status=status.HTTP_201_CREATED)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class FollowViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = FollowSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        return Follow.objects.all().filter(user_id=user_id)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
