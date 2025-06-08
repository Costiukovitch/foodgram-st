from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Пользователь."""

    email = models.EmailField(
        'Параметры для электронной почты',
        db_index=True,
        max_length=254,
        unique=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username