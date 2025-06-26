from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для рецептов:
    - по автору
    - по наличию в избранном (is_favorited)
    - по наличию в списке покупок (is_in_shopping_cart)
    """
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = (
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, queryset, name, value):
        """Фильтрация по наличию рецепта в избранном пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(fans__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по наличию рецепта в корзине покупок пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_cart__user=self.request.user)
        return queryset