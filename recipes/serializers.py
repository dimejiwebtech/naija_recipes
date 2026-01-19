from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Recipe, Ingredient, Category, Ethnicity, RecipeNote

class EthnicitySerializer(serializers.ModelSerializer):
    # Serializer for ethnic groups
    recipe_count = serializers.SerializerMethodField()
    class Meta:
        model = Ethnicity
        fields = ['id', 'name', 'slug', 'description', 'recipe_count', 'created_at']
        read_only_fields = ['slug', 'created_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_recipe_count(self, obj):
        return obj.recipes.filter(is_active=True).count()

class CategorySerializer(serializers.ModelSerializer):
    # Serializer for recipe categories
    recipe_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'recipe_count']
        read_only_fields = ['slug', 'created_at']

    @extend_schema_field(OpenApiTypes.INT)
    def get_recipe_count(self, obj):
        return obj.recipes.filter(is_active=True).count()
    
class IngredientSerializer(serializers.ModelSerializer):
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    # Serializer for ingredients
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'quantity', 'unit', 'unit_display']

class RecipeNoteSerializer(serializers.ModelSerializer):
    # Serializer for recipe notes
    class Meta:
        model = RecipeNote
        fields = ['id', 'note']

class RecipeListSerializer(serializers.ModelSerializer):
    # Serializer for listing recipes
    ethnicity_name = serializers.CharField(source='ethnicity.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    ingredients_count = serializers.SerializerMethodField()
    total_time = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'slug', 'description', 'ethnicity_name', 
                  'category_name', 
                  'prep_time', 'cook_time', 'servings', 'total_time', 
                  'ingredients_count', 'created_at', 'image']
        read_only_fields = ['slug', 'created_at']
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_total_time(self, obj):
        return obj.total_time
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_ingredients_count(self, obj):
        return obj.ingredients.count()
    
class RecipeDetailSerializer(serializers.ModelSerializer):
    # Serializer for single recipe view with ingredients, notes, etc
    ingredients = IngredientSerializer(many=True, read_only=True)
    notes = RecipeNoteSerializer(many=True, read_only=True)
    ethnicity_name = serializers.CharField(source='ethnicity.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    total_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'slug', 'description', 'instructions', 
                  'prep_time', 'cook_time', 'servings', 'total_time',
                  'ethnicity_name', 'category_name', 'ingredients', 'notes',
                  'image', 'created_at','updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at', 'total_time']

class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    # Serializer for creating/updating recipes with nested ingredients and notes
    ingredients = IngredientSerializer(many=True)
    notes = RecipeNoteSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'instructions', 'prep_time', 'cook_time', 'servings', 'ethnicity', 'category', 'image', 'ingredients', 'notes']

    def create(self, validated_data):
        # for creating recipe with nested ingredients and notes
        ingredients_data = validated_data.pop('ingredients')
        notes_data = validated_data.pop('notes', [])

        # create recipe
        recipe = Recipe.objects.create(**validated_data)

        # create ingredients
        for ingredient_data in ingredients_data:
            Ingredient.objects.create(recipe=recipe, **ingredient_data)

        # create notes
        for note_data in notes_data:
            RecipeNote.objects.create(recipe=recipe, **note_data)

        return recipe
    
    def update(self, instance, validated_data):
        # for updating recipe with nested ingredients and notes
        ingredients_data = validated_data.pop('ingredients')
        notes_data = validated_data.pop('notes', None)

        # update recipe fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Replace ingredients
        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for ingredient_data in ingredients_data:
                Ingredient.objects.create(recipe=instance, **ingredient_data)


        # Replace notes
        if notes_data is not None:
            instance.notes.all().delete()
            for note_data in notes_data:
                RecipeNote.objects.create(recipe=instance, **note_data)

        return instance