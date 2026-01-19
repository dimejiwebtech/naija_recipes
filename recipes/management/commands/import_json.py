"""
Django management command to import recipes from JSON file
Usage: python manage.py import_json data/sample_recipes.json
"""

from django.core.management.base import BaseCommand
from recipes.utils.json_importer import JSONRecipeImporter


class Command(BaseCommand):
    help = 'Import Nigerian recipes from JSON file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to JSON file containing recipes'
        )
    
    def handle(self, *args, **options):
        json_file = options['json_file']
        
        self.stdout.write(f"Importing recipes from: {json_file}")
        
        # Create importer and run
        importer = JSONRecipeImporter(json_file)
        result = importer.import_recipes()
        
        # Display results
        if result['success']:
            self.stdout.write(self.style.SUCCESS(f"\n=== Import Complete ==="))
            self.stdout.write(f"Created: {result['created']}")
            self.stdout.write(f"Skipped: {result['skipped']}")
            
            if result['errors']:
                self.stdout.write(self.style.ERROR(f"\n=== Errors ({len(result['errors'])}) ==="))
                for error in result['errors']:
                    self.stdout.write(f"  Recipe: {error['recipe']}")
                    self.stdout.write(f"  Error: {error['error']}\n")
        else:
            self.stdout.write(self.style.ERROR(f"Import failed: {result['error']}"))