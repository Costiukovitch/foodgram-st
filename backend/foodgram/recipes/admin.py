from django.contrib.admin import ModelAdmin, register

from .models import (
    Ingredient, IngredientInRecipe, Recipe,
    Tag, ShoppingCart, Follow, Favorite, TagInRecipe
)


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    """Панель администратора для ингредиентов"""

    search_fields = ('name',)
    list_display = ('pk', 'name', 'measurement_unit')


@register(IngredientInRecipe)
class IngredientInRecipe(ModelAdmin):
    """Панель администратора для ингредиентов в рецепте."""

    list_display = ('pk', 'recipe', 'ingredient', 'amount')


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    """Панель администратора для рецептов."""

    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)
    list_display = (
        'pk', 'name', 'author', 'get_favorites', 'get_tags', 'created'
    )

    def get_favorites(self, obj):
        return obj.favorites.count()

    get_favorites.short_description = (
        'Количество добавлений рецепта в избранное'
    )

    def get_tags(self, obj):
        return '\n'.join(obj.tags.values_list('name', flat=True))

    get_tags.short_description = 'Тег или список тегов'


@register(Tag)
class TagAdmin(ModelAdmin):
    """Панель администратора для тегов."""

    list_display = ('pk', 'name', 'color', 'slug')


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    """Панель администратора для списка покупок."""

    list_display = ('pk', 'user', 'recipe')


@register(Follow)
class FollowAdmin(ModelAdmin):
    """Панель администратора для подписок."""

    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
    list_display = ('pk', 'user', 'author')


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    """Панель администратора для избранного."""

    list_display = ('pk', 'user', 'recipe')


@register(TagInRecipe)
class TagAdmin(ModelAdmin):
    """Панель администратора для тегов рецепта."""

    list_display = ('pk', 'tag', 'recipe')
    