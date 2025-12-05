from rest_framework.permissions import BasePermission

class IsAdminUserCustom(BasePermission):
    """
    Allows only admin (is_staff=True) users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
