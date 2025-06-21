# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, IngredientViewSet, TagViewSet, FollowViewSet

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'users/subscriptions', FollowViewSet, basename='follow')

urlpatterns = [
    path('', include(router.urls)),
    path('users/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]