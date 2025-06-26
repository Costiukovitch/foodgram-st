from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, Subscription


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ-панель для пользователей."""
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    list_display = ('id', 'email', 'username', 'first_name', 'last_name', 'is_staff')
    list_display_links = ('email', 'username')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('id',)
    readonly_fields = ('last_login', 'date_joined')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для подписок."""
    list_display = ('id', 'author_username', 'subscriber_username')
    search_fields = ('author__username', 'subscriber__username')
    list_select_related = ('author', 'subscriber')

    @admin.display(description='Автор')
    def author_username(self, obj):
        return obj.author.username

    @admin.display(description='Подписчик')
    def subscriber_username(self, obj):
        return obj.subscriber.username
        