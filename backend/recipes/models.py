from django.contrib.auth import get_user_model
from django.db import models

from recipes.constants import (INGREDIENT_NAME_MAX_LENGTH,
                               MEASURE_UNIT_MAX_LENGTH, TAG_NAME_MAX_LENGTH,
                               TAG_SLUG_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH)
User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=INGREDIENT_NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MEASURE_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        'Название тега',
        max_length=TAG_NAME_MAX_LENGTH
    )
    slug = models.SlugField(
        'Slug тега',
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        null=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        'Название рецпта',
        max_length=RECIPE_NAME_MAX_LENGTH
    )
    description = models.TextField(
        'Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='recipes/images/'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Тег'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления в мин.'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name}: {self.amount}'
                f'{self.ingredient.measurement_unit} для {self.recipe.name}')


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        verbose_name='Тег'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_recipe_tag'
            )
        ]

    def __str__(self):
        return f'{self.recipe} {self.tag}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество'
    )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранные рецепты'
        verbose_name_plural = 'избранные рецепты'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписан на',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='user_and_following_different'
            ),
        ]
        verbose_name = 'Подписки'
        verbose_name_plural = 'подписки'
