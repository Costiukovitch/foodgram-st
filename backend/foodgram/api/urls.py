from rest_framework import routers
from django.urls import include, path

from .views import (
    RecipeViewSet, IngredientViewSet, TagViewSet,
    CustomUserViewSet,
)

app_name = 'api'
router = routers.DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]