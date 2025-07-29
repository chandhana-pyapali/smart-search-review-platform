from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.models import User 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np

from .models import App, AppReview, UserReview, UserProfile
from .forms import CustomUserCreationForm, UserReviewForm

def home(request):
    return render(request, 'search_app/home.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    if len(query) >= 3:
        apps = App.objects.filter(
            name__icontains=query
        ).values_list('name', flat=True)[:10]
        return JsonResponse(list(apps), safe=False)
    return JsonResponse([], safe=False)

def search_results(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        # Simple text-based search (you can enhance this with TF-IDF)
        results = App.objects.filter(
            Q(name__icontains=query) | 
            Q(category__icontains=query) |
            Q(genres__icontains=query)
        ).order_by('-rating')
        
        # Implement text similarity using TF-IDF
        if results.exists():
            results = enhance_search_with_similarity(query, results)
    
    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'search_app/search_results.html', {
        'page_obj': page_obj,
        'query': query
    })

def enhance_search_with_similarity(query, queryset):
    # Convert queryset to list for similarity calculation
    apps_list = list(queryset)
    if not apps_list:
        return apps_list
    
    # Create text corpus for similarity calculation
    app_texts = [f"{app.name} {app.category} {app.genres or ''}" for app in apps_list]
    app_texts.append(query)
    
    # Calculate TF-IDF similarity
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
    tfidf_matrix = vectorizer.fit_transform(app_texts)
    
    # Calculate cosine similarity between query and each app
    query_vector = tfidf_matrix[-1]
    similarities = cosine_similarity(query_vector, tfidf_matrix[:-1]).flatten()
    
    # Sort apps by similarity score
    app_similarity_pairs = list(zip(apps_list, similarities))
    app_similarity_pairs.sort(key=lambda x: x[1], reverse=True)
    
    return [app for app, _ in app_similarity_pairs]

def app_detail(request, app_id):
    app = get_object_or_404(App, id=app_id)
    
    # Get existing reviews from CSV data
    csv_reviews = AppReview.objects.filter(app=app)
    
    # Get approved user reviews
    user_reviews = UserReview.objects.filter(app=app, status='approved').order_by('-created_at')
    
    # Check if user has supervisor (for review permission)
    user_has_supervisor = False
    user_supervisor = None
    supervisor_display_name = None

    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            user_supervisor = profile.supervisor
            user_has_supervisor = user_supervisor is not None
            if user_supervisor:
                supervisor_display_name = user_supervisor.get_full_name() or user_supervisor.username
        except UserProfile.DoesNotExist:
            user_has_supervisor = False

    # Handle review submission
    if request.method == 'POST' and request.user.is_authenticated:
        # CHECK: User must have supervisor to submit review
        if not user_has_supervisor:
            messages.error(request, 
                'You cannot submit reviews because no supervisor is assigned to your account. '
                'Please contact your administrator to assign a supervisor.'
            )
            return redirect('app_detail', app_id=app.id)
        
        form = UserReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.app = app
            review.user = request.user
            review.save()
            review.analyze_combined_sentiment()
            messages.success(request, f'Your review has been submitted for approval to {supervisor_display_name}!')
            return redirect('app_detail', app_id=app.id)
    else:
        form = UserReviewForm()
    
    return render(request, 'search_app/app_detail.html', {
        'app': app,
        'csv_reviews': csv_reviews,
        'user_reviews': user_reviews,
        'form': form,
        'user_has_supervisor': user_has_supervisor,
        'user_supervisor': user_supervisor,
        'supervisor_display_name': supervisor_display_name
    })

@login_required
def supervisor_dashboard(request):
    try:
        profile = request.user.userprofile
        if not profile.is_supervisor:
            messages.error(request, 'Access denied. Supervisor privileges required.')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('home')
    
    supervised_users = User.objects.filter(userprofile__supervisor=request.user)
    pending_reviews = UserReview.objects.filter(user__in=supervised_users, status='pending').order_by('-created_at')
    
    return render(request, 'search_app/supervisor_dashboard.html', {
        'pending_reviews': pending_reviews,
        'supervised_users_count': supervised_users.count()
    })

@login_required
def approve_review(request, review_id):
    try:
        profile = request.user.userprofile
        if not profile.is_supervisor:
            messages.error(request, 'Access denied.')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('home')
    
    review = get_object_or_404(UserReview, id=review_id)
    try:
        review_author_supervisor = review.user.userprofile.supervisor
        if review_author_supervisor != request.user:
            messages.error(request, 'You are not authorized to approve this review.')
            return redirect('supervisor_dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Review author profile not found.')
        return redirect('supervisor_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            review.status = 'approved'
            review.approved_by = request.user
            review.approved_at = timezone.now()
            review.save()
            sentiment_context = ""
            if review.sentiment:
                sentiment_context = f" (AI detected: {review.sentiment} sentiment)"
            messages.success(request, f'Review approved successfully!{sentiment_context}')
        elif action == 'reject':
            review.status = 'rejected'
            review.approved_by = request.user
            review.approved_at = timezone.now()
            review.save()
            sentiment_context = ""
            if review.sentiment:
                sentiment_context = f" (AI detected: {review.sentiment} sentiment)"
            messages.success(request, f'Review rejected successfully!{sentiment_context}')
    
    return redirect('supervisor_dashboard')