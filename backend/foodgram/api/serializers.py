import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from djoser.serializers import UserCreateSerializer

from recipes.models import (
    Ingredient, Recipe, IngredientInRecipe,
    Tag, TagInRecipe, Follow, Favorite, ShoppingCart
)
from users.models import User


class Base64ImageField(serializers.ImageField):
    """Поле для кодирования изображения в base64."""

    def to_internal_value(self, data):
        """Метод для преобразования картинки."""

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='photo.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserCreateSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Meta-параметры сериализатора."""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        """Метод для проверки подписки."""

        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class CustomCreateUserSerializer(CustomUserSerializer):
    """Сериализатор для создания пользователя
    без проверки на подписку."""

    class Meta:
        """Meta-параметры сериализатора"""

        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {'password': {'write_only': True}}


class TagSerializer(ModelSerializer):
    """Сериализатор для вывода тегов."""

    class Meta:
        """Meta-параметры сериализатора."""

        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    """Сериализатор для вывода ингредиентов."""

    class Meta:
        """Meta-параметры сериализатора."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        """Meta-параметры сериализатора."""

        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_list', many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Meta-параметры сериализатора."""

        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time'
                  )

    def get_is_favorited(self, obj):
        """Метод проверки на добавление в избранное."""

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Метод проверки на присутствие в корзине."""

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()


class CreateIngredientsInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецептах."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    @staticmethod
    def validate_amount(value):
        """Метод для валидации количества ингредиентов."""

        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0!'
            )
        return value

    class Meta:
        """Meta-параметры сериализатора."""

        model = IngredientInRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

    ingredients = CreateIngredientsInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(use_url=True)

    class Meta:
        """Meta-параметры сериализатора"""

        model = Recipe
        fields = ('ingredients', 'tags', 'name',
                  'image', 'text', 'cooking_time')

    def to_representation(self, instance):
        """Метод представления модели."""

        serializer = RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data

    def validate(self, data):
        """Метод валидации ингредиентов."""

        ingredients = self.initial_data.get('ingredients')
        lst_ingredient = []

        for ingredient in ingredients:
            if ingredient['id'] in lst_ingredient:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальными!'
                )
            lst_ingredient.append(ingredient['id'])

        return data

    def create_ingredients(self, ingredients, recipe):
        """Метод для создания ингредиента."""

        for element in ingredients:
            id = element['id']
            ingredient = Ingredient.objects.get(pk=id)
            amount = element['amount']
            IngredientInRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )

    def create_tags(self, tags, recipe):
        """Метод добавления тега."""

        recipe.tags.set(tags)

    def create(self, validated_data):
        """Метод создания модели."""

        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        user = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления модели."""

        IngredientInRecipe.objects.filter(recipe=instance).delete()
        TagInRecipe.objects.filter(recipe=instance).delete()

        self.create_ingredients(validated_data.pop('ingredients'), instance)
        self.create_tags(validated_data.pop('tags'), instance)

        return super().update(instance, validated_data)


class AdditionalRecipeSerializer(serializers.ModelSerializer):
    """Дополнительный сериализатор для рецептов."""

    class Meta:
        """Meta-параметры сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(CustomUserSerializer):
    """Сериализатор для модели Follow."""

    recipes = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        """Meta-параметры сериализатора."""

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)

    def get_recipes(self, obj):
        """Метод для получения рецептов."""

        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return AdditionalRecipeSerializer(recipes, many=True).data

    @staticmethod
    def get_recipes_count(obj):
        """Метод для получения количества рецептов."""

        return obj.recipes.count()


class AddFavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в избранное по модели Recipe."""

    image = Base64ImageField()

    class Meta:
        """Meta-параметры сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
