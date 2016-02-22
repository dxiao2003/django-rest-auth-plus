from __future__ import unicode_literals

from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff or \
            (request.user.username ==
             view.get_parents_query_dict()[view.parent_fk])
