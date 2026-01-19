import re
import pdfplumber
from recipes.models import Recipe, Ingredient, Category, Ethnicity, RecipeNote


class PDFRecipeParser:
    
    def __init__(self, pdf_path):

        self.pdf_path = pdf_path
        self.recipes = []
        self.errors = []
    
    def extract_text_from_pdf(self):
        try:
            full_text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n\n"
            return full_text
        except Exception as e:
            self.errors.append(f"Error reading PDF: {str(e)}")
            return ""
    
    def split_into_recipes(self, text):
        
        # Split by double newlines first
        sections = text.split('\n\n')
        
        recipe_blocks = []
        current_block = []
        
        for section in sections:
            section = section.strip()
            
            # Check if this looks like a recipe title
            if self._is_likely_title(section):
                # Save previous block if it exists
                if current_block:
                    recipe_blocks.append('\n'.join(current_block))
                # Start new block
                current_block = [section]
            else:
                # Add to current block
                if section:  # Skip empty sections
                    current_block.append(section)
        
        # Add the last block
        if current_block:
            recipe_blocks.append('\n'.join(current_block))
        
        return recipe_blocks
    
    def _is_likely_title(self, text):
        
        if len(text) > 50:
            return False
        
        if text[0].isdigit():
            return False
        
        # Common Nigerian food keywords
        food_keywords = [
            'rice', 'soup', 'stew', 'jollof', 'egusi', 'efo', 'okra',
            'beans', 'yam', 'plantain', 'chicken', 'fish', 'meat',
            'pepper', 'tuwo', 'masa', 'moi moi', 'akara', 'suya',
            'fufu', 'garri', 'amala', 'pounded', 'fried', 'boiled'
        ]
        
        text_lower = text.lower()
        for keyword in food_keywords:
            if keyword in text_lower:
                return True
        
        if text.isupper() and len(text) > 3:
            return True
        
        return False
    
    def parse_recipe_block(self, recipe_text):
        lines = recipe_text.split('\n')
        
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
        
        for line in lines:
            if line.strip():
                recipe_data['title'] = line.strip()
                break
        
        # Find sections
        ingredient_section = []
        instruction_section = []
        notes_section = []
        description_section = []
        
        current_section = None
        
        for line in lines[1:]: 
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            # Detect section headers
            if any(word in line_lower for word in ['ingredient', 'you will need', 'what you need']):
                current_section = 'ingredients'
                continue
            elif any(word in line_lower for word in ['instruction', 'method', 'direction', 'preparation', 'how to', 'steps']):
                current_section = 'instructions'
                continue
            elif any(word in line_lower for word in ['note', 'tip', 'hint', 'suggestion']):
                current_section = 'notes'
                continue
            elif any(word in line_lower for word in ['serve', 'serving', 'yield']):
                # Extract servings
                numbers = re.findall(r'\d+', line)
                if numbers:
                    recipe_data['servings'] = int(numbers[0])
                continue
            elif any(word in line_lower for word in ['prep time', 'preparation time']):
                # Extract prep time
                numbers = re.findall(r'\d+', line)
                if numbers:
                    recipe_data['prep_time'] = int(numbers[0])
                continue
            elif any(word in line_lower for word in ['cook time', 'cooking time']):
                # Extract cook time
                numbers = re.findall(r'\d+', line)
                if numbers:
                    recipe_data['cook_time'] = int(numbers[0])
                continue
            
            # Add line to appropriate section
            if current_section == 'ingredients':
                ingredient_section.append(line)
            elif current_section == 'instructions':
                instruction_section.append(line)
            elif current_section == 'notes':
                notes_section.append(line)
            elif current_section is None and not recipe_data['description']:
                
                description_section.append(line)
        
        # Process description
        if description_section:
            recipe_data['description'] = ' '.join(description_section)
        
        # Process ingredients
        for ing_line in ingredient_section:
            if ing_line.strip():
                parsed_ing = self._parse_ingredient_line(ing_line)
                if parsed_ing:
                    recipe_data['ingredients'].append(parsed_ing)
        
        # Process instructions
        if instruction_section:
            recipe_data['instructions'] = '\n'.join(instruction_section)
        
        # Process notes
        recipe_data['notes'] = [note for note in notes_section if note.strip()]
        
        # Validate - must have title and at least one ingredient
        if not recipe_data['title'] or not recipe_data['ingredients']:
            return None
        
        return recipe_data
    
    def _parse_ingredient_line(self, line):
        line = line.strip()
        
        # Remove bullet points or list markers
        line = re.sub(r'^[\-\*\•\◦]\s*', '', line)
        
        result = {
            'name': line, 
            'quantity': 1,
            'unit': 'piece',
            'notes': ''
        }
        
        # Unit mapping
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
    
        pattern = r'^([\d./]+)\s*([a-zA-Z]+)?\s+(.+)$'
        match = re.match(pattern, line)
        
        if match:
            quantity_str = match.group(1)
            unit_str = match.group(2)
            name_and_notes = match.group(3)
            
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
            
            if ',' in name_and_notes:
                name_part, notes_part = name_and_notes.split(',', 1)
                result['name'] = name_part.strip()
                result['notes'] = notes_part.strip()
            else:
                result['name'] = name_and_notes.strip()
        
        return result
    
    def parse_pdf(self):

        # Extract text
        full_text = self.extract_text_from_pdf()
        
        if not full_text:
            return []
        
        # Split into recipe blocks
        recipe_blocks = self.split_into_recipes(full_text)
        
        # Parse each block
        for block in recipe_blocks:
            recipe_data = self.parse_recipe_block(block)
            if recipe_data:
                self.recipes.append(recipe_data)
        
        return self.recipes
    
    def save_to_database(self, default_ethnicity='yoruba', default_category=None):

        created_count = 0
        skipped_count = 0
        errors = []
        
        # Get or create default ethnicity
        ethnicity, _ = Ethnicity.objects.get_or_create(
            slug=default_ethnicity,
            defaults={'name': default_ethnicity.title()}
        )
        
        category = None
        if default_category:
            category, _ = Category.objects.get_or_create(
                slug=default_category,
                defaults={'name': default_category.replace('-', ' ').title()}
            )
        
        for recipe_data in self.recipes:
            try:
                # Check if recipe already exists
                from django.utils.text import slugify
                slug = slugify(recipe_data['title'])
                
                if Recipe.objects.filter(slug=slug).exists():
                    skipped_count += 1
                    continue
                
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
                    if note_text.strip():
                        RecipeNote.objects.create(
                            recipe=recipe,
                            note=note_text
                        )
                
                created_count += 1
                
            except Exception as e:
                errors.append({
                    'recipe': recipe_data.get('title', 'Unknown'),
                    'error': str(e)
                })
                skipped_count += 1
        
        return {
            'success': True,
            'created': created_count,
            'skipped': skipped_count,
            'errors': errors,
            'total_parsed': len(self.recipes)
        }


class SimplePDFExtractor:
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
    
    def extract_to_text_file(self, output_path):
        try:
            full_text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    full_text += f"\n\n=== PAGE {i+1} ===\n\n"
                    text = page.extract_text()
                    if text:
                        full_text += text
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            return True
        except Exception as e:
            print(f"Error: {str(e)}")
            return False
    
    def extract_tables(self):
        all_tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
        except Exception as e:
            print(f"Error extracting tables: {str(e)}")
        
        return all_tables