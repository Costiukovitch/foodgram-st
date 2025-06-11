from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """Поиск по названию ингредиента."""
    
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Поиск по названию рецепта."""

    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.Filter(field_name='author__id')
    is_favorited = filters.Filter(field_name='is_favorited')
    is_in_shopping_cart = filters.Filter(field_name='is_in_shopping_cart')    

    class Meta:
        model = Recipe
        fields = [
            'is_favorited',
            'is_in_shopping_cart',
            'author',
            'tags',
        ]
