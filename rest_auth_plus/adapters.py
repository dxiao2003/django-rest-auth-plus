from __future__ import unicode_literals, absolute_import

from allauth.socialaccount import providers
from allauth.socialaccount.providers.facebook.views import \
    FacebookOAuth2Adapter as BaseFacebookOAuth2Adapter
from allauth.socialaccount.providers.facebook.provider import FacebookProvider, \
    GRAPH_API_URL
import requests


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
            token.token = resp['access_token']
        return super(FacebookOAuth2Adapter, self).complete_login(
            request, app, token
        )