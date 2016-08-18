from __future__ import unicode_literals, absolute_import

from django.utils.translation import ugettext as _
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount import signals
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.facebook.views import \
    FacebookOAuth2Adapter as BaseFacebookOAuth2Adapter
from allauth.socialaccount.providers.facebook.provider import \
    FacebookProvider, GRAPH_API_URL
import requests

import allauth.socialaccount.helpers
from rest_framework.exceptions import ValidationError


def _add_social_account(request, sociallogin):
    if request.user.is_anonymous():
        # This should not happen. Simply redirect to the connections
        # view (which has a login required)
        raise ValidationError("Cannot link to anonymous account")

    if sociallogin.is_existing:
        if sociallogin.user != request.user:
            # Social account of other user. For now, this scenario
            # is not supported. Issue is that one cannot simply
            # remove the social account from the other user, as
            # that may render the account unusable.
            raise ValidationError("Already linked; to change, first unlink")
        else:
            # This account is already connected -- let's play along
            # and render the standard "account connected" message
            # without actually doing anything.
            pass
    else:
        # New account, let's connect
        sociallogin.connect(request, request.user)
        try:
            signals.social_account_added.send(sender=SocialLogin,
                                              request=request,
                                              sociallogin=sociallogin)
        except ImmediateHttpResponse as e:
            raise ValidationError(e.response.content)

# monkey patch this to remove all the HTTP redirects
# note that this means you can't use the HTML forms in the same server
allauth.socialaccount.helpers._add_social_account = _add_social_account


def get_request_params(request, name, default=None):
    return request.GET.get(name) or request.POST.get(name) or default


class FacebookOAuth2Adapter(BaseFacebookOAuth2Adapter):

    def complete_login(self, request, app, token, **kwargs):

        provider = providers.registry.by_id(FacebookProvider.id)
        if provider.get_settings().get('EXCHANGE_TOKEN'):
            resp = requests.get(
                GRAPH_API_URL + '/oauth/access_token',
                params={'grant_type': 'fb_exchange_token',
                        'client_id': app.client_id,
                        'client_secret': app.secret,
                        'fb_exchange_token': token.token}).json()

            if "access_token" not in resp:
                raise ValidationError(_("Invalid access token"))
            else:
                token.token = resp['access_token']

        login = super(FacebookOAuth2Adapter, self).complete_login(
            request, app, token
        )

        process = get_request_params(request, "process")

        if process:
            login.state["process"] = process

        return logi