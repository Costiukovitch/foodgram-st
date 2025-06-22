from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, IngredientViewSet, FollowViewSet

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'users/subscriptions', FollowViewSet, basename='follow')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    #path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]