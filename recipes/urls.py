from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, CategoryViewSet, EthnicityViewSet
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .views import (
    # API ViewSets
    RecipeViewSet, 
    CategoryViewSet, 
    EthnicityViewSet,
    # Template views
    recipe_list_view,
    recipe_detail_view,
    ethnicity_view,
)

# Router automatically generates URLs for ViewSets
router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'ethnicities', EthnicityViewSet, basename='ethnicity')

app_name = 'recipes'

urlpatterns = [
    # API Documentation URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='recipes:schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='recipes:schema'), name='redoc'),

    # API endpoints
    path('api/v1/', include(router.urls)),
    
    # Template views
    path('', recipe_list_view, name='recipe_list'),
    path('recipe/<slug:slug>/', recipe_detail_view, name='recipe_detail'),
    path('ethnicity/<slug:slug>/', ethnicity_view, name='ethnicity_detail'),
]