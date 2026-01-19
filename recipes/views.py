from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response   
from django_filters.rest_framework import DjangoFilterBackend
from .models import Recipe, Category, Ethnicity
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from .serializers import (
    RecipeListSerializer, 
    RecipeDetailSerializer, 
    CategorySerializer, 
    EthnicitySerializer,
    RecipeCreateUpdateSerializer
)
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes



@extend_schema_view(
    list=extend_schema(
        summary="List all ethnicities",
        description="Get a list of all Nigerian ethnic groups (Yoruba, Igbo, Hausa, etc.) with recipe counts.",
        tags=['Ethnicities']
    ),
    retrieve=extend_schema(
        summary="Get ethnicity details",
        description="Retrieve detailed information about a specific Nigerian ethnic group.",
        tags=['Ethnicities']
    ),
    create=extend_schema(
        summary="Create new ethnicity",
        description="Add a new Nigerian ethnic group to the system.",
        tags=['Ethnicities']
    ),
    update=extend_schema(
        summary="Update ethnicity",
        description="Update all fields of an ethnic group.",
        tags=['Ethnicities']
    ),
    partial_update=extend_schema(
        summary="Partial update ethnicity",
        description="Update specific fields of an ethnic group.",
        tags=['Ethnicities']
    ),
    destroy=extend_schema(
        summary="Delete ethnicity",
        description="Remove an ethnic group from the system.",
        tags=['Ethnicities']
    ),
)
class EthnicityViewSet(viewsets.ModelViewSet):

    queryset = Ethnicity.objects.all()
    serializer_class = EthnicitySerializer
    lookup_field = 'slug'
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


