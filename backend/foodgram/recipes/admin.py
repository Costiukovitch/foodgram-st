from django.contrib import admin
from .models import Ingredient, Tag, Recipe, RecipeIngredient, Favorite, ShoppingCart


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('tags',)
    search_fields = ('author__username', 'name')
    inlines = [RecipeIngredientInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('favorites')

    def favorited_count(self, obj):
        return obj.favorites.count()
    favorited_count.short_description = 'Число добавлений в избранное'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        recipe = self.get_object(request, object_id)
        extra_context = extra_context or {}
        extra_context['favorited_count'] = recipe.favorites.count()
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial['author'] = request.user.id
        return initial


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')