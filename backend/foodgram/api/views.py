from django.db.models import Sum
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404

from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
)
from users.models import User
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    CreateRecipeSerializer,
    FollowSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    CustomUserSerializer,
)
from .filters import RecipeFilter, IngredientFilter
from .permissions import IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly
from .pagination import CustomPageNumberPagination


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateRecipeSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action in ['create']:
            self.permission_classes = [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthorOrReadOnly()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            _, created = request.user.favorites.get_or_create(recipe=recipe)
            if not created:
                return Response(
                    {'error': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FavoriteSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted, _ = request.user.favorites.filter(recipe=recipe).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            _, created = request.user.shopping_cart.get_or_create(recipe=recipe)
            if not created:
                return Response(
                    {'error': 'Рецепт уже добавлен в корзину покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({'success': 'Рецепт добавлен в список покупок'}, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted, _ = request.user.shopping_cart.filter(recipe=recipe).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Рецепт не найден в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)


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
        follows = request.user.follows.select_related('author').all()
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
                    {'error': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            follow, created = request.user.follows.get_or_create(author=author)
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FollowSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted, _ = request.user.follows.filter(author=author).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

class UserViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    Вьюсет для работы с пользователями.
    Поддерживает: профиль пользователя, подписки, управление аватаром.
    """

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return User.objects.all()

    @action(
        detail=False,
        methods=['get'],
        url_path='me',
        permission_classes=[permissions.IsAuthenticated]
    )
    def current_profile(self, request):
        """Получить данные текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[permissions.IsAuthenticated]
    )
    def update_avatar(self, request):
        """Обновить или удалить аватар текущего пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(instance=user, data=request.data, partial=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if hasattr(user, 'avatar') and user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[permissions.IsAuthenticated],
    )
    def toggle_subscription(self, request, pk=None):
        """Подписаться или отписаться от автора."""
        author = get_object_or_404(User, id=pk)
        subscriber = request.user

        if request.method == 'POST':
            _, created = Subscription.objects.get_or_create(
                author=author,
                subscriber=subscriber
            )
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            recipes_limit = request.query_params.get('recipes_limit')
            context = {'request': request, 'recipes_limit': recipes_limit}
            serializer = SubscriptionSerializer(author, context=context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                author_id=pk,
                subscriber=subscriber
            ).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Вы не подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def list_subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        subscriptions = request.user.followers.all().select_related('author')

        page = self.paginate_queryset(subscriptions)
        recipes_limit = request.query_params.get('recipes_limit')
        context = {
            'request': request,
            'recipes_limit': recipes_limit
        }

        serializer = SubscriptionSerializer(page, many=True, context=context)
        return self.get_paginated_response(serializer.data)