@extend_schema_view(
    list=extend_schema(
        summary="List all categories",
        description="Get a list of all recipe categories (Soups, Swallow, Rice Dishes, etc.) with recipe counts.",
        tags=['Categories']
    ),
    retrieve=extend_schema(
        summary="Get category details",
        description="Retrieve detailed information about a specific recipe category.",
        tags=['Categories']
    ),
    create=extend_schema(
        summary="Create new category",
        description="Add a new recipe category to the system.",
        tags=['Categories']
    ),
    update=extend_schema(
        summary="Update category",
        description="Update all fields of a category.",
        tags=['Categories']
    ),
    partial_update=extend_schema(
        summary="Partial update category",
        description="Update specific fields of a category.",
        tags=['Categories']
    ),
    destroy=extend_schema(
        summary="Delete category",
        description="Remove a category from the system.",
        tags=['Categories']
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


@extend_schema_view(
    list=extend_schema(
        summary="List all recipes",
        description="""
        Get a paginated list of all active Nigerian recipes.
        
        Supports filtering by ethnicity, category, and servings.
        Supports searching by title, description, ingredients, ethnicity name, and category name.
        Supports ordering by created_at, title, prep_time, cook_time, and servings.
        """,
        tags=['Recipes'],
        parameters=[
            OpenApiParameter(
                name='ethnicity',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by ethnicity ID'
            ),
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by category ID'
            ),
            OpenApiParameter(
                name='servings',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by number of servings'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, description, ingredients'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order results by field (prefix with - for descending)',
                enum=['created_at', '-created_at', 'title', '-title', 'prep_time', '-prep_time', 'cook_time', '-cook_time']
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Get recipe details",
        description="Retrieve complete details of a specific recipe including all ingredients and cooking instructions.",
        tags=['Recipes']
    ),
    create=extend_schema(
        summary="Create new recipe",
        description="Add a new recipe with ingredients and optional notes.",
        tags=['Recipes']
    ),
    update=extend_schema(
        summary="Update recipe",
        description="Update all fields of a recipe including ingredients.",
        tags=['Recipes']
    ),
    partial_update=extend_schema(
        summary="Partial update recipe",
        description="Update specific fields of a recipe.",
        tags=['Recipes']
    ),
    destroy=extend_schema(
        summary="Delete recipe",
        description="Remove a recipe from the system.",
        tags=['Recipes']
    ),
)
class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.select_related(
        'category', 'ethnicity'
    ).prefetch_related(
        'ingredients', 'notes'
    ).filter(is_active=True)
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    
    filterset_fields = ['ethnicity', 'category', 'servings']
    search_fields = [
        'title', 
        'description', 
        'ingredients__name',
        'ethnicity__name',
        'category__name'
    ]
    ordering_fields = [
        'created_at', 'title', 'prep_time', 
        'cook_time', 'servings'
    ]
    ordering = ['-created_at']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        
        if self.action == 'list':
            return RecipeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeDetailSerializer
    
    @extend_schema(
        summary="Get recipes by ethnicity",
        description="Filter recipes by Nigerian ethnic group (Yoruba, Igbo, or Hausa).",
        parameters=[
            OpenApiParameter(
                name='ethnicity',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Ethnicity slug (e.g., yoruba, igbo, hausa)',
                required=True,
                examples=[
                    OpenApiExample('Yoruba', value='yoruba'),
                    OpenApiExample('Igbo', value='igbo'),
                    OpenApiExample('Hausa', value='hausa'),
                ]
            ),
        ],
        responses={200: RecipeListSerializer(many=True)},
        tags=['Recipes']
    )
    @action(detail=False, methods=['get'])
    def by_ethnicity(self, request):
        ethnicity_slug = request.query_params.get('ethnicity')
        
        if not ethnicity_slug:
            return Response(
                {'error': 'ethnicity parameter is required (yoruba, igbo, hausa)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recipes = self.queryset.filter(ethnicity__slug=ethnicity_slug)
        
        page = self.paginate_queryset(recipes)
        if page is not None:
            serializer = RecipeListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = RecipeListSerializer(recipes, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get quick recipes",
        description="Get recipes that can be prepared quickly (total time under specified minutes).",
        parameters=[
            OpenApiParameter(
                name='max_time',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Maximum total time in minutes (default: 45)',
                required=False
            ),
        ],
        responses={200: RecipeListSerializer(many=True)},
        tags=['Recipes']
    )
    @action(detail=False, methods=['get'])
    def quick_recipes(self, request):

        max_time = int(request.query_params.get('max_time', 45))
        
        quick_recipes = self.queryset.filter(
            prep_time__lte=max_time,
            cook_time__lte=max_time
        )
        
        # Filter by total time
        quick_recipes = [
            recipe for recipe in quick_recipes 
            if recipe.total_time <= max_time
        ]
        
        page = self.paginate_queryset(quick_recipes)
        if page is not None:
            serializer = RecipeListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = RecipeListSerializer(quick_recipes, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get API statistics",
        description="Get overview statistics about recipes in the database.",
        responses={
            200: OpenApiTypes.OBJECT
        },
        tags=['Recipes']
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        
        stats = {
            'total_recipes': self.queryset.count(),
            'by_ethnicity': list(
                Ethnicity.objects.annotate(
                    recipe_count=Count('recipes', filter=models.Q(recipes__is_active=True))
                ).values('name', 'recipe_count')
            ),
            'by_category': list(
                Category.objects.annotate(
                    recipe_count=Count('recipes', filter=models.Q(recipes__is_active=True))
                ).values('name', 'recipe_count')
            ),
            'average_prep_time': self.queryset.aggregate(Avg('prep_time'))['prep_time__avg'],
            'average_cook_time': self.queryset.aggregate(Avg('cook_time'))['cook_time__avg'],
        }
        
        return Response(stats)
    
def recipe_list_view(request):
  
    recipes = Recipe.objects.filter(is_active=True).select_related(
        'ethnicity', 'category'
    ).order_by('-created_at')
    
    # Get filter parameters from URL
    ethnicity_filter = request.GET.get('ethnicity', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    # Apply filters
    if ethnicity_filter:
        recipes = recipes.filter(ethnicity__slug=ethnicity_filter)
    
    if category_filter:
        recipes = recipes.filter(category__slug=category_filter)
    
    if search_query:
        recipes = recipes.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(ingredients__name__icontains=search_query)
        ).distinct()
    
    # Pagination - 12 recipes per page
    paginator = Paginator(recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all ethnicities and categories for filter dropdown
    ethnicities = Ethnicity.objects.all()
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'ethnicities': ethnicities,
        'categories': categories,
        'current_ethnicity': ethnicity_filter,
        'current_category': category_filter,
        'search_query': search_query,
    }
    
    return render(request, 'recipes/recipe_list.html', context)


def recipe_detail_view(request, slug):

    recipe = get_object_or_404(
        Recipe.objects.select_related('ethnicity', 'category')
                      .prefetch_related('ingredients', 'notes'),
        slug=slug,
        is_active=True
    )
    
    # Get related recipes (same ethnicity)
    related_recipes = Recipe.objects.filter(
        ethnicity=recipe.ethnicity,
        is_active=True
    ).exclude(id=recipe.id)[:4]
    
    context = {
        'recipe': recipe,
        'related_recipes': related_recipes,
    }
    
    return render(request, 'recipes/recipe_detail.html', context)


def ethnicity_view(request, slug):

    ethnicity = get_object_or_404(Ethnicity, slug=slug)
    
    recipes = Recipe.objects.filter(
        ethnicity=ethnicity,
        is_active=True
    ).select_related('category').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'ethnicity': ethnicity,
        'page_obj': page_obj,
    }
    
    return render(request, 'recipes/ethnicity_detail.html', context)