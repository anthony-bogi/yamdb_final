from rest_framework import permissions


class IsAdminOrSuperuserPermission(permissions.BasePermission):
    """Разрешение доступа только для Администратора и Суперпользователя."""
    message = 'Админ зона! У Вас нет разрешения для дальнейшей работы!'

    def has_permission(self, request, view):
        if request.user.role == 'admin' or request.user.is_superuser:
            return True
        return False


class IsModeratorPermission(permissions.BasePermission):
    """Доступ разрешен только для Модератора."""
    message = 'Зона Модератора! У Вас нет разрешения для дальнейшей работы!'

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role == 'moderator':
            return True
        return False


class TitlePermission(permissions.BasePermission):
    """
    Предоставление прав на добавление и
     удаление категорий, жанров и произведений.
    """
    message = 'У Вас нет разрешения для дальнейшей работы!'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'admin' or request.user.is_superuser:
            return True
        return False


class IsAdminModeratorOwnerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.role == 'admin'
                or request.user.role == 'moderator'
                or obj.author == request.user)
