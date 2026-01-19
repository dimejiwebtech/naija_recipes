import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from recipes.models import Recipe, Ingredient, Category, Ethnicity, RecipeNote
from django.utils.text import slugify


class BaseRecipeScraper:
    """
    Base class for recipe scrapers
    Contains common functionality that all scrapers will use
    """
    
    def __init__(self, base_url):
        """
        Initialize the scraper
        
        Args:
            base_url: The base URL of the website to scrape
        """
        self.base_url = base_url
        self.session = requests.Session()
        # Set a proper User-Agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_count = 0
        self.skipped_count = 0
        self.errors = []
    
    def get_page(self, url, retries=3):
        """
        Fetch a webpage with retry logic
        
        Args:
            url: URL to fetch
            retries: Number of retry attempts
            
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                # Return parsed HTML
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                if attempt == retries - 1:
                    self.errors.append({
                        'url': url,
                        'error': f"Failed to fetch page: {str(e)}"
                    })
                    return None
                # Wait before retrying (exponential backoff)
                time.sleep(2 ** attempt)
        return None
    
    def clean_text(self, text):
        """
        Clean and normalize text extracted from HTML
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters that might cause issues
        text = text.strip()
        return text
    
    def extract_time(self, time_string):
        """
        Extract time in minutes from various text formats
        
        Examples:
            "30 minutes" -> 30
            "1 hour" -> 60
            "1 hour 30 minutes" -> 90
            "45 mins" -> 45
        
        Args:
            time_string: String containing time information
            
        Returns:
            Integer representing minutes
        """
        if not time_string:
            return 30  # Default fallback
        
        time_string = time_string.lower()
        total_minutes = 0
        
        # Extract hours
        hour_match = re.search(r'(\d+)\s*(?:hour|hr|h)', time_string)
        if hour_match:
            total_minutes += int(hour_match.group(1)) * 60
        
        # Extract minutes
        minute_match = re.search(r'(\d+)\s*(?:minute|min|m)', time_string)
        if minute_match:
            total_minutes += int(minute_match.group(1))
        
        # If no pattern matched but there's a number, assume it's minutes
        if total_minutes == 0:
            number_match = re.search(r'(\d+)', time_string)
            if number_match:
                total_minutes = int(number_match.group(1))
        
        return total_minutes if total_minutes > 0 else 30
    
    def extract_servings(self, servings_string):
        """
        Extract number of servings from text
        
        Examples:
            "Serves 4" -> 4
            "4-6 servings" -> 5 (average)
            "Makes 6 portions" -> 6
        
        Args:
            servings_string: String containing serving information
            
        Returns:
            Integer representing number of servings
        """
        if not servings_string:
            return 4  # Default fallback
        
        servings_string = servings_string.lower()
        
        # Look for range (e.g., "4-6")
        range_match = re.search(r'(\d+)\s*-\s*(\d+)', servings_string)
        if range_match:
            # Return average of range
            low = int(range_match.group(1))
            high = int(range_match.group(2))
            return (low + high) // 2
        
        # Look for single number
        number_match = re.search(r'(\d+)', servings_string)
        if number_match:
            return int(number_match.group(1))
        
        return 4  # Default
    
    def parse_ingredient(self, ingredient_text):
        """
        Parse ingredient text into structured data
        
        Examples:
            "2 cups rice" -> {name: "rice", quantity: 2, unit: "cup"}
            "500g beef" -> {name: "beef", quantity: 500, unit: "g"}
            "3 large onions, chopped" -> {name: "onions", quantity: 3, unit: "piece", notes: "chopped"}
        
        Args:
            ingredient_text: Raw ingredient text
            
        Returns:
            Dictionary with ingredient data
        """
        ingredient_text = self.clean_text(ingredient_text)
        
        # Default values
        result = {
            'name': ingredient_text,
            'quantity': 1,
            'unit': 'piece',
            'notes': ''
        }
        
        # Common unit patterns
        units = {
            'cup': 'cup', 'cups': 'cup',
            'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
            'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp',
            'g': 'g', 'gram': 'g', 'grams': 'g',
            'kg': 'kg', 'kilogram': 'kg', 'kilograms': 'kg',
            'ml': 'ml', 'milliliter': 'ml', 'milliliters': 'ml',
            'l': 'l', 'liter': 'l', 'liters': 'l',
            'piece': 'piece', 'pieces': 'piece',
            'bunch': 'bunch', 'bunches': 'bunch',
            'handful': 'handful', 'handfuls': 'handful',
            'wrap': 'wrap', 'wraps': 'wrap',
            'cube': 'cube', 'cubes': 'cube',
            'bulb': 'bulb', 'bulbs': 'bulb',
            'pinch': 'pinch', 'pinches': 'pinch',
        }
        
        # Try to match pattern: "quantity unit name"
        # Example: "2 cups rice" or "500g beef"
        pattern = r'^([\d./]+)\s*([a-zA-Z]+)?\s+(.+)$'
        match = re.match(pattern, ingredient_text)
        
        if match:
            quantity_str = match.group(1)
            unit_str = match.group(2)
            name_and_notes = match.group(3)
            
            # Parse quantity (handle fractions like "1/2")
            try:
                if '/' in quantity_str:
                    parts = quantity_str.split('/')
                    result['quantity'] = float(parts[0]) / float(parts[1])
                else:
                    result['quantity'] = float(quantity_str)
            except ValueError:
                result['quantity'] = 1
            
            # Parse unit
            if unit_str:
                unit_lower = unit_str.lower()
                result['unit'] = units.get(unit_lower, 'piece')
            
            # Split name and notes (usually separated by comma)
            if ',' in name_and_notes:
                name_part, notes_part = name_and_notes.split(',', 1)
                result['name'] = self.clean_text(name_part)
                result['notes'] = self.clean_text(notes_part)
            else:
                result['name'] = self.clean_text(name_and_notes)
        
        return result
    
    def save_recipe(self, recipe_data, ethnicity_slug=None, category_slug=None):
        """
        Save scraped recipe to database
        
        Args:
            recipe_data: Dictionary containing recipe information
            ethnicity_slug: Slug of ethnicity (yoruba, igbo, hausa)
            category_slug: Slug of category (optional)
            
        Returns:
            Recipe object or None if failed
        """
        try:
            # Get or create ethnicity
            ethnicity = None
            if ethnicity_slug:
                ethnicity, _ = Ethnicity.objects.get_or_create(
                    slug=ethnicity_slug,
                    defaults={'name': ethnicity_slug.title()}
                )
            
            # Get or create category
            category = None
            if category_slug:
                category, _ = Category.objects.get_or_create(
                    slug=category_slug,
                    defaults={'name': category_slug.replace('-', ' ').title()}
                )
            
            # Check if recipe already exists (by title or slug)
            recipe_slug = slugify(recipe_data['title'])
            if Recipe.objects.filter(slug=recipe_slug).exists():
                self.skipped_count += 1
                return None
            
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
            )
            
            # Create ingredients
            for ingredient_data in recipe_data.get('ingredients', []):
                Ingredient.objects.create(
                    recipe=recipe,
                    name=ingredient_data['name'],
                    quantity=ingredient_data.get('quantity', 1),
                    unit=ingredient_data.get('unit', 'piece'),
                    notes=ingredient_data.get('notes', '')
                )
            
            # Create notes
            for note_text in recipe_data.get('notes', []):
                if note_text.strip():
                    RecipeNote.objects.create(
                        recipe=recipe,
                        note=note_text
                    )
            
            self.scraped_count += 1
            return recipe
            
        except Exception as e:
            self.errors.append({
                'recipe': recipe_data.get('title', 'Unknown'),
                'error': str(e)
            })
            self.skipped_count += 1
            return None
    
    def scrape_recipe_list(self, list_url):
        """
        Scrape a list of recipe URLs from a category/archive page
        This method should be overridden by site-specific scrapers
        
        Args:
            list_url: URL of page containing recipe links
            
        Returns:
            List of recipe URLs
        """
        raise NotImplementedError("Subclass must implement scrape_recipe_list()")
    
    def scrape_recipe_detail(self, recipe_url):
        """
        Scrape details from a single recipe page
        This method should be overridden by site-specific scrapers
        
        Args:
            recipe_url: URL of recipe page
            
        Returns:
            Dictionary containing recipe data
        """
        raise NotImplementedError("Subclass must implement scrape_recipe_detail()")
    
    def get_summary(self):
        """
        Get summary of scraping operation
        
        Returns:
            Dictionary with statistics
        """
        return {
            'scraped': self.scraped_count,
            'skipped': self.skipped_count,
            'errors': len(self.errors),
            'error_details': self.errors
        }


