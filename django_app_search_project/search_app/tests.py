from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import App, AppReview, UserReview, UserProfile

class AppSearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test app
        self.app = App.objects.create(
            name='Test App',
            category='Productivity',
            rating=4.5,
            reviews_count=100
        )
        
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        UserProfile.objects.create(user=self.user, is_supervisor=False)
        
        self.supervisor = User.objects.create_user(
            username='supervisor',
            password='supervisor123',
            email='supervisor@example.com'
        )
        UserProfile.objects.create(user=self.supervisor, is_supervisor=True)
    
    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'App Search Engine')
    
    def test_search_functionality(self):
        response = self.client.get(reverse('search_results'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test App')
    
    def test_search_suggestions(self):
        response = self.client.get(reverse('search_suggestions'), {'q': 'Tes'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('Test App', data)
    
    def test_app_detail_page(self):
        response = self.client.get(reverse('app_detail', args=[self.app.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test App')
    
    def test_user_review_submission(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('app_detail', args=[self.app.id]), {
            'review_text': 'Great app!',
            'rating': 5
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            UserReview.objects.filter(
                app=self.app,
                user=self.user,
                status='pending'
            ).exists()
        )
    
    def test_supervisor_dashboard(self):
        # Create pending review
        review = UserReview.objects.create(
            app=self.app,
            user=self.user,
            review_text='Test review',
            rating=4,
            status='pending'
        )
        
        self.client.login(username='supervisor', password='supervisor123')
        response = self.client.get(reverse('supervisor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test review')
    
    def test_review_approval(self):
        review = UserReview.objects.create(
            app=self.app,
            user=self.user,
            review_text='Test review',
            rating=4,
            status='pending'
        )
        
        self.client.login(username='supervisor', password='supervisor123')
        response = self.client.post(
            reverse('approve_review', args=[review.id]),
            {'action': 'approve'}
        )
        self.assertEqual(response.status_code, 302)
        
        review.refresh_from_db()
        self.assertEqual(review.status, 'approved')
        self.assertEqual(review.approved_by, self.supervisor)