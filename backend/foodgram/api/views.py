from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    Favorite,
    ShoppingCart,
    Follow,
    RecipeIngredient,
)
from users.models import User
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeSerializer,
    CreateRecipeSerializer,
    FollowSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer
)
from .filters import RecipeFilter, IngredientFilter
from .permissions import IsAuthorOrReadOnly
from .pagination import CustomPageNumberPagination


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class RecipeViewSet(ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthorOrReadOnly]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}

        if request.method == 'POST':
            serializer = FavoriteSerializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(user=request.user, recipe=recipe)
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Favorite.DoesNotExist:
                return Response(
                    {'error': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}

        if request.method == 'POST':
            serializer = ShoppingCartSerializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                cart_item = ShoppingCart.objects.get(user=request.user, recipe=recipe)
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ShoppingCart.DoesNotExist:
                return Response(
                    {'error': 'Рецепт не найден в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount_total=Sum('amount'))

        shopping_list = '\n'.join([
            f"{item['ingredient__name']} — {item['amount_total']} "
            f"({item['ingredient__measurement_unit']})"
            for item in ingredients
        ])

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response


class FollowViewSet(viewsets.ViewSet):
    """Вьюсет для управления подписками пользователей."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        follows = Follow.objects.filter(user=request.user).select_related('author')
        paginator = CustomPageNumberPagination()
        page = paginator.paginate_queryset(follows, request)
        serializer = FollowSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'error': 'Нельзя подписаться на себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow, created = Follow.objects.get_or_create(user=request.user, author=author)
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FollowSerializer(follow.author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted, _ = Follow.objects.filter(user=request.user, author=author).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
            