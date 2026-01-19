from django.core.management.base import BaseCommand
from recipes.utils.pdf_parser import PDFRecipeParser, SimplePDFExtractor


class Command(BaseCommand):
    help = 'Import Nigerian recipes from PDF cookbook'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'pdf_file',
            type=str,
            help='Path to PDF file containing recipes'
        )
        parser.add_argument(
            '--ethnicity',
            type=str,
            default='yoruba',
            help='Default ethnicity: yoruba, igbo, or hausa (default: yoruba)'
        )
        parser.add_argument(
            '--category',
            type=str,
            default=None,
            help='Default category slug (optional)'
        )
        parser.add_argument(
            '--extract-only',
            action='store_true',
            help='Only extract text to file without importing'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='extracted_recipes.txt',
            help='Output file for extracted text (when using --extract-only)'
        )
    
    def handle(self, *args, **options):
        pdf_file = options['pdf_file']
        ethnicity = options['ethnicity']
        category = options['category']
        extract_only = options['extract_only']
        output_file = options['output']
        
        self.stdout.write(f"\nProcessing PDF: {pdf_file}")
        
        # If extract-only mode
        if extract_only:
            self.stdout.write("Mode: Extract text only (for manual review)")
            extractor = SimplePDFExtractor(pdf_file)
            
            if extractor.extract_to_text_file(output_file):
                self.stdout.write(self.style.SUCCESS(
                    f"\n✓ Text extracted to: {output_file}"
                ))
                self.stdout.write(
                    "Review the file, then you can manually create JSON or use auto-import."
                )
            else:
                self.stdout.write(self.style.ERROR("✗ Failed to extract text"))
            
            return
        
        # Auto-import mode
        self.stdout.write("Mode: Auto-import recipes")
        self.stdout.write(f"Default ethnicity: {ethnicity}")
        if category:
            self.stdout.write(f"Default category: {category}")
        
        # Parse PDF
        parser = PDFRecipeParser(pdf_file)
        recipes = parser.parse_pdf()
        
        self.stdout.write(f"\nParsed {len(recipes)} recipe(s) from PDF")
        
        if not recipes:
            self.stdout.write(self.style.WARNING(
                "\nNo recipes found. Try --extract-only mode to review the PDF content."
            ))
            return
        
        # Show preview of found recipes
        self.stdout.write("\nFound recipes:")
        for i, recipe in enumerate(recipes, 1):
            self.stdout.write(f"  {i}. {recipe['title']} ({len(recipe.get('ingredients', []))} ingredients)")
        
        # Ask for confirmation
        confirm = input("\nProceed with import? (yes/no): ")
        
        if confirm.lower() not in ['yes', 'y']:
            self.stdout.write(self.style.WARNING("Import cancelled"))
            return
        
        # Save to database
        self.stdout.write("\nImporting to database...")
        result = parser.save_to_database(
            default_ethnicity=ethnicity,
            default_category=category
        )
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f"\n=== Import Complete ==="))
        self.stdout.write(f"Total parsed: {result['total_parsed']}")
        self.stdout.write(f"Created: {result['created']}")
        self.stdout.write(f"Skipped: {result['skipped']}")
        
        if result['errors']:
            self.stdout.write(self.style.ERROR(f"\n=== Errors ({len(result['errors'])}) ==="))
            for error in result['errors']:
                self.stdout.write(f"  Recipe: {error['recipe']}")
                self.stdout.write(f"  Error: {error['error']}\n")