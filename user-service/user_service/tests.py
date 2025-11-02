from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class UserEndpointsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_password = "TestPass123"
        self.user = User.objects.create(
            first_name="Test",
            last_name="User",
            email="testuser@example.com",
            phone_number="1234567890"
        )
        self.user.set_password(self.user_password)
        self.user.save()

    # REGISTER
    def test_register(self):
        url = reverse('register')
        data = {
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "phone_number": "0987654321",
            "password": "NewPass123"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)

    # LOGIN
    def test_login(self):
        url = reverse('login')
        data = {
            "email": self.user.email,
            "password": self.user_password
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)

    # LOGOUT
    def test_logout(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('logout')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data['detail'], "Logged out successfully")

    # USER PROFILE GET
    def test_user_profile_get(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('user-profile')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    # USER PROFILE PUT
    def test_user_profile_put(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('user-profile')
        data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "updateduser@example.com",
            "phone_number": "1112223333"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], "Updated")
        self.assertEqual(response.data['email'], "updateduser@example.com")

    # USER PROFILE PATCH

    

