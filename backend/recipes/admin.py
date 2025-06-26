from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Recipe,
    Ingredient,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
)


class BaseAdmin(admin.ModelAdmin):
    """Базовой класс для общих настроек."""
    ordering = ('id',)
    empty_value_display = _('-пусто-')


@admin.register(Ingredient)
class IngredientAdmin(BaseAdmin):
    """Админ-панель для модели Ингредиент."""
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(BaseAdmin):
    """Админ-панель для связи Рецепт-Ингредиент."""
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_select_related = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(BaseAdmin):
    """Админ-панель для Избранного."""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_select_related = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseAdmin):
    """Админ-панель для Корзины покупок."""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_select_related = ('user', 'recipe')


@admin.register(Recipe)
class RecipeAdmin(BaseAdmin):
    """Админ-панель для Рецепта."""
    list_display = ('id', 'author', 'name', 'get_favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = ('author',)
    list_select_related = ('author',)

    @admin.display(description=_('Число добавлений в избранное'))
    def get_favorite_count(self, obj):
        return obj.favorites.count()