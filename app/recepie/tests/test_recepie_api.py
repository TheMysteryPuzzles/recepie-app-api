import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recepie, Tag, Ingredient

from recepie.serializers import RecepieSerializer, RecepieDetailSerializer

RECEPIE_URLS = reverse('recepie:recepie-list')


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recepie:recepie-upload-image', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recepie:recepie-detail', args=[recipe_id])


def sample_recepie(user, **params):
    defaults = {
        'title': 'sample recepie',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)
    return Recepie.objects.create(user=user, **defaults)


class PublicRecepieApiTest(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        
    def test_auth_required(self):
        res = self.client.get(RECEPIE_URLS)
        
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)    


class PrivateRecepieApiTest(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'email@gmail.com',
            '12345678'
        )
        self.client.force_authenticate(self.user)
        
    def test_retrieve_recepies(self):
        sample_recepie(self.user)
        sample_recepie(self.user)
        
        res = self.client.get(RECEPIE_URLS)
        
        recepie = Recepie.objects.all().order_by('-id')
        serializer = RecepieSerializer(recepie, many=True)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        
    def test_recepies_limited_to_user(self):
        
        user2 = get_user_model().objects.create_user(
            'email2@gmail.com',
            '1234567'
        )
        
        sample_recepie(user=user2)
        sample_recepie(user=self.user)
        
        res = self.client.get(RECEPIE_URLS)
        
        recepie = Recepie.objects.filter(user=self.user)
        serializer = RecepieSerializer(recepie, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
    
    def test_view_recepie_detail(self):
        """Test viewing a recipe detail"""
        recepie = sample_recepie(user=self.user)
        recepie.tags.add(sample_tag(user=self.user))
        recepie.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recepie.id)
        res = self.client.get(url)

        serializer = RecepieDetailSerializer(recepie)
        self.assertEqual(res.data, serializer.data)
    
    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Test recipe',
            'time_minutes': 30,
            'price': 10.00,
        }
        res = self.client.post(RECEPIE_URLS, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recepie.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        
        tag1 = sample_tag(user=self.user, name='Tag 1')
        tag2 = sample_tag(user=self.user, name='Tag 2')
        payload = {
            'title': 'Test recipe with two tags',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECEPIE_URLS, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recepie.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name='Ingredient 1')
        ingredient2 = sample_ingredient(user=self.user, name='Ingredient 2')
        payload = {
            'title': 'Test recipe with ingredients',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 45,
            'price': 15.00
        }

        res = self.client.post(RECEPIE_URLS, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recepie.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)
        
    def test_partial_update_recepie(self):
        recepie = sample_recepie(user=self.user)
        recepie.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')
        payload = {
            'title': 'New Recepie Changed',
            'tags': [new_tag.id]
        }
        url = detail_url(recepie.id)
        self.client.patch(url, payload)
        
        recepie.refresh_from_db()
        self.assertEqual(recepie.title, payload['title'])
        tags = recepie.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)
    
    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = sample_recepie(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
                'title': 'Spaghetti carbonara',
                'time_minutes': 25,
                'price': 5.00
            }
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)
        
    
class RecipeImageUploadTests(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('user', 'testpass')
        self.client.force_authenticate(self.user)
        self.recepie = sample_recepie(user=self.user)

    def tearDown(self):
        self.recepie.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recepie.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recepie.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recepie.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recepie.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)