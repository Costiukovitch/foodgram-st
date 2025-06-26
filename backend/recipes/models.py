from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

from utils.constants import (
    MIN_INGREDIENT_AMOUNT,
    MAX_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
)

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        'Название',
        max_length=255,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=255,
    )

    class Meta:
        verbose_name = _('Ингредиент')
        verbose_name_plural = _('Ингредиенты')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_per_unit',
            ),
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта."""
    name = models.CharField(_('Название'), max_length=256)
    image = models.ImageField(_('Изображение'), upload_to='recipes/')
    text = models.TextField(_('Описание'))
    author = models.ForeignKey(
        User,
        related_name='recipes',
        verbose_name=_('Автор'),
        on_delete=models.CASCADE,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    cooking_time = models.PositiveSmallIntegerField(
        _('Время приготовления'),
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ],
    )

    class Meta:
        verbose_name = _('Рецепт')
        verbose_name_plural = _('Рецепты')
        ordering = ['-id']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связь между рецептами и ингредиентами."""
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='dish_components',
        verbose_name=_('Ингредиент'),
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='components',
        verbose_name=_('Рецепт'),
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        _('Количество'),
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
            MaxValueValidator(MAX_INGREDIENT_AMOUNT),
        ],
    )

    class Meta:
        verbose_name = _('Ингредиент в рецепте')
        verbose_name_plural = _('Ингредиенты в рецептах')
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_recipe_ingredient',
            ),
        ]
        ordering = ['id']

    def __str__(self):
        return f'{self.amount} {self.ingredient} в {self.recipe}'


class ShoppingCart(models.Model):
    """Модель списка покупок пользователя."""
    user = models.ForeignKey(
        User,
        related_name='cart_items',
        verbose_name=_('Пользователь'),
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_cart',
        verbose_name=_('Рецепт'),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('Список покупок')
        verbose_name_plural = _('Списки покупок')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart_recipe',
            ),
        ]
        ordering = ['id']

    def __str__(self):
        return f'{self.recipe} в корзине {self.user}'


class Favorite(models.Model):
    """Модель избранного у пользователя."""
    user = models.ForeignKey(
        User,
        related_name='favorite_recipes',
        verbose_name=_('Пользователь'),
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='fans',
        verbose_name=_('Рецепт'),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('Избранное')
        verbose_name_plural = _('Избранное')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe',
            ),
        ]
        ordering = ['id']

    def __str__(self):
        return f'{self.recipe} в избранном {self.user}'