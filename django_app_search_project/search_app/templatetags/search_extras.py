from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def stars_range(rating):
    """Convert rating to range for template iteration"""
    try:
        return range(int(float(rating)))
    except (ValueError, TypeError):
        return range(0)

@register.filter
def empty_stars_range(rating):
    """Get range for empty stars"""
    try:
        filled = int(float(rating))
        return range(5 - filled)
    except (ValueError, TypeError):
        return range(5)

@register.simple_tag
def render_stars(rating, size=''):
    """Render star rating HTML"""
    try:
        rating_int = int(float(rating))
        size_class = f'fa-{size}' if size else ''
        
        stars_html = ''
        for i in range(1, 6):
            if i <= rating_int:
                stars_html += f'<i class="fas fa-star {size_class}"></i>'
            else:
                stars_html += f'<i class="far fa-star {size_class}"></i>'
        
        return mark_safe(stars_html)
    except (ValueError, TypeError):
        return mark_safe('<i class="fas fa-question-circle"></i>')

@register.filter
def sentiment_class(sentiment):
    """Get CSS class for sentiment"""
    sentiment_lower = str(sentiment).lower()
    if 'positive' in sentiment_lower:
        return 'sentiment-positive'
    elif 'negative' in sentiment_lower:
        return 'sentiment-negative'
    else:
        return 'sentiment-neutral'

@register.filter
def sentiment_badge_class(sentiment):
    """Get Bootstrap badge class for sentiment"""
    sentiment_lower = str(sentiment).lower()
    if 'positive' in sentiment_lower:
        return 'bg-success'
    elif 'negative' in sentiment_lower:
        return 'bg-danger'
    else:
        return 'bg-secondary'

@register.filter
def confidence_badge_class(confidence):
    """Get Bootstrap badge class for confidence level"""
    confidence_lower = str(confidence).lower()
    if 'high' in confidence_lower:
        return 'bg-success'      # Green for high confidence
    elif 'medium' in confidence_lower:
        return 'bg-warning'      # Yellow/Orange for medium confidence  
    elif 'low' in confidence_lower:
        return 'bg-danger'       # Red for low confidence
    else:
        return 'bg-secondary'    # Gray for unknown