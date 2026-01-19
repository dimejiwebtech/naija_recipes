import json
from django.core.files import File
from recipes.models import Recipe, Ingredient, Category, Ethnicity, RecipeNote


class JSONRecipeImporter:
    """
    Import recipes from JSON file
    
    Expected JSON structure:
    {
        "recipes": [
            {
                "title": "Jollof Rice",
                "description": "...",
                "ethnicity": "yoruba",
                "category": "rice-dishes",
                ...
            }
        ]
    }
    """
    
    def __init__(self, json_file_path):
        """
        Initialize importer with path to JSON file
        
        Args:
            json_file_path: Path to JSON file containing recipes
        """
        self.json_file_path = json_file_path
        self.created_count = 0
        self.skipped_count = 0
        self.errors = []
    
    def import_recipes(self):
        """
        Main method to import all recipes from JSON file
        
        Returns:
            dict: Summary of import operation
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes_data = data.get('recipes', [])
            
            for recipe_data in recipes_data:
                try:
                    self._create_recipe(recipe_data)
                    self.created_count += 1
                except Exception as e:
                    self.skipped_count += 1
                    self.errors.append({
                        'recipe': recipe_data.get('title', 'Unknown'),
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'created': self.created_count,
                'skipped': self.skipped_count,
                'errors': self.errors
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_recipe(self, recipe_data):
        """
        Create a single recipe with all related objects
        
        Args:
            recipe_data: Dictionary containing recipe information
        """
        # Get or create ethnicity
        ethnicity = None
        if recipe_data.get('ethnicity'):
            ethnicity, _ = Ethnicity.objects.get_or_create(
                slug=recipe_data['ethnicity'],
                defaults={'name': recipe_data['ethnicity'].title()}
            )
        
        # Get or create category
        category = None
        if recipe_data.get('category'):
            category, _ = Category.objects.get_or_create(
                slug=recipe_data['category'],
                defaults={'name': recipe_data['category'].replace('-', ' ').title()}
            )
        
        # Create recipe
        recipe = Recipe.objects.create(
            title=recipe_data['title'],
            description=recipe_data.get('description', ''),
            instructions=recipe_data.get('instructions', ''),
            prep_time=recipe_data.get('prep_time', 30),
            cook_time=recipe_data.get('cook_time', 30),
            servings=recipe_data.get('servings', 4),
            ethnicity=ethnicity,
            category=category,
            # source_type='json'
        )
        
        # Create ingredients
        for ing_data in recipe_data.get('ingredients', []):
            Ingredient.objects.create(
                recipe=recipe,
                name=ing_data['name'],
                quantity=ing_data.get('quantity', 1),
                unit=ing_data.get('unit', 'piece'),
                notes=ing_data.get('notes', '')
            )
        
        # Create notes
        for note_text in recipe_data.get('notes', []):
            RecipeNote.objects.create(
                recipe=recipe,
                note=note_text
            )
        
        return recipe