class AllNigerianFoodsScraper(BaseRecipeScraper):
    """
    Scraper specifically for allnigerianfoods.com
    
    This site has a consistent structure that we can target.
    Note: HTML structure may change, so selectors might need updates.
    """
    
    def __init__(self):
        super().__init__('https://www.allnigerianfoods.com')
    
    def scrape_recipe_list(self, list_url, max_recipes=10):
        """
        Scrape recipe URLs from a category page
        
        Args:
            list_url: URL of category page
            max_recipes: Maximum number of recipes to scrape
            
        Returns:
            List of recipe URLs
        """
        soup = self.get_page(list_url)
        if not soup:
            return []
        
        recipe_urls = []
        
        # Find all recipe links
        # Adjust these selectors based on actual site structure
        recipe_links = soup.find_all('a', class_='recipe-link')[:max_recipes]
        
        # Alternative: if no specific class
        if not recipe_links:
            # Find all links in article containers
            articles = soup.find_all('article')[:max_recipes]
            for article in articles:
                link = article.find('a', href=True)
                if link:
                    recipe_links.append(link)
        
        for link in recipe_links:
            href = link.get('href', '')
            if href:
                # Make sure we have absolute URL
                full_url = urljoin(self.base_url, href)
                recipe_urls.append(full_url)
        
        return recipe_urls
    
    def scrape_recipe_detail(self, recipe_url):
        """
        Scrape a single recipe page
        
        Args:
            recipe_url: URL of recipe page
            
        Returns:
            Dictionary with recipe data
        """
        soup = self.get_page(recipe_url)
        if not soup:
            return None
        
        recipe_data = {
            'title': '',
            'description': '',
            'instructions': '',
            'prep_time': 30,
            'cook_time': 30,
            'servings': 4,
            'ingredients': [],
            'notes': []
        }
        
        try:
            # Extract title
            # Try multiple possible selectors
            title = (
                soup.find('h1', class_='recipe-title') or 
                soup.find('h1', class_='entry-title') or
                soup.find('h1')
            )
            if title:
                recipe_data['title'] = self.clean_text(title.get_text())
            
            # Extract description
            description = soup.find('div', class_='recipe-description')
            if description:
                recipe_data['description'] = self.clean_text(description.get_text())
            
            # Extract prep time
            prep_time = soup.find('span', class_='prep-time')
            if prep_time:
                recipe_data['prep_time'] = self.extract_time(prep_time.get_text())
            
            # Extract cook time
            cook_time = soup.find('span', class_='cook-time')
            if cook_time:
                recipe_data['cook_time'] = self.extract_time(cook_time.get_text())
            
            # Extract servings
            servings = soup.find('span', class_='servings')
            if servings:
                recipe_data['servings'] = self.extract_servings(servings.get_text())
            
            # Extract ingredients
            ingredients_section = soup.find('div', class_='ingredients') or soup.find('ul', class_='ingredients')
            if ingredients_section:
                ingredient_items = ingredients_section.find_all(['li', 'p'])
                for item in ingredient_items:
                    ingredient_text = self.clean_text(item.get_text())
                    if ingredient_text:
                        parsed = self.parse_ingredient(ingredient_text)
                        recipe_data['ingredients'].append(parsed)
            
            # Extract instructions
            instructions_section = soup.find('div', class_='instructions')
            if instructions_section:
                instruction_items = instructions_section.find_all(['li', 'p', 'div'])
                instructions_list = []
                for idx, item in enumerate(instruction_items, 1):
                    text = self.clean_text(item.get_text())
                    if text:
                        # Number the steps if not already numbered
                        if not text[0].isdigit():
                            text = f"{idx}. {text}"
                        instructions_list.append(text)
                recipe_data['instructions'] = '\n'.join(instructions_list)
            
            # Extract notes/tips
            notes_section = soup.find('div', class_='recipe-notes') or soup.find('div', class_='tips')
            if notes_section:
                note_items = notes_section.find_all(['li', 'p'])
                for item in note_items:
                    note_text = self.clean_text(item.get_text())
                    if note_text:
                        recipe_data['notes'].append(note_text)
            
            return recipe_data
            
        except Exception as e:
            self.errors.append({
                'url': recipe_url,
                'error': f"Error parsing recipe: {str(e)}"
            })
            return None


