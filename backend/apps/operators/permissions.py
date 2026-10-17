from rest_framework.permissions import BasePermission
from .models import OperatorMembership

class IsOperatorMember(BasePermission):
    """Check if the currently authnticated user has an
    Active mebership"""

    def has_object_permission(self, request, view, obj) -> bool:
        # If user is platform  admin
        if request.user and request.user.is_superuser:
            return True

        # Check if an active membership exist for this user and this operator

        return OperatorMembership.objects.filter(
            user=request.user,
            operator=obj,
            status=OperatorMembership.Status.ACTIVE,
        ).exists()

        
       