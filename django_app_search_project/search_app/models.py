from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from textblob import TextBlob

class App(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=100)
    rating = models.FloatField(null=True, blank=True)
    reviews_count = models.IntegerField(default=0)
    size = models.CharField(max_length=50, null=True, blank=True)
    installs = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=20, null=True, blank=True)
    price = models.CharField(max_length=20, null=True, blank=True)
    content_rating = models.CharField(max_length=50, null=True, blank=True)
    genres = models.CharField(max_length=200, null=True, blank=True)
    last_updated = models.CharField(max_length=50, null=True, blank=True)
    current_version = models.CharField(max_length=50, null=True, blank=True)
    android_version = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'apps'
        
    def __str__(self):
        return self.name

class AppReview(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='app_reviews')
    translated_review = models.TextField()
    sentiment = models.CharField(max_length=20)
    sentiment_polarity = models.FloatField(null=True, blank=True)
    sentiment_subjectivity = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'app_reviews'
        
    def __str__(self):
        return f"{self.app.name} - {self.sentiment}"

class UserReview(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='user_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review_text = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reviews'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    sentiment = models.CharField(max_length=20, null=True, blank=True)
    sentiment_polarity = models.FloatField(null=True, blank=True)
    sentiment_subjectivity = models.FloatField(null=True, blank=True)

    confidence_score = models.FloatField(null=True, blank=True)
    has_contradiction = models.BooleanField(default=False)
    text_sentiment_polarity = models.FloatField(null=True, blank=True)  # Store original text sentiment
    rating_sentiment_polarity = models.FloatField(null=True, blank=True)  # Store rating sentiment
    
    class Meta:
        db_table = 'user_reviews'
        
    def __str__(self):
        return f"{self.app.name} - {self.user.username} - {self.status}"
    
    def get_designated_supervisor(self):
        """Get the supervisor who should approve this review"""
        try:
            return self.user.userprofile.supervisor
        except UserProfile.DoesNotExist:
            return None
    
    def is_supervisor_authorized(self, supervisor_user):
        """Check if a supervisor is authorized to approve this review"""
        designated_supervisor = self.get_designated_supervisor()
        return designated_supervisor == supervisor_user
    
    def analyze_combined_sentiment(self):
        """Enhanced sentiment analysis using both text and rating"""
        if self.review_text and self.rating:
            # Step 1: Analyze text sentiment
            blob = TextBlob(self.review_text)
            text_polarity = blob.sentiment.polarity  # -1 to +1
            text_subjectivity = blob.sentiment.subjectivity
            
            # Step 2: Convert rating to sentiment scale
            # Rating 1-5 → Polarity -1 to +1
            rating_polarity = (self.rating - 3) / 2  # 1→-1, 3→0, 5→+1
            
            # Step 3: Calculate weighted combination
            # Give more weight to rating if text is very short or neutral
            text_weight = min(len(self.review_text.split()) / 10, 0.7)  # Max 70% weight to text
            rating_weight = 1 - text_weight
            
            combined_polarity = (text_polarity * text_weight) + (rating_polarity * rating_weight)
            
            # Step 4: Detect contradictions
            contradiction_threshold = 0.8
            if abs(text_polarity - rating_polarity) > contradiction_threshold:
                self.has_contradiction = True
                # Lower confidence for contradictory reviews
                confidence_penalty = 0.3
            else:
                self.has_contradiction = False
                confidence_penalty = 0
            
            # Step 5: Classify final sentiment
            if combined_polarity > 0.1:
                sentiment = 'Positive'
            elif combined_polarity < -0.1:
                sentiment = 'Negative'
            else:
                sentiment = 'Neutral'
            
            # Step 6: Calculate confidence
            base_confidence = abs(combined_polarity)
            final_confidence = max(0, base_confidence - confidence_penalty)
            
            # Update fields
            self.sentiment = sentiment
            self.sentiment_polarity = combined_polarity
            self.sentiment_subjectivity = text_subjectivity
            self.confidence_score = final_confidence
            self.text_sentiment_polarity = text_polarity
            self.rating_sentiment_polarity = rating_polarity
            self.save()
    
    def get_sentiment_confidence(self):
        """Enhanced confidence calculation"""
        if hasattr(self, 'confidence_score') and self.confidence_score is not None:
            if self.confidence_score > 0.7:
                return 'High'
            elif self.confidence_score > 0.4:
                return 'Medium'
            else:
                return 'Low'
        return 'Unknown'
    
    def has_text_rating_mismatch(self):
        """Detect if text sentiment and rating don't match"""
        return self.has_contradiction

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_supervisor = models.BooleanField(default=False)

    supervisor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='supervised_users',
        limit_choices_to={'userprofile__is_supervisor': True},
        help_text="The supervisor who can approve this user's reviews"
    )
    
    def __str__(self):
        return f"{self.user.username} - {'Supervisor' if self.is_supervisor else 'User'}"
    
    def get_supervisor(self):
        """Get this user's assigned supervisor"""
        return self.supervisor
    
    def get_supervised_users(self):
        """Get all users this person supervises (if they're a supervisor)"""
        if self.is_supervisor:
            return User.objects.filter(userprofile__supervisor=self.user)
        return User.objects.none()
