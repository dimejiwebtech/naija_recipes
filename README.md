# Nigerian Recipe Box

A comprehensive web application and REST API for exploring authentic Nigerian recipes from Yoruba, Igbo, and Hausa cuisines. Built with Django, Django REST Framework, Tailwind CSS, and Alpine.js.

## Features

### Web Application
- Browse recipes from three major Nigerian ethnic groups (Yoruba, Igbo, Hausa)
- Search recipes by name, ingredients, or description
- Filter recipes by ethnicity and category
- Detailed recipe pages with ingredients and step-by-step instructions
- Responsive design for mobile, tablet, and desktop
- Interactive ingredient checklist

### REST API
- Complete CRUD operations for recipes, categories, and ethnicities
- Advanced filtering and search capabilities
- Pagination support
- Interactive API documentation (Swagger/ReDoc)
- Statistics endpoint for recipe analytics

### Data Import Tools
- JSON batch import for recipe data
- Web scraping utility for recipe websites
- PDF extraction for cookbook digitization

## Technology Stack

**Backend:**
- Django 6.0+
- Django REST Framework
- SQLite
- drf-spectacular for API documentation

**Frontend:**
- Tailwind CSS for styling
- Alpine.js for interactivity
- Responsive design principles

**Testing:**
- pytest for unit and integration tests
- pytest-django for Django-specific testing
- Comprehensive test coverage

**Deployment:**
- Render.com platform
- Gunicorn WSGI server
- WhiteNoise for static file serving

## Getting Started

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Virtual environment (recommended)

### Local Development Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd naija_recipes
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from template:
```bash
cp .env.example .env
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Import sample recipes:
```bash
python manage.py import_json data/sample_recipes.json
```

8. Run development server:
```bash
python manage.py runserver
```

9. Access the application:
- Web Interface: http://127.0.0.1:8000/
- Admin Panel: http://127.0.0.1:8000/admin/
- API Documentation: http://127.0.0.1:8000/api/docs/

## API Endpoints

### Recipes
- `GET /api/recipes/` - List all recipes (paginated)
- `POST /api/recipes/` - Create new recipe
- `GET /api/recipes/{slug}/` - Get recipe details
- `PUT /api/recipes/{slug}/` - Update recipe
- `DELETE /api/recipes/{slug}/` - Delete recipe
- `GET /api/recipes/by_ethnicity/?ethnicity=yoruba` - Filter by ethnicity
- `GET /api/recipes/quick_recipes/?max_time=45` - Get quick recipes
- `GET /api/recipes/statistics/` - Get recipe statistics

### Categories
- `GET /api/categories/` - List all categories
- `POST /api/categories/` - Create category
- `GET /api/categories/{slug}/` - Get category details

### Ethnicities
- `GET /api/ethnicities/` - List all ethnicities
- `POST /api/ethnicities/` - Create ethnicity
- `GET /api/ethnicities/{slug}/` - Get ethnicity details

### API Documentation
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

## Data Import

### JSON Import
```bash
python manage.py import_json path/to/recipes.json
```

### Web Scraping
```bash
python manage.py scrape_recipes <url> --ethnicity yoruba --max 10
```

### PDF Import
```bash
python manage.py import_pdf path/to/cookbook.pdf --ethnicity igbo
```

## Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=recipes

# Run specific test categories
pytest -m api      # API tests only
pytest -m models   # Model tests only

# Generate HTML coverage report
pytest --cov=recipes --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## Code Quality

This project follows:
- DRY (Don't Repeat Yourself) principles
- KISS (Keep It Simple, Stupid) approach
- PEP 8 style guide for Python code
- Django best practices
- RESTful API design principles

## License

This project is licensed under the MIT License.

## Acknowledgments

- Recipe data sourced from authentic Nigerian cuisine resources
- Built with Django and Django REST Framework
- UI styled with Tailwind CSS
- Interactive elements powered by Alpine.js

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

## Author

Developed as a learning project for mastering Django, Django REST Framework, Tailwind CSS, and Alpine.js.
