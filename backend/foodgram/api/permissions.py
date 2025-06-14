from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Проверка авторства пользователя."""

    message = 'У вас недостаточно прав для редактирования.'

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated
                and request.user == obj.author)
        )
