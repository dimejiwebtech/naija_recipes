from django.contrib import admin
from .models import Recipe, Ingredient, Category, Ethnicity, RecipeNote


class IngredientInline(admin.TabularInline):
    # Add/Edit ingredients directly on the recipe admin page

    model = Ingredient
    extra = 1  # Show 1 empty form for adding new ingredients
    fields = ['name', 'quantity', 'unit', 'notes']


class RecipeNoteInline(admin.TabularInline):
    # Add/Edit recipe notes directly on the recipe admin page
    model = RecipeNote
    extra = 1
    fields = ['note']


@admin.register(Ethnicity)
class EthnicityAdmin(admin.ModelAdmin):
    # Admin interface for Nigerian ethnic groups
    list_display = ['name', 'slug']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}  
    # readonly_fields = ['created_at', 'updated_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Admin interface for recipe categories
    list_display = ['name', 'slug']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    # readonly_fields = ['created_at', 'updated_at']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    # Admin interface for recipes
    list_display = ['title', 'ethnicity', 'category', 'prep_time', 'cook_time', 'servings', 'is_active', 'created_at']
    list_filter = ['ethnicity', 'category', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'instructions']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    list_editable = ['is_active']  
    
    # Show ingredients and notes inline
    inlines = [IngredientInline, RecipeNoteInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'ethnicity', 'category', 'image')
        }),
        ('Cooking Details', {
            'fields': ('instructions', 'prep_time', 'cook_time', 'servings')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Collapsible section
        }),
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    # Admin interface for ingredients
    list_display = ['name', 'quantity', 'unit', 'recipe', 'notes']
    list_filter = ['unit']
    search_fields = ['name', 'recipe__title']


@admin.register(RecipeNote)
class RecipeNoteAdmin(admin.ModelAdmin):
    # Admin interface for recipe notes
    list_display = ['recipe', 'note_preview']
    search_fields = ['recipe__title', 'note']
    
    def note_preview(self, obj):
        """Show first 50 characters of note"""
        return obj.note[:50] + '...' if len(obj.note) > 50 else obj.note
    note_preview.short_description = 'Note'