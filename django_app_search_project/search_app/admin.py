# search_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import App, AppReview, UserReview, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "supervisor":
            # Only show users who are supervisors in the dropdown
            kwargs["queryset"] = User.objects.filter(userprofile__is_supervisor=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs) 

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = UserAdmin.list_display + ('get_is_supervisor', 'get_supervisor')
    
    def get_is_supervisor(self, obj):
        try:
            return obj.userprofile.is_supervisor
        except UserProfile.DoesNotExist:
            return False
    get_is_supervisor.boolean = True
    get_is_supervisor.short_description = 'Is Supervisor'
    
    def get_supervisor(self, obj):
        try:
            return obj.userprofile.supervisor
        except UserProfile.DoesNotExist:
            return None
    get_supervisor.short_description = 'Supervisor'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'rating', 'reviews_count', 'installs', 'type']
    list_filter = ['category', 'type', 'content_rating']
    search_fields = ['name', 'category', 'genres']
    list_per_page = 25
    ordering = ['-rating']

@admin.register(AppReview)
class AppReviewAdmin(admin.ModelAdmin):
    list_display = ['app', 'sentiment', 'sentiment_polarity', 'sentiment_subjectivity']
    list_filter = ['sentiment']
    search_fields = ['app__name', 'translated_review']
    list_per_page = 25

@admin.register(UserReview)
class UserReviewAdmin(admin.ModelAdmin):
    list_display = ['app', 'user', 'get_user_supervisor', 'rating', 'status', 'created_at', 'approved_by']
    list_filter = ['status', 'rating', 'created_at']
    search_fields = ['app__name', 'user__username', 'review_text']
    list_per_page = 25
    readonly_fields = ['created_at']

    def get_user_supervisor(self, obj):
        try:
            return obj.user.userprofile.supervisor
        except UserProfile.DoesNotExist:
            return None
    get_user_supervisor.short_description = 'User\'s Supervisor'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('app', 'user', 'approved_by')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_supervisor', 'supervisor', 'get_supervised_count']
    list_filter = ['is_supervisor']
    search_fields = ['user__username', 'user__email', 'supervisor__username']
    raw_id_fields = ['supervisor']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "supervisor":
            kwargs["queryset"] = User.objects.filter(userprofile__is_supervisor=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_supervised_count(self, obj):
        """Show how many users this person supervises"""
        if obj.is_supervisor:
            return UserProfile.objects.filter(supervisor=obj.user).count()
        return 0
    get_supervised_count.short_description = 'Supervises'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'supervisor')