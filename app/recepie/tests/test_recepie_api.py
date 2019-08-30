from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recepie

from recepie.serializers import RecepieSerializer

RECEPIE_URLS = reverse('recepie:recepie-list')


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
        