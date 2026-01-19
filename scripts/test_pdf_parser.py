import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'naija_recipes.settings')
import django
django.setup()

from recipes.utils.pdf_parser import PDFRecipeParser


def test_parser(): 
    pdf_path = 'data/sample_cookbook.txt'
    
    print(f"Testing PDF Parser with: {pdf_path}\n")
    
    parser = PDFRecipeParser(pdf_path)
    recipes = parser.parse_pdf()
    
    print(f"Found {len(recipes)} recipe(s)\n")
    
    for i, recipe in enumerate(recipes, 1):
        print(f"{'='*60}")
        print(f"Recipe {i}: {recipe['title']}")
        print(f"{'='*60}")
        print(f"Description: {recipe.get('description', 'N/A')[:100]}...")
        print(f"Prep Time: {recipe.get('prep_time')} min")
        print(f"Cook Time: {recipe.get('cook_time')} min")
        print(f"Servings: {recipe.get('servings')}")
        print(f"\nIngredients ({len(recipe.get('ingredients', []))}):")
        for ing in recipe.get('ingredients', [])[:5]: 
            print(f"  - {ing['quantity']} {ing['unit']} {ing['name']}")
        if len(recipe.get('ingredients', [])) > 5:
            print(f"  ... and {len(recipe.get('ingredients', [])) - 5} more")
        print(f"\nInstructions: {recipe.get('instructions', '')[:100]}...")
        print()


if __name__ == '__main__':
    test_parser()