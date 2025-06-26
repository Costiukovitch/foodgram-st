from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import RecipeViewSet, IngredientViewSet, FollowViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'users/subscriptions', FollowViewSet, basename='follow')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]