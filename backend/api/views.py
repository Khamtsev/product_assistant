from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from recipes.models import Follow, Ingredient, Recipe, Tag, ShoppingCart
from api.serializers import (ChangePasswordSerializer, CreateUserSerializer,
                             FollowSerializer, TagSerializer, UserSerializer,
                             IngredientSerializer, RecipeSerializer,
                             RecipeCreateSerializer, UserFollowSerializer,
                             ShoppingCartSerializer, RecipeIngredient)

User = get_user_model()


# class TagViewSet(viewsets.ReadOnlyModelViewSet):
class TagViewSet(viewsets.ModelViewSet):
    """ViewSet для тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


# class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
class IngredientViewSet(viewsets.ModelViewSet):
    """ViewSet для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class CustomUserViewSet(UserViewSet):
    """ViewSet для пользователей."""
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
        """Изменение пароля."""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # @action(detail=False, methods=['get'], permission_classes=(IsAuthenticated,))
    # def me(self, request):
    #     user = request.user
    #     serializer = self.get_serializer(user)
    #     return Response(serializer.data)

    # @action(detail=False, methods=['put', 'delete'], permission_classes=(IsAuthenticated,), url_path='me/avatar')
    # def avatar(self, request):
    #     user = request.user

    #     if request.method == 'PUT':
    #         if 'avatar' not in request.data:
    #             return Response(status=status.HTTP_400_BAD_REQUEST)
    #         serializer = UserSerializer(user, data=request.data, partial=True)
    #         if serializer.is_valid():
    #             serializer.save()
    #             avatar_url = f"{settings.MEDIA_URL}{serializer.data.get('avatar')}"
    #             response_data = {"avatar": avatar_url}
    #             return Response(response_data, status=status.HTTP_200_OK)
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #     elif request.method == 'DELETE':
    #         if not user.avatar:
    #             return Response({'error': 'Аватар не найден.'}, status=status.HTTP_400_BAD_REQUEST)
    #         user.avatar.delete(save=True)
    #         user.avatar = None
    #         user.save()
    #         return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put'], permission_classes=(IsAuthenticated,), url_path='me/avatar')
    def avatar(self, request):
        """Обновление аватара."""
        user = request.user
        if 'avatar' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            avatar_url = f"{settings.MEDIA_URL}{serializer.data.get('avatar')}"
            response_data = {"avatar": avatar_url}
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара."""
        user = request.user
        if not user.avatar:
            return Response({'error': 'Аватар не найден.'}, status=status.HTTP_400_BAD_REQUEST)
        user.avatar.delete(save=True)
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Подписки пользователя."""
        user = request.user
        follows = User.objects.filter(following__user=user)
        page = self.paginate_queryset(follows)
        serializer = UserFollowSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['post'],
            detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id):
        """Подписаться на автора."""
        following = get_object_or_404(User, pk=id)
        serializer = FollowSerializer(
            data={
                'user': request.user.id,
                'following': following.id
            },
            context={
                'request': request,
                'recipes_limit': request.query_params.get('recipes_limit')
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Отменить подписку."""
        following = get_object_or_404(User, pk=id)
        follow = Follow.objects.filter(
            user=request.user,
            following=following
        )
        if follow.exists():
            follow.delete()
            return Response(status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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


# class FollowViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
#     serializer_class = FollowSerializer
#     pk_url_kwarg = 'id'

#     def get_queryset(self):
#         user_id = self.request.user.id
#         return Follow.objects.all().filter(user_id=user_id)

#     def get_object(self, *args, **kwargs):
#         id = self.kwargs.get('id')
#         obj = get_object_or_404(User, id=id)
#         return obj

#     def perform_create(self, serializer):
#         following = self.get_object()
#         serializer.save(user=self.request.user, following=following)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({
                'detail': 'Authentication credentials were not provided.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        serializer = RecipeCreateSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def update(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = RecipeCreateSerializer(
    #         instance, data=request.data, partial=True,
    #         context={'request': request}
    #     )
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Получить коротку ссылку на рецепт."""
        recipe = self.get_object()
        short_url = f'https://{settings.DOMAIN}/s/{recipe.short_link}'
        return Response({'short-link': short_url})

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок."""
        recipe = self.get_object()
        if ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            return Response({
                'detail': 'Recipe already in shopping cart.'
            }, status=status.HTTP_400_BAD_REQUEST)
        shopping_cart = ShoppingCart.objects.create(
            user=request.user, recipe=recipe
        )
        serializer = ShoppingCartSerializer(
            shopping_cart, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        """Удалить рецепт из списка покупок."""
        recipe = self.get_object()
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        )
        if shopping_cart.exists():
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'detail': 'Recipe not found in shopping cart.'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Отправка файла со списком покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_cart = []
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_cart.append(f'{name}: {amount}, {measurement_unit}\n')
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response


def recipe_by_short_link(request, short_link):
    """Редирект с короткой ссылки на рецепт."""
    recipe = get_object_or_404(Recipe.objects, short_link=short_link)
    return redirect(f'http://{settings.DOMAIN}/api/recipes/{recipe.pk}')
