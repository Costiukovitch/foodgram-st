from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


class User(AbstractUser):
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$'
            ),
        ],
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        default=''
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
        'password',
    ]

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    author = models.ForeignKey(
        User,
        related_name='subscribers', #followers
        verbose_name='Автор',
        on_delete=models.CASCADE,
    )
    subscriber = models.ForeignKey(
        User,
        related_name='subscriptions',
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'subscriber'],
                name='unique_author_subscriber',
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'

    def clean(self):
        if self.subscriber == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')
