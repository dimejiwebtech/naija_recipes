import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from recipes.models import Recipe, Ethnicity, Category, Ingredient, RecipeNote

User = get_user_model()


@pytest.fixture
def api_client():

    return APIClient()


@pytest.fixture
def create_user(db):

    def make_user(**kwargs):
        if 'username' not in kwargs:
            kwargs['username'] = 'testuser'
        if 'password' not in kwargs:
            kwargs['password'] = 'testpass123'
        return User.objects.create_user(**kwargs)
    return make_user


@pytest.fixture
def yoruba_ethnicity(db):

    return Ethnicity.objects.create(
        name='Yoruba',
        slug='yoruba',
        description='Yoruba cuisine from South-Western Nigeria'
    )


@pytest.fixture
def igbo_ethnicity(db):

    return Ethnicity.objects.create(
        name='Igbo',
        slug='igbo',
        description='Igbo cuisine from South-Eastern Nigeria'
    )


@pytest.fixture
def soup_category(db):

    return Category.objects.create(
        name='Soups',
        slug='soups',
        description='Traditional Nigerian soups'
    )


@pytest.fixture
def rice_category(db):

    return Category.objects.create(
        name='Rice Dishes',
        slug='rice-dishes',
        description='Nigerian rice-based dishes'
    )


@pytest.fixture
def sample_recipe(db, yoruba_ethnicity, rice_category):
    recipe = Recipe.objects.create(
        title='Jollof Rice',
        slug='jollof-rice',
        description='Classic Nigerian rice dish',
        instructions='1. Blend tomatoes\n2. Fry paste\n3. Add rice\n4. Cook',
        prep_time=20,
        cook_time=45,
        servings=6,
        ethnicity=yoruba_ethnicity,
        category=rice_category,
        is_active=True
    )
    
    # Add ingredients
    Ingredient.objects.create(
        recipe=recipe,
        name='Rice',
        quantity=3,
        unit='cup'
    )
    Ingredient.objects.create(
        recipe=recipe,
        name='Tomatoes',
        quantity=5,
        unit='piece'
    )
    
    # Add note
    RecipeNote.objects.create(
        recipe=recipe,
        note='For smoky flavor, allow bottom to burn slightly'
    )
    
    return recipe