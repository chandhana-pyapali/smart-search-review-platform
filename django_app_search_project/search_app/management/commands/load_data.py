import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from search_app.models import App, AppReview

class Command(BaseCommand):
    help = 'Load data from CSV files'
    
    def handle(self, *args, **options):
        # Load apps data
        apps_file = os.path.join(settings.BASE_DIR, 'data', 'googleplaystore.csv')
        reviews_file = os.path.join(settings.BASE_DIR, 'data', 'googleplaystore_user_reviews.csv')
        
        self.stdout.write('Loading apps data...')
        apps_df = pd.read_csv(apps_file)
        
        for _, row in apps_df.iterrows():
            app, created = App.objects.get_or_create(
                name=row['App'],
                defaults={
                    'category': row.get('Category', ''),
                    'rating': pd.to_numeric(row.get('Rating'), errors='coerce'),
                    'reviews_count': pd.to_numeric(row.get('Reviews'), errors='coerce') or 0,
                    'size': row.get('Size', ''),
                    'installs': row.get('Installs', ''),
                    'type': row.get('Type', ''),
                    'price': row.get('Price', ''),
                    'content_rating': row.get('Content Rating', ''),
                    'genres': row.get('Genres', ''),
                    'last_updated': row.get('Last Updated', ''),
                    'current_version': row.get('Current Ver', ''),
                    'android_version': row.get('Android Ver', ''),
                }
            )
        
        self.stdout.write('Loading reviews data...')
        reviews_df = pd.read_csv(reviews_file)
        
        for _, row in reviews_df.iterrows():
            try:
                app = App.objects.get(name=row['App'])
                polarity = pd.to_numeric(row.get('Sentiment_Polarity'), errors='coerce')
                subjectivity = pd.to_numeric(row.get('Sentiment_Subjectivity'), errors='coerce')
                AppReview.objects.get_or_create(
                    app=app,
                    translated_review=row.get('Translated_Review', ''),
                    defaults={
                        'sentiment': row.get('Sentiment', ''),
                        'sentiment_polarity': None if pd.isnull(polarity) else polarity,
                        'sentiment_subjectivity': None if pd.isnull(subjectivity) else subjectivity,
                    }
                )
            except App.DoesNotExist:
                continue
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded data from CSV files')
        )