from __future__ import unicode_literals

from allauth.socialaccount.models import SocialAccount
from rest_framework.serializers import ModelSerializer


class SocialAccountSerializer(ModelSerializer):
    class Meta:
        model = SocialAccount