class GenericNigerianRecipeScraper(BaseRecipeScraper):
    """
    Generic scraper that works with common recipe markup patterns
    
    This uses a flexible approach that can work with many sites.
    It looks for common HTML patterns used in recipe sites.
    """
    
    def __init__(self, base_url):
        super().__init__(base_url)
    
    def scrape_recipe_list(self, list_url, max_recipes=10):
        """
        Generic method to find recipe links
        
        Looks for common patterns like:
        - Links within article tags
        - Links with 'recipe' in URL
        - Links in specific containers
        """
        soup = self.get_page(list_url)
        if not soup:
            return []
        
        recipe_urls = []
        
        # Strategy 1: Find all article containers
        articles = soup.find_all('article')
        for article in articles[:max_recipes]:
            link = article.find('a', href=True)
            if link:
                href = link['href']
                full_url = urljoin(self.base_url, href)
                recipe_urls.append(full_url)
        
        # Strategy 2: If no articles found, look for links containing 'recipe'
        if not recipe_urls:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if 'recipe' in href.lower() or 'food' in href.lower():
                    full_url = urljoin(self.base_url, href)
                    # Avoid duplicate URLs
                    if full_url not in recipe_urls:
                        recipe_urls.append(full_url)
                        if len(recipe_urls) >= max_recipes:
                            break
        
        return recipe_urls
    
    def scrape_recipe_detail(self, recipe_url):
        """
        Generic recipe scraper using multiple strategies
        """
        soup = self.get_page(recipe_url)
        if not soup:
            return None
        
        recipe_data = {
            'title': '',
            'description': '',
            'instructions': '',
            'prep_time': 30,
            'cook_time': 30,
            'servings': 4,
            'ingredients': [],
            'notes': []
        }
        
        try:
            # Title - try common patterns
            title = (
                soup.find('h1', class_=re.compile(r'title|heading|name', re.I)) or
                soup.find('h1') or
                soup.find('title')
            )
            if title:
                recipe_data['title'] = self.clean_text(title.get_text())
            
            # Description - usually in first paragraph or meta description
            description = (
                soup.find('div', class_=re.compile(r'description|summary|intro', re.I)) or
                soup.find('p', class_=re.compile(r'description|summary', re.I)) or
                soup.find('meta', attrs={'name': 'description'})
            )
            if description:
                if description.name == 'meta':
                    recipe_data['description'] = description.get('content', '')
                else:
                    recipe_data['description'] = self.clean_text(description.get_text())
            
            # Time information - look for common time patterns
            time_elements = soup.find_all(text=re.compile(r'prep|cook|time', re.I))
            for elem in time_elements:
                text = elem.strip().lower()
                if 'prep' in text:
                    recipe_data['prep_time'] = self.extract_time(text)
                elif 'cook' in text:
                    recipe_data['cook_time'] = self.extract_time(text)
            
            # Servings
            servings_elem = soup.find(text=re.compile(r'serve|serving|yield', re.I))
            if servings_elem:
                recipe_data['servings'] = self.extract_servings(servings_elem)
            
            # Ingredients - look for lists
            ingredients_section = (
                soup.find(['ul', 'ol', 'div'], class_=re.compile(r'ingredient', re.I)) or
                soup.find(['ul', 'ol'], id=re.compile(r'ingredient', re.I))
            )
            if ingredients_section:
                items = ingredients_section.find_all('li')
                for item in items:
                    ingredient_text = self.clean_text(item.get_text())
                    if ingredient_text:
                        parsed = self.parse_ingredient(ingredient_text)
                        recipe_data['ingredients'].append(parsed)
            
            # Instructions - look for ordered lists or divs
            instructions_section = (
                soup.find(['ol', 'ul', 'div'], class_=re.compile(r'instruction|direction|method|step', re.I)) or
                soup.find(['ol', 'ul'], id=re.compile(r'instruction|direction|method', re.I))
            )
            if instructions_section:
                items = instructions_section.find_all(['li', 'p'])
                instructions_list = []
                for idx, item in enumerate(items, 1):
                    text = self.clean_text(item.get_text())
                    if text:
                        if not text[0].isdigit():
                            text = f"{idx}. {text}"
                        instructions_list.append(text)
                recipe_data['instructions'] = '\n'.join(instructions_list)
            
            # Notes - look for tips/notes sections
            notes_section = soup.find(['div', 'ul'], class_=re.compile(r'note|tip|hint', re.I))
            if notes_section:
                note_items = notes_section.find_all(['li', 'p'])
                for item in note_items:
                    note_text = self.clean_text(item.get_text())
                    if note_text:
                        recipe_data['notes'].append(note_text)
            
            return recipe_data
            
        except Exception as e:
            self.errors.append({
                'url': recipe_url,
                'error': f"Error parsing recipe: {str(e)}"
            })
            return None


