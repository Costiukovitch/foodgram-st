from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)
from users.models import Subscription

from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    UserSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeMiniSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubscriptionCreateSerializer,
    SubscriptionSerializer,
)

User = get_user_model()


def redirect_to_recipe(request, recipe_id):
    """Переадресация на рецепт по ID."""
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise Http404('Рецепт не найден')
    return redirect('recipe_detail', pk=recipe_id)


class UserViewSet(DjoserUserViewSet):
    """ViewSet для пользователей с действиями подписки и аватаром."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        return super().me(request)

    @action(
        url_path='me/avatar',
        detail=False,
        methods=['put', 'delete'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def manage_avatar(self, request):
        """Управление аватаром пользователя."""
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'error': 'Аватар обязателен'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = AvatarSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.user.avatar:
            request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка от автора рецептов."""
        subscriber = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            serializer = SubscriptionCreateSerializer(
                data={'author': author.id, 'subscriber': subscriber.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            context = {
                'request': request,
                'recipes_limit': request.query_params.get('recipes_limit')
            }
            subscription_serializer = SubscriptionSerializer(author, context=context)
            return Response(subscription_serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                author=author, subscriber=subscriber
            ).delete()
            if not deleted:
                return Response(
                    {'error': 'Вы не подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Получить список авторов, на которых подписан пользователь."""
        authors = (
            User.objects
            .filter(followers__subscriber=request.user)
            .annotate(recipes_count=Count('recipes'))
        )
        page = self.paginate_queryset(authors)

        context = {
            'request': request,
            'recipes_limit': request.query_params.get('recipes_limit')
        }

        serializer = SubscriptionSerializer(page, many=True, context=context)
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов: создание, редактирование, фильтрация."""
    queryset = Recipe.objects.select_related('author').prefetch_related('components__ingredient')
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly
    ]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _generate_shopping_list(self, ingredients):
        text = 'Список покупок:\n\n'
        for item in ingredients:
            text += (
                f"{item['ingredient__name']} "
                f"{item['ingredient__measurement_unit']} — "
                f"{item['total']} "
                f"(в {item['recipe_count']} рецептах)\n"
            )
        return text

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk):
        """Получить короткую ссылку на рецепт."""
        if not Recipe.objects.filter(pk=pk).exists():
            return Response({'detail': 'Рецепт не найден'}, status=status.HTTP_404_NOT_FOUND)
        short_link = request.build_absolute_uri(reverse('redirect_to_recipe', kwargs={'recipe_id': pk}))
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок в виде текстового файла."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount'),
            recipe_count=Count('recipe', distinct=True)
        )

        text = self._generate_shopping_list(ingredients)

        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(url_path='favorite', detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = FavoriteSerializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeMiniSerializer(recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            deleted, _ = Favorite.objects.filter(user=user, recipe=recipe).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Рецепт не в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(url_path='shopping_cart', detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавить/удалить рецепт из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = ShoppingCartSerializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeMiniSerializer(recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            deleted, _ = ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Рецепт не в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)