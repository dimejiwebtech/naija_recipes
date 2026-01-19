import pytest
from django.urls import reverse
from rest_framework import status
from recipes.models import Recipe


@pytest.mark.django_db
class TestRecipeListAPI:
    
    def test_list_recipes(self, api_client, sample_recipe):
        url = reverse('recipes:recipe-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data  # Pagination
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Jollof Rice'
    
    def test_filter_by_ethnicity(self, api_client, sample_recipe, igbo_ethnicity):
        # Create Igbo recipe
        Recipe.objects.create(
            title='Egusi Soup',
            slug='egusi-soup',
            description='Igbo soup',
            instructions='Cook soup',
            prep_time=25,
            cook_time=40,
            servings=4,
            ethnicity=igbo_ethnicity,
            is_active=True
        )
        
        url = reverse('recipes:recipe-list')
        response = api_client.get(url, {'ethnicity': igbo_ethnicity.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['ethnicity_name'] == 'Igbo'
    
    def test_search_recipes(self, api_client, sample_recipe):
        url = reverse('recipes:recipe-list')
        response = api_client.get(url, {'search': 'jollof'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert 'Jollof' in response.data['results'][0]['title']
    
    def test_ordering_recipes(self, api_client, sample_recipe):
        url = reverse('recipes:recipe-list')
        response = api_client.get(url, {'ordering': '-created_at'})
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data


@pytest.mark.django_db
class TestRecipeDetailAPI:
    
    def test_retrieve_recipe(self, api_client, sample_recipe):
        url = reverse('recipes:recipe-detail', kwargs={'slug': sample_recipe.slug})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Jollof Rice'
        assert response.data['prep_time'] == 20
        assert response.data['cook_time'] == 45
        assert response.data['total_time'] == 65
        assert len(response.data['ingredients']) == 2
        assert len(response.data['notes']) == 1
    
    def test_retrieve_nonexistent_recipe(self, api_client):
        url = reverse('recipes:recipe-detail', kwargs={'slug': 'nonexistent'})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRecipeCreateAPI:
    
    def test_create_recipe(self, api_client, yoruba_ethnicity, rice_category):
        url = reverse('recipes:recipe-list')
        data = {
            'title': 'Fried Rice',
            'description': 'Nigerian fried rice',
            'instructions': '1. Cook rice\n2. Fry vegetables\n3. Mix together',
            'prep_time': 15,
            'cook_time': 30,
            'servings': 4,
            'ethnicity': yoruba_ethnicity.id,
            'category': rice_category.id,
            'ingredients': [
                {'name': 'Rice', 'quantity': 2, 'unit': 'cup'},
                {'name': 'Carrots', 'quantity': 2, 'unit': 'piece', 'notes': 'diced'},
            ],
            'notes': [
                {'note': 'Use day-old rice for best results'}
            ]
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Recipe.objects.filter(title='Fried Rice').exists()
        
        recipe = Recipe.objects.get(title='Fried Rice')
        assert recipe.ingredients.count() == 2
        assert recipe.notes.count() == 1
    
    def test_create_recipe_missing_fields(self, api_client):
        url = reverse('recipes:recipe-list')
        data = {
            'title': 'Incomplete Recipe',
            # Missing required fields
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRecipeCustomEndpoints:
    
    def test_by_ethnicity_endpoint(self, api_client, sample_recipe):
        url = reverse('recipes:recipe-by-ethnicity')
        response = api_client.get(url, {'ethnicity': 'yoruba'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_by_ethnicity_missing_param(self, api_client):
        url = reverse('recipes:recipe-by-ethnicity')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_quick_recipes_endpoint(self, api_client, sample_recipe):
        url = reverse('recipes:recipe-quick-recipes')
        response = api_client.get(url, {'max_time': 60})
        
        assert response.status_code == status.HTTP_200_OK
        # Jollof takes 65 minutes, shouldn't be in results
        assert len(response.data['results']) == 0
        
        # Test with higher limit
        response = api_client.get(url, {'max_time': 70})
        assert len(response.data['results']) == 1
    
    def test_statistics_endpoint(self, api_client, sample_recipe):
        url = reverse('recipes:recipe-statistics')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_recipes' in response.data
        assert 'by_ethnicity' in response.data
        assert 'by_category' in response.data
        assert response.data['total_recipes'] == 1


@pytest.mark.django_db
class TestEthnicityAPI:
    
    def test_list_ethnicities(self, api_client, yoruba_ethnicity, igbo_ethnicity):
        url = reverse('recipes:ethnicity-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_retrieve_ethnicity(self, api_client, yoruba_ethnicity):
        url = reverse('recipes:ethnicity-detail', kwargs={'slug': yoruba_ethnicity.slug})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Yoruba'


@pytest.mark.django_db
class TestCategoryAPI:
    
    def test_list_categories(self, api_client, soup_category, rice_category):
        url = reverse('recipes:category-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_retrieve_category(self, api_client, rice_category):
        url = reverse('recipes:category-detail', kwargs={'slug': rice_category.slug})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Rice Dishes'