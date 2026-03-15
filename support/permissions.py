from rest_framework import permissions

class IsTicketOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of a ticket or admins to view/reply to it.
    """
    def has_object_permission(self, request, view, obj):
        # Admins can see all tickets
        if request.user.is_staff:
            return True
        
        # User can only see their own tickets
        return obj.user == request.user
