from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib import messages
from unittest.mock import patch
from .models import App, AppReview, UserReview, UserProfile

class AppSearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test app
        self.app = App.objects.create(
            name='Test App',
            category='Productivity',
            rating=4.5,
            reviews_count=100,
            genres='Productivity;Business'
        )
        
        # Create another app for search testing
        self.app2 = App.objects.create(
            name='Social Media App',
            category='Social',
            rating=3.8,
            reviews_count=50,
            genres='Social;Communication'
        )
        
        # Create supervisors
        self.supervisor1 = User.objects.create_user(
            username='supervisor1',
            password='supervisor123',
            email='supervisor1@example.com',
            first_name='John',
            last_name='Manager'
        )
        UserProfile.objects.create(user=self.supervisor1, is_supervisor=True)
        
        self.supervisor2 = User.objects.create_user(
            username='supervisor2',
            password='supervisor123',
            email='supervisor2@example.com',
            first_name='Sarah',
            last_name='Director'
        )
        UserProfile.objects.create(user=self.supervisor2, is_supervisor=True)
        
        # Create users with supervisor assignments
        self.user1 = User.objects.create_user(
            username='employee1',
            password='testpass123',
            email='employee1@example.com',
            first_name='Alice',
            last_name='Johnson'
        )
        UserProfile.objects.create(
            user=self.user1, 
            is_supervisor=False, 
            supervisor=self.supervisor1
        )
        
        self.user2 = User.objects.create_user(
            username='employee2',
            password='testpass123',
            email='employee2@example.com',
            first_name='Bob',
            last_name='Smith'
        )
        UserProfile.objects.create(
            user=self.user2, 
            is_supervisor=False, 
            supervisor=self.supervisor2
        )
        
        # Create user without supervisor
        self.user_no_supervisor = User.objects.create_user(
            username='orphan_user',
            password='testpass123',
            email='orphan@example.com'
        )
        UserProfile.objects.create(
            user=self.user_no_supervisor, 
            is_supervisor=False,
            supervisor=None
        )

    def test_home_page(self):
        """Test home page loads correctly"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'App Search Engine')
        self.assertContains(response, 'Smart Search')

    def test_search_functionality_basic(self):
        """Test basic search functionality"""
        response = self.client.get(reverse('search_results'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test App')

    def test_search_functionality_advanced(self):
        """Test advanced search with multiple criteria"""
        response = self.client.get(reverse('search_results'), {'q': 'Social'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Social Media App')

    def test_search_suggestions(self):
        """Test search suggestions API"""
        response = self.client.get(reverse('search_suggestions'), {'q': 'Tes'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('Test App', data)

    def test_search_suggestions_minimum_length(self):
        """Test search suggestions only work with 3+ characters"""
        response = self.client.get(reverse('search_suggestions'), {'q': 'Te'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])  # Should return empty for < 3 chars

    def test_app_detail_page(self):
        """Test app detail page loads correctly"""
        response = self.client.get(reverse('app_detail', args=[self.app.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test App')
        self.assertContains(response, 'Productivity')

    def test_user_review_submission_with_supervisor(self):
        """Test user with supervisor can submit review"""
        self.client.login(username='employee1', password='testpass123')
        
        response = self.client.post(reverse('app_detail', args=[self.app.id]), {
            'review_text': 'Great app! Really useful for productivity.',
            'rating': 5
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful submission
        
        # Check review was created
        review = UserReview.objects.filter(
            app=self.app,
            user=self.user1,
            status='pending'
        ).first()
        
        self.assertIsNotNone(review)
        self.assertEqual(review.review_text, 'Great app! Really useful for productivity.')
        self.assertEqual(review.rating, 5)

    def test_user_review_submission_without_supervisor(self):
        """Test user without supervisor cannot submit review"""
        self.client.login(username='orphan_user', password='testpass123')
        
        response = self.client.post(reverse('app_detail', args=[self.app.id]), {
            'review_text': 'Great app!',
            'rating': 5
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect with error
        
        # Check no review was created
        self.assertFalse(
            UserReview.objects.filter(
                app=self.app,
                user=self.user_no_supervisor
            ).exists()
        )

    def test_sentiment_analysis_functionality(self):
        """Test sentiment analysis on review submission"""
        self.client.login(username='employee1', password='testpass123')
        
        # Submit positive review
        response = self.client.post(reverse('app_detail', args=[self.app.id]), {
            'review_text': 'Amazing app! Love the interface and features.',
            'rating': 5
        })
        
        review = UserReview.objects.filter(user=self.user1).first()
        review.analyze_combined_sentiment()  # Manually trigger analysis for testing
        
        self.assertIsNotNone(review.sentiment)
        self.assertIsNotNone(review.sentiment_polarity)
        self.assertIsNotNone(review.confidence_score)

    def test_supervisor_dashboard_shows_only_assigned_reviews(self):
        """Test supervisor only sees reviews from their assigned users"""
        # Create reviews from different users
        review1 = UserReview.objects.create(
            app=self.app,
            user=self.user1,  # Supervised by supervisor1
            review_text='Review by user1',
            rating=4,
            status='pending'
        )
        
        review2 = UserReview.objects.create(
            app=self.app,
            user=self.user2,  # Supervised by supervisor2
            review_text='Review by user2',
            rating=3,
            status='pending'
        )
        
        # Login as supervisor1
        self.client.login(username='supervisor1', password='supervisor123')
        response = self.client.get(reverse('supervisor_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Review by user1')  # Should see this
        self.assertNotContains(response, 'Review by user2')  # Should NOT see this

    def test_supervisor_dashboard_access_control(self):
        """Test only supervisors can access supervisor dashboard"""
        # Test regular user cannot access
        self.client.login(username='employee1', password='testpass123')
        response = self.client.get(reverse('supervisor_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirected due to no access

    def test_review_approval_authorization(self):
        """Test supervisor can only approve reviews from their assigned users"""
        review = UserReview.objects.create(
            app=self.app,
            user=self.user1,  # Supervised by supervisor1
            review_text='Test review',
            rating=4,
            status='pending'
        )
        
        # Login as supervisor1 (correct supervisor)
        self.client.login(username='supervisor1', password='supervisor123')
        response = self.client.post(
            reverse('approve_review', args=[review.id]),
            {'action': 'approve'}
        )
        
        self.assertEqual(response.status_code, 302)  # Successful redirect
        review.refresh_from_db()
        self.assertEqual(review.status, 'approved')
        self.assertEqual(review.approved_by, self.supervisor1)

    def test_review_approval_unauthorized(self):
        """Test supervisor cannot approve reviews from other supervisors' users"""
        review = UserReview.objects.create(
            app=self.app,
            user=self.user1,  # Supervised by supervisor1
            review_text='Test review',
            rating=4,
            status='pending'
        )
        
        # Login as supervisor2 (wrong supervisor)
        self.client.login(username='supervisor2', password='supervisor123')
        response = self.client.post(
            reverse('approve_review', args=[review.id]),
            {'action': 'approve'}
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect due to no access
        review.refresh_from_db()
        self.assertEqual(review.status, 'pending')  # Status unchanged
        self.assertIsNone(review.approved_by)

    def test_review_rejection(self):
        """Test review rejection functionality"""
        review = UserReview.objects.create(
            app=self.app,
            user=self.user1,
            review_text='Test review',
            rating=4,
            status='pending'
        )
        
        self.client.login(username='supervisor1', password='supervisor123')
        response = self.client.post(
            reverse('approve_review', args=[review.id]),
            {'action': 'reject'}
        )
        
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.status, 'rejected')
        self.assertEqual(review.approved_by, self.supervisor1)

    def test_enhanced_sentiment_analysis(self):
        """Test enhanced sentiment analysis with text-rating correlation"""
        review = UserReview.objects.create(
            app=self.app,
            user=self.user1,
            review_text='This app is terrible and crashes constantly!',
            rating=1,  # Rating matches negative text
            status='pending'
        )
        
        review.analyze_combined_sentiment()
        
        # Should detect negative sentiment with high confidence
        self.assertEqual(review.sentiment, 'Negative')
        self.assertLess(review.sentiment_polarity, 0)  # Negative polarity
        self.assertGreater(review.confidence_score, 0.5)  # High confidence
        self.assertFalse(review.has_contradiction)  # Text and rating agree

    def test_sentiment_contradiction_detection(self):
        """Test detection of text-rating contradictions"""
        review = UserReview.objects.create(
            app=self.app,
            user=self.user1,
            review_text='Amazing app, works perfectly!',  # Positive text
            rating=1,  # Negative rating - contradiction!
            status='pending'
        )
        
        review.analyze_combined_sentiment()
        
        # Should detect contradiction
        self.assertTrue(review.has_contradiction)
        self.assertIsNotNone(review.text_sentiment_polarity)
        self.assertIsNotNone(review.rating_sentiment_polarity)

    def test_user_profile_supervisor_relationship(self):
        """Test UserProfile supervisor relationship methods"""
        profile1 = self.user1.userprofile
        profile_supervisor1 = self.supervisor1.userprofile
        
        # Test get_supervisor method
        self.assertEqual(profile1.get_supervisor(), self.supervisor1)
        
        # Test get_supervised_users method
        supervised_users = profile_supervisor1.get_supervised_users()
        self.assertIn(self.user1, supervised_users)
        self.assertNotIn(self.user2, supervised_users)

    def test_app_detail_shows_approved_reviews_only(self):
        """Test app detail page only shows approved reviews"""
        # Create reviews with different statuses
        UserReview.objects.create(
            app=self.app,
            user=self.user1,
            review_text='Approved review',
            rating=5,
            status='approved'
        )
        
        UserReview.objects.create(
            app=self.app,
            user=self.user2,
            review_text='Pending review',
            rating=4,
            status='pending'
        )
        
        UserReview.objects.create(
            app=self.app,
            user=self.user1,
            review_text='Rejected review',
            rating=3,
            status='rejected'
        )
        
        response = self.client.get(reverse('app_detail', args=[self.app.id]))
        
        self.assertContains(response, 'Approved review')
        self.assertNotContains(response, 'Pending review')
        self.assertNotContains(response, 'Rejected review')

    def test_confidence_score_calculation(self):
        """Test sentiment confidence score calculation"""
        review = UserReview.objects.create(
            app=self.app,
            user=self.user1,
            review_text='This app is absolutely fantastic!',
            rating=5,
            status='pending'
        )
        
        review.analyze_combined_sentiment()
        
        confidence = review.get_sentiment_confidence()
        self.assertIn(confidence, ['High', 'Medium', 'Low', 'Unknown'])

    def test_anonymous_user_cannot_submit_review(self):
        """Test anonymous users cannot submit reviews"""
        response = self.client.post(reverse('app_detail', args=[self.app.id]), {
            'review_text': 'Great app!',
            'rating': 5
        })
        
        # Should not create any review
        self.assertEqual(UserReview.objects.count(), 0)

    def test_search_empty_query(self):
        """Test search with empty query"""
        response = self.client.get(reverse('search_results'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        # Should handle empty query gracefully
    
    def test_text_similarity_engine(self):
        """Test the TextSimilarityEngine from utils"""
        from .utils import TextSimilarityEngine
        
        engine = TextSimilarityEngine()
        
        # Test documents
        documents = [
            "Photo editing application with filters",
            "Image manipulation software", 
            "Calculator for mathematical operations",
            "Social media networking app"
        ]
        
        # Test query
        query = "photo editor"
        
        # Calculate similarities
        similarities = engine.calculate_similarity(query, documents)
        
        # Verify results
        self.assertEqual(len(similarities), 4)
        self.assertIsInstance(similarities, list)
        
        # Photo editing should have highest similarity
        max_similarity_index = similarities.index(max(similarities))
        self.assertEqual(max_similarity_index, 0)  # First document should be most similar