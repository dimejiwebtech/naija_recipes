"""
Django management command to scrape recipes from websites
Usage: python manage.py scrape_recipes <url> --ethnicity yoruba --max 10
"""

from django.core.management.base import BaseCommand
from recipes.utils.web_scraper import scrape_recipes_from_url


class Command(BaseCommand):
    help = 'Scrape Nigerian recipes from websites'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            type=str,
            help='URL to scrape (category page or single recipe)'
        )
        parser.add_argument(
            '--ethnicity',
            type=str,
            default='yoruba',
            help='Ethnicity: yoruba, igbo, or hausa (default: yoruba)'
        )
        parser.add_argument(
            '--category',
            type=str,
            default=None,
            help='Category slug (optional)'
        )
        parser.add_argument(
            '--max',
            type=int,
            default=10,
            help='Maximum recipes to scrape (default: 10)'
        )
    
    def handle(self, *args, **options):
        url = options['url']
        ethnicity = options['ethnicity']
        category = options['category']
        max_recipes = options['max']
        
        self.stdout.write(f"Starting scrape from: {url}")
        self.stdout.write(f"Ethnicity: {ethnicity}")
        if category:
            self.stdout.write(f"Category: {category}")
        
        # Run the scraper
        summary = scrape_recipes_from_url(
            url=url,
            max_recipes=max_recipes,
            ethnicity=ethnicity,
            category=category
        )
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f"\n=== Scraping Complete ==="))
        self.stdout.write(f"Scraped: {summary['scraped']}")
        self.stdout.write(f"Skipped: {summary['skipped']}")
        self.stdout.write(f"Errors: {summary['errors']}")
        
        if summary['error_details']:
            self.stdout.write(self.style.ERROR("\n=== Errors ==="))
            for error in summary['error_details']:
                self.stdout.write(f"  {error}")