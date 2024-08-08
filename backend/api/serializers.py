from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Follow, Tag

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            'avatar',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'avatar': {'required': False},
        }

    def validate(self, data):
        username = data.get('username').lower()
        if username == 'me':
            raise serializers.ValidationError(
                'Использовать "me" в качестве username запрещено'
            )
        email = data.get('email').lower()
        user_by_username = User.objects.filter(
            username=username
        ).first()
        user_by_email = User.objects.filter(
            email=email
        ).first()
        if user_by_username or user_by_email:
            if user_by_username != user_by_email:
                raise serializers.ValidationError(
                    'Пользователь с таким email/username уже существует.'
                )
        return data

    def create(self, validatted_data):
        password = validatted_data.pop('password', None)
        avatar = validatted_data.pop('avatar', None)

        user = User(**validatted_data)
        if password:
            user.set_password(password)
        if avatar:
            user.avatar = avatar
        user.save()
        return user

    def to_representation(self, instance):
        representation = {
            'email': instance.email,
            'id': instance.id,
            'username': instance.username,
            'first_name': instance.first_name,
            'last_name': instance.last_name
        }
        return representation


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    current_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return data

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if user.is_anonymous:
                return False
            return Follow.objects.filter(user=user, following=obj).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
    )

    class Meta:
        fields = ('user', 'following')
        model = Follow

    def validate(self, data):
        user = self.context['request'].user
        if user == data['following']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!')
        if Follow.objects.all().filter(user=user, following=data['following']):
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!')
        return data
