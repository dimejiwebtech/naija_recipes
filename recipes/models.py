from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator

class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class Ethnicity(TimeStampModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Ethnicities"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Category(TimeStampModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Recipe(TimeStampModel):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField()
    instructions = models.TextField(help_text="Step by step cooking instructions.")

    prep_time = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Preparation time in minutes.")
    cook_time = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Cooking time in minutes.")
    servings = models.PositiveIntegerField(default=4, validators=[MinValueValidator(1)], help_text="Number of servings.")

    ethnicity = models.ForeignKey(Ethnicity, on_delete=models.SET_NULL, null=True, related_name='recipes', help_text='Yoruba, Igbo, Hausa, etc.')

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='recipes')
    image = models.ImageField(upload_to='recipes/%Y/%m/%d/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['ethnicity']),
            models.Index(fields=['category']),
            models.Index(fields=['slug'])
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    @property
    def total_time(self):
        return self.prep_time + self.cook_time
    

class Ingredient(models.Model):

    UNIT_CHOICES = [
        # Weight
        ('g', 'grams'),
        ('kg', 'kilograms'),

        # Volume
        ('ml', 'milliliters'),
        ('l', 'liters'),
        ('cup', 'Cup'),
        ('tbsp', 'tablespoon'),
        ('tsp', 'teaspoon'),

        # Common Measurements
        ('piece', 'Piece'),
        ('bunch', 'Bunch'),
        ('handful', 'Handful'),
        ('wrap', 'Wrap'),
        ('seed', 'Seed'),
        ('cube', 'Cube'),
        ('bulb', 'Bulb'),
        ('pinch', 'Pinch'),
        ('to taste', 'To Taste'),
        ('as needed', 'As Needed'),
    ]

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, help_text="Amount Needed")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES,)

    notes = models.CharField(max_length=300, blank=True, help_text="e.g., chopped, diced, softened")

    class Meta:
        ordering = ['id']

    def __str__(self):
        base = f"{self.quantity} {self.get_unit_display()} {self.name}"
        if self.notes:
            return f"{base} ({self.notes})"
        return base
    
class RecipeNote(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='notes')
    note = models.TextField()

    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"Note for {self.recipe.title}"



