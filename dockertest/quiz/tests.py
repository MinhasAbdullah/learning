from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Application, Company, Job


User = get_user_model()

class PortalApiTest(APITestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username='recruiter',
            password='demo1234',
            email='recruiter@example.com',
            profile_type='recruiter'
        )
        self.company = Company.objects.create(
            name ='Tech Corp',
            owner=self.recruiter
        )
        self.recruiter2 = User.objects.create_user(
            username='recruiter2',
            password='demo1234',
            email='recruiter2@example.com',
            profile_type='recruiter'
        )
        self.job = Job.objects.create(
            title = 'Backend Developer',
            description = 'We are looking for a skilled backend developer.',
            salary = 80000,
            location = 'New York',
            company = self.company,
        )
        self.candidate = User.objects.create_user(
            username='candidate',
            password='demo1234',
            profile_type='candidate'
        )

    def test_register_success(self):
        data = {
            'username':'newuser',
            'email':'newuser@example.com',
            'password':'demo1234',
            'confirm_password':'demo1234',
            'profile_type':'candidate'
        }

        response = self.client.post('/quiz/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_fail(self):
        data = {
            'username' : 'newuser',
            'email' : 'demo@gmail.com',
            'password' : 'demo1234',
            'confirm_password' : 'different',
            'profile_type' : 'recruiter',
        }

        response = self.client.post('/quiz/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login(self):
        data = {
            'username' : 'recruiter',
            'password' : 'demo1234'
        }

        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong(self):
        data = {
            'username' : 'recruiter',
            'password' : '1234'
        }

        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_job(self):
        self.client.force_authenticate(user=self.recruiter)
        data = {
            'title': 'frontend developer',
            'description': 'a good frontend developer',
            'salary': '10000.00',
            'location' : 'rawalpindi ',
            'company_id' : self.company.id
        }
        response = self.client.post('/quiz/jobs/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.count(), 2)

    def test_create_job_unauth(self):
        data = {
                    'title': 'frontend developer',
                    'description': 'a good frontend developer',
                    'salary': '10000.00',
                    'location' : 'rawalpindi ',
                    'company_id' : self.company.id
                }

        response = self.client.post('/quiz/jobs/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jobapply(self):
        self.client.force_authenticate(user=self.candidate)
        data = {
            'cover_letter':'i am interested'
        }
        response = self.client.post(f'/quiz/jobs/{self.job.id}/apply/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Application.objects.filter(job=self.job, applicant=self.candidate).exists())

    def test_jobapply_twice(self):
        self.client.force_authenticate(user=self.candidate)
        data = {
                  'cover_letter':'i am interested'
              }  
        self.client.post(f'/quiz/jobs/{self.job.id}/apply/', data)
        
        # Second application fails with 400
        response = self.client.post(f'/quiz/jobs/{self.job.id}/apply/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonowner(self):
        self.client.force_authenticate(user= self.recruiter2)
        data = {
            'title': 'Hacked Job Title',
            'description': 'Malicious edit',
            'salary': '999999.00',
            'location': 'Unknown',
            'company_id': self.company.id
        }
        response = self.client.put(f'/quiz/jobs/{self.job.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, 'Backend Developer')


