from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Позволяет редактировать объект только его автору.
    Для остальных — доступ только на чтение.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только администраторам.
    Для других — только чтение.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Позволяет доступ только владельцу объекта или администратору.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Позволяет аутентифицированным пользователям выполнять любые действия.
    Неаутентифицированным — только чтение.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and request.user.is_authenticated
        