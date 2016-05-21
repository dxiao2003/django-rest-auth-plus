from __future__ import unicode_literals

# view all social accounts for a specific user
from allauth.socialaccount import signals
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import ValidationError

from rest_auth_plus.permissions import IsOwner
from rest_auth_plus.serializers import SocialAccountSerializer
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.exceptions import ValidationError as RestValidationError


class SocialAccountViewSet(ListAPIView, GenericViewSet):
    queryset = SocialAccount.objects.all()
    serializer_class = SocialAccountSerializer
    permission_classes = (IsAdminUser,)

    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        try:
            get_adapter().validate_disconnect(
                account,
                SocialAccount.objects.filter(user_id=account.user_id)
            )
        except ValidationError as e:
            raise RestValidationError(str(e))

        account.delete()
        signals.social_account_removed.send(sender=SocialAccount,
                                            request=self.request,
                                            socialaccount=account)
        return Response({'result': 'OK'})


class UserSocialAccountViewSet(NestedViewSetMixin, SocialAccountViewSet):
    parent_fk = "user__username"
    permission_classes = (IsAuthenticated, IsOwner)
