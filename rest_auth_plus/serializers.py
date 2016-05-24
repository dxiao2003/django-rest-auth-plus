from __future__ import unicode_literals

from allauth.socialaccount.models import SocialAccount, SocialToken
from rest_framework.serializers import ModelSerializer


class SocialTokenSerializer(ModelSerializer):

    class Meta:
        model = SocialToken
        fields = ("app", "account", "token", "token_secret", "expires_at")


class SocialAccountSerializer(ModelSerializer):

    social_token_set = SocialTokenSerializer(source="socialtoken_set",
                                             many=True)

    class Meta:
        model = SocialAccount
        fields = ("user", "provider", "uid", "last_login", "date_joined",
                  "extra_data", "social_token_set")
