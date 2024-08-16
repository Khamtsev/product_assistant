from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from recipes.constants import (INGREDIENT_NAME_MAX_LENGTH,
                               MEASURE_UNIT_MAX_LENGTH, MIN_AMOUNT,
                               MIN_COOKING_TIME, RECIPE_NAME_MAX_LENGTH,
                               TAG_NAME_MAX_LENGTH, TAG_SLUG_MAX_LENGTH)

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        unique=True
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
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Slug тега',
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True
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
        max_length=RECIPE_NAME_MAX_LENGTH,
        unique=True
    )
    text = models.TextField(
        'Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes'
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
        'Время приготовления в мин.',
        validators=[MinValueValidator(
            MIN_COOKING_TIME,
            message=f'Минимальное время приготовления: {MIN_COOKING_TIME}!'
        )]
    )
    short_link = models.SlugField(
        'Короткая ссылка',
        unique=True,
        blank=True
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        editable=False
    )

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'рецепты'
        ordering = ('-pub_date',)

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
        'Количество',
        validators=[MinValueValidator(
            MIN_AMOUNT,
            message=f'Минимальное количество: {MIN_AMOUNT}!')]
    )

    class Meta:
        verbose_name = 'Количество ингредиентов в рецепте'
        verbose_name_plural = 'количество ингредиентов в рецепте'
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
        on_delete=models.CASCADE,
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
        related_name='carts',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'списки покупок'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
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
