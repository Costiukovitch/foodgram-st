from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect
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
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise Http404('Рецепт не найден')
    return redirect('recipe_detail', pk=recipe_id)


class UserViewSet(DjoserUserViewSet):
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
        detail=False,
        url_path='me/avatar',
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def manage_avatar(self, request):
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'error': 'Avatar data is required'},
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
        subscriber = request.user

        if request.method == 'POST':
            author = get_object_or_404(User, pk=id)
            serializer = SubscriptionCreateSerializer(
                data={'author': author.id, 'subscriber': subscriber.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            recipes_limit = request.query_params.get('recipes_limit')
            context = {
                'request': request,
                'recipes_limit': recipes_limit
            }
            subscription_serializer = SubscriptionSerializer(
                author, context=context
            )
            return Response(subscription_serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            author = get_object_or_404(User, pk=id)
            deleted, _ = subscriber.subscriptions.filter(
                author=author
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
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(subscribers__subscriber=user).annotate(
            recipes_count=Count('recipes')
        )

        page = self.paginate_queryset(authors)
        context = {
            'request': request,
            'recipes_limit': request.query_params.get('recipes_limit')
        }

        serializer = SubscriptionSerializer(page, many=True, context=context)
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'components__ingredient'
    )
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

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, pk):
        if not Recipe.objects.filter(pk=pk).exists():
            return Response(
                {'detail': 'Recipe not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        short_link = request.build_absolute_uri(
            reverse('redirect_to_recipe', kwargs={'recipe_id': pk})
        )
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount'),
            recipe_count=Count('recipe', distinct=True)
        )

        text = self._generate_shopping_list(ingredients)

        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        url_path='favorite',
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = FavoriteSerializer(
                data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeMiniSerializer(
                    recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            deleted, _ = user.favorites.filter(
                recipe=recipe
            ).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Recipe not in favorites'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        url_path='shopping_cart',
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = ShoppingCartSerializer(
                data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeMiniSerializer(
                    recipe, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            deleted, _ = user.in_cart.filter(
                recipe=recipe
            ).delete()
            if deleted == 0:
                return Response(
                    {'error': 'Recipe not in shopping cart'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
