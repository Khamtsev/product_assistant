from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import FollowViewSet, TagViewSet, CustomUserViewSet

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('users', CustomUserViewSet, basename='users')
router_v1.register(r'users/(?P<id>\d+)/subscribe', FollowViewSet, basename='subscribe')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
