from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='users_groups',
        blank=True,
        help_text='Группы, к которым принадлежит пользователь.',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='users_permissions',
        blank=True,
        help_text='Специальные права доступа пользователя.',
    )

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email