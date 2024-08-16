from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from rest_framework import serializers

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""
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
            'password': {'write_only': True}
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


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения пользователя."""
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
            return (request.user.is_authenticated
                    and Follow.objects.filter(
                        user=request.user, following=obj
                    ).exists())


class UserFollowSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения пользователя и его рецептов."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', None
        )
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMiniSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""
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


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    class Meta:
        model = Follow
        fields = (
            'user',
            'following'
        )
        read_only_fields = (
            'user',
            'following'
        )

    def validate(self, data):
        following = self.context['following']
        user = self.context['request'].user
        if user == following:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Follow.objects.filter(user=user, following=following).exists():
            raise serializers.ValidationError(
                'Нельзя подписаться на этого пользователя!'
            )
        return data

    def to_representation(self, instance):
        return UserFollowSerializer(instance.following,
                                    context=self.context).data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов."""
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class IngredientPostSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов при создании рецепта."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте."""
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения тегов."""
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug'
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов."""
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'text',
            'ingredients',
            'image',
            'tags',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_ingredients(self, obj):
        return IngredientGetSerializer(
            RecipeIngredient.objects.filter(recipe=obj), many=True
        ).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            not user.is_anonymous and Favorite.objects.filter(
                user=user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            not user.is_anonymous and ShoppingCart.objects.filter(
                user=user, recipe=obj
            ).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    ingredients = IngredientPostSerializer(
        many=True, source='recipeingredients'
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'name',
            'text',
            'cooking_time',
            'image',
            'tags',
            'ingredients'
        )

    def validate(self, data):
        if data.get('cooking_time') is None or data.get('cooking_time') < 1:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовления должно быть больше 0.'
            })
        if not data.get('tags'):
            raise serializers.ValidationError({
                'tags': 'Теги должны быть указаны.'
            })
        if len(data.get('tags', [])) != len(set(data.get('tags', []))):
            raise serializers.ValidationError({
                'tags': 'Теги должны быть уникальными.'
            })
        for tag in data.get('tags', []):
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError({
                    'tags': 'Несуществующий тег.'
                })
        if not data.get('image'):
            raise serializers.ValidationError({
                'image': 'Изображение должно быть указано.'
            })
        ingredients = data.get('recipeingredients', [])
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты должны быть указаны.'
            })
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты должны быть уникальными.'
            })
        for ingredient in ingredients:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError({
                    'amount': 'Количество ингредиента должно быть больше 0.'
                })
            if not Ingredient.objects.filter(
                id=ingredient['id']
            ).exists():
                raise serializers.ValidationError({
                    'ingredients': 'Несуществующий ингредиент.'
                })
        return data

    def create_ingredients(self, ingredients, recipe):
        ingredient_list = []
        for ingredient_data in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_data.get('id')
            )
            ingredient_list.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data.get('amount')
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_list)

    @atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredients', [])
        tags_data = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    # @atomic
    # def update(self, instance, validated_data):
    #     instance.image = validated_data.get('image', instance.image)
    #     instance.name = validated_data.get('name', instance.name)
    #     instance.text = validated_data.get('text', instance.text)
    #     instance.cooking_time = validated_data.get('cooking_time',
    #                                                instance.cooking_time)
    #     ingredients_data = validated_data.pop('recipeingredients', [])
    #     if ingredients_data:
    #         instance.ingredients.clear()
    #         self.create_ingredients(ingredients_data, instance)
    #     tags_data = validated_data.pop('tags', [])
    #     if tags_data:
    #         instance.tags.set(tags_data)
    #     return instance
    @atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipeingredients', [])
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.create_ingredients(ingredients_data, instance)
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSerializer(
            instance, context={'request': request}
        ).data


class RecipeMiniSerializer(serializers.ModelSerializer):
    """Сериализатор для для отображения рецептов в укороченной форме."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'user',
            'recipe'
        )

    def validate(self, data):
        request = self.context.get('request')
        if ShoppingCart.objects.filter(
            user=request.user, recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError('Рецепт уже в списке покупок.')
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMiniSerializer(
            instance.recipe, context={'request': request}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с избранными рецептами."""
    class Meta:
        model = Favorite
        fields = (
            'id',
            'user',
            'recipe'
        )

    def validate(self, data):
        request = self.context.get('request')
        if Favorite.objects.filter(
            user=request.user, recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError('Рецепт уже в избранном.')
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeMiniSerializer(
            instance.recipe, context={'request': request}
        ).data
