from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    redirect_to_recipe,
)


router = DefaultRouter()
router.register("users", UserViewSet)
router.register("recipes", RecipeViewSet)
router.register("ingredients", IngredientViewSet)

urlpatterns = [
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
    path('r/<int:recipe_id>/', redirect_to_recipe, name='redirect_to_recipe'),
]
