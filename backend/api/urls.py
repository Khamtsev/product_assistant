from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet, recipe_by_short_link)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', CustomUserViewSet, basename='users')
# router_v1.register(r'users/(?P<id>\d+)/subscribe', FollowViewSet, basename='subscribe')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    re_path(r'^s/(?P<short_link>[а-яёА-ЯЁ\-]+)/$', recipe_by_short_link),
]
