from django_filters import (
    FilterSet, CharFilter, NumberFilter, BooleanFilter,
    ModelMultipleChoiceFilter
)

from recipes.models import Ingredient, Tag, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name')


class RecipeFilter(FilterSet):
    author = NumberFilter(field_name='author__id')
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug', to_field_name='slug'
    )
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    is_favorited = BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = (
            'is_in_shopping_cart',
            'is_favorited'
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(carts__user=user)
        return queryset.exclude(carts__user=user)

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)
