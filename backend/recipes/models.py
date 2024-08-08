from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from recipes.constants import (INGREDIENT_NAME_MAX_LENGTH,
                               MEASURE_UNIT_MAX_LENGTH, TAG_NAME_MAX_LENGTH,
                               TAG_SLUG_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH,
                               EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH,
                               FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
                               PASSWORD_MAX_LENGHT, ROLE_MAX_LENGTH)

USER = 'user'
ADMIN = 'admin'


class MyUser(AbstractUser):
    ROLES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=EMAIL_MAX_LENGTH,
        unique=True
    )
    username = models.CharField(
        'Уникальный юзернейм',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z'
            )
        ]
    )
    first_name = models.CharField(
        'Имя',
        max_length=FIRST_NAME_MAX_LENGTH
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=LAST_NAME_MAX_LENGTH
    )
    password = models.CharField(
        'Пароль',
        max_length=PASSWORD_MAX_LENGHT
    )
    role = models.CharField(
        'Роль',
        default='user',
        choices=ROLES,
        max_length=ROLE_MAX_LENGTH
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
        default=None
    )

    @property
    def is_user(self):
        return self.role == USER

    @property
    def is_admin(self):
        return self.role == ADMIN

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return self.username


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
        MyUser,
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
        MyUser,
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
        MyUser,
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
        MyUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    following = models.ForeignKey(
        MyUser,
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
