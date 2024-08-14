from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from users.constants import (EMAIL_MAX_LENGTH, FIRST_NAME_MAX_LENGTH,
                             LAST_NAME_MAX_LENGTH, PASSWORD_MAX_LENGHT,
                             ROLE_MAX_LENGTH, USERNAME_MAX_LENGTH)

USER = 'user'
ADMIN = 'admin'


class CystomUser(AbstractUser):
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
    def is_admin(self):
        return self.role == ADMIN or self.is_superuser

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return self.username