# Convenience function for quick scraping
def scrape_recipes_from_url(url, max_recipes=10, ethnicity='yoruba', category=None):
    """
    Quick function to scrape recipes from a URL
    
    Args:
        url: URL to scrape (either list page or single recipe)
        max_recipes: Maximum number of recipes to scrape
        ethnicity: Ethnicity slug (yoruba, igbo, hausa)
        category: Optional category slug
        
    Returns:
        Dictionary with scraping summary
    """
    # Determine which scraper to use based on URL
    if 'allnigerianfoods.com' in url:
        scraper = AllNigerianFoodsScraper()
    else:
        # Use generic scraper for other sites
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        scraper = GenericNigerianRecipeScraper(base_url)
    
    # Decide if this is a list page or single recipe
    if 'recipe' in url.lower() or 'food' in url.lower():
        # Likely a single recipe page
        recipe_urls = [url]
    else:
        # Likely a list/category page
        recipe_urls = scraper.scrape_recipe_list(url, max_recipes)
    
    # Scrape each recipe
    for recipe_url in recipe_urls:
        print(f"Scraping: {recipe_url}")
        recipe_data = scraper.scrape_recipe_detail(recipe_url)
        
        if recipe_data and recipe_data.get('title'):
            scraper.save_recipe(recipe_data, ethnicity, category)
        
        # Be polite - wait between requests
        time.sleep(2)
    
    return scraper.get_summary()