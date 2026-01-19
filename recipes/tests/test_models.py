import pytest
from recipes.models import Recipe, Ethnicity, Category, Ingredient


@pytest.mark.django_db
class TestEthnicityModel:
    
    def test_ethnicity_creation(self, db):
        ethnicity = Ethnicity.objects.create(
            name='Yoruba',
            description='Yoruba cuisine'
        )
        
        assert ethnicity.name == 'Yoruba'
        assert ethnicity.slug == 'yoruba'  # Auto-generated
        assert str(ethnicity) == 'Yoruba'
    
    def test_ethnicity_slug_auto_generation(self, db):
        ethnicity = Ethnicity.objects.create(name='Igbo People')
        assert ethnicity.slug == 'igbo-people'


@pytest.mark.django_db
class TestCategoryModel:
    
    def test_category_creation(self, db):
        category = Category.objects.create(
            name='Soups',
            description='Traditional soups'
        )
        
        assert category.name == 'Soups'
        assert category.slug == 'soups'
        assert str(category) == 'Soups'


@pytest.mark.django_db
class TestRecipeModel:
    
    def test_recipe_creation(self, db, yoruba_ethnicity, rice_category):
        recipe = Recipe.objects.create(
            title='Jollof Rice',
            description='Nigerian rice dish',
            instructions='Cook rice',
            prep_time=20,
            cook_time=45,
            servings=6,
            ethnicity=yoruba_ethnicity,
            category=rice_category
        )
        
        assert recipe.title == 'Jollof Rice'
        assert recipe.slug == 'jollof-rice'  
        assert recipe.total_time == 65  
        assert str(recipe) == 'Jollof Rice'
    
    def test_recipe_total_time_property(self, db, sample_recipe):
        assert sample_recipe.total_time == sample_recipe.prep_time + sample_recipe.cook_time
        assert sample_recipe.total_time == 65


@pytest.mark.django_db
class TestIngredientModel:
    def test_ingredient_creation(self, db, sample_recipe):
        """Test creating an ingredient"""
        ingredient = Ingredient.objects.create(
            recipe=sample_recipe,
            name='Onions',
            quantity=2,
            unit='piece',
            notes='chopped'
        )
        
        assert ingredient.name == 'Onions'
        assert float(ingredient.quantity) == 2.0
        assert ingredient.unit == 'piece'
        assert 'Onions' in str(ingredient)
        assert 'chopped' in str(ingredient)