from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recepie import views

router = DefaultRouter()
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)
router.register('recepies', views.RecepieViewSet)

app_name = 'recepie'

urlpatterns = [
    path('', include(router.urls))
]