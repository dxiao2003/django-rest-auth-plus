from __future__ import unicode_literals

from collections import namedtuple
from random import randint

from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken, \
    SocialLogin
from django.conf.urls import patterns, url, include
from django.contrib.auth.models import User

from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.contrib.sites.shortcuts import get_current_site
from mock import patch, MagicMock
from rest_auth.registration.views import SocialLoginView
from rest_auth.serializers import UserDetailsSerializer
from rest_auth_plus.adapters import FacebookOAuth2Adapter
from rest_auth_plus.views import SocialAccountViewSet, UserSocialAccountViewSet
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.routers import SimpleRouter
from rest_framework.test import APITestCase, APIClient, APIRequestFactory, \
    force_authenticate
from rest_framework.viewsets import ModelViewSet
from rest_framework_extensions.routers import NestedRouterMixin
from rest_framework_extensions.settings import extensions_api_settings


class NestedSimpleRouter(NestedRouterMixin, SimpleRouter):
    pass

router = NestedSimpleRouter()
social_account_routes = router.register(r'social-account',
                                        SocialAccountViewSet,
                                        base_name='social-account')


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserDetailsSerializer

user_routes = router.register(r'user', UserViewSet, base_name='user')

user_social_account_routes = user_routes.register(
    r'social-account',
    UserSocialAccountViewSet,
    base_name='user-social-account',
    parents_query_lookups=[UserSocialAccountViewSet.parent_fk]
)

urlpatterns = patterns('', url(r'^', include(router.urls)))

user_social_accounts_parent_fk = \
    extensions_api_settings.DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX + \
    UserSocialAccountViewSet.parent_fk


def social_account_test(account, a):
    return account.provider == a["provider"] and \
        account.uid == a["uid"] and (account.provider != 'google' or
            (account.socialtoken_set.first().token ==
                                     a["social_token_set"][0]["token"] and
             account.socialtoken_set.first().account.uid == a["uid"]))


class FacebookLoginView(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class FacebookAdapterTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            "test user " + str(randint(1, 100000000))
        )
        self.app = SocialApp.objects.create(provider='facebook',
                                            name='test app',
                                            client_id='client_id',
                                            secret='secret')

    @patch("requests.get")
    @patch("allauth.socialaccount.providers.facebook.views.fb_complete_login")
    def test_create(self, fb_mock, get_mock):
        user = User(username="username")
        login = SocialLogin(user=user, account=SocialAccount())
        login.state["next"] = "/"
        fb_mock.return_value = login
        ret_mock = MagicMock()
        ret_mock.json.return_value = { "access_token": "OK" }
        get_mock.return_value = ret_mock
        factory = APIRequestFactory()
        request = factory.post(
            "/",
            { "access_token": "1234" },
            format="json"
        )
        request.session = SessionStore()
        self.app.sites.add(get_current_site(request))
        response = FacebookLoginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        code = response.data["key"]
        user = Token.objects.get(key=code).user
        self.assertIsNotNone(user.socialaccount_set.first())
        self.assertEqual(
            user.socialaccount_set.first().socialtoken_set.first().token,
            "OK"
        )

    @patch("requests.get")
    @patch("allauth.socialaccount.providers.facebook.views.fb_complete_login")
    def test_process_connect(self, fb_mock, get_mock):
        fb_mock.return_value = SocialLogin(account=SocialAccount())
        ret_mock = MagicMock()
        ret_mock.json.return_value = { "access_token": "OK" }
        get_mock.return_value = ret_mock
        factory = APIRequestFactory()
        request = factory.post(
            "/?process=connect",
            { "access_token": "1234" },
            format="json"
        )
        self.app.sites.add(get_current_site(request))
        force_authenticate(request, self.user)
        response = FacebookLoginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(self.user.socialaccount_set.first())
        self.assertEqual(
            self.user.socialaccount_set.first().socialtoken_set.first().token,
            "OK"
        )

class SocialAccountTestCase(APITestCase):
    urls = 'tests.test_views'

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            "test user " + str(randint(1, 100000000))
        )
        self.user_2 = User.objects.create_user(
            "test user " + str(randint(1, 100000000))
        )
        for i in range(1, 10):
            SocialAccount.objects.create(user=self.user,
                                         provider='facebook',
                                         uid=str(randint(1, 100000000000)))

        self.account2 = SocialAccount.objects.create(
            user=self.user_2,
            provider='google',
            uid=str(randint(1, 100000000000))
        )
        self.app = SocialApp.objects.create(provider='google',
                                            name='test app',
                                            client_id='client_id',
                                            secret='secret')
        self.token = SocialToken.objects.create(app=self.app,
                                                account=self.account2,
                                                token="skldfjslf")

    def list_social_accounts(self):
        return self.client.get(reverse('social-account-list'))

    def list_user_social_accounts(self, username):
        return self.client.get(
            reverse('user-social-account-list',
                    kwargs={user_social_accounts_parent_fk: username})
        )

    def destroy_social_account(self, social_account_id):
        return self.client.delete(reverse('social-account-detail',
                                          kwargs={'pk': social_account_id}))

    def destroy_user_social_account(self, username, social_account_id):
        return self.client.delete(
            reverse('user-social-account-detail',
                    kwargs={
                        user_social_accounts_parent_fk: username,
                        'pk': social_account_id})
        )

    def assertSocialAccounts(self, accounts_data, accounts_queryset):
        self.assertEqual(len(accounts_data), accounts_queryset.count())
        for account in accounts_queryset.all():
            any(social_account_test(account, a) for a in accounts_data)

    def test_list_social_accounts_anon(self):
        response = self.list_social_accounts()
        self.assertEqual(response.status_code, 401)

    def test_list_social_accounts_unauthorized(self):
        self.client.force_authenticate(self.user)
        response = self.list_social_accounts()
        self.assertEqual(response.status_code, 403)

    def test_list_social_accounts_staff(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.list_social_accounts()
        self.assertEqual(response.status_code, 200)
        self.assertSocialAccounts(response.data, SocialAccount.objects.all())

    def test_list_user_social_accounts_anon(self):
        response = self.list_user_social_accounts(self.user.username)
        self.assertEqual(response.status_code, 401)

    def test_list_user_social_accounts_unauthorized(self):
        self.client.force_authenticate(self.user_2)
        response = self.list_user_social_accounts(self.user.username)
        self.assertEqual(response.status_code, 403)

    def test_list_user_social_accounts_authorized(self):
        self.client.force_authenticate(self.user)
        response = self.list_user_social_accounts(self.user.username)
        self.assertEqual(response.status_code, 200)
        self.assertSocialAccounts(response.data,
                                  SocialAccount.objects.filter(user=self.user))

    def test_disconnect_social_account_anon(self):
        social_account = self.user.socialaccount_set.first()
        response = self.destroy_social_account(social_account.id)
        self.assertEqual(response.status_code, 401)

    def test_disconnect_social_account_unauthorized(self):
        social_account = self.user.socialaccount_set.first()
        self.client.force_authenticate(self.user)
        response = self.destroy_social_account(social_account.id)
        self.assertEqual(response.status_code, 403)

    def test_disconnect_social_account_staff(self):
        social_account = self.user.socialaccount_set.first()
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.destroy_social_account(social_account.id)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            SocialAccount.objects.filter(pk=social_account.id).exists()
        )

    def test_disconnect_social_account_staff_invalid(self):
        social_account = self.user_2.socialaccount_set.first()
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.destroy_social_account(social_account.id)
        self.assertEqual(response.status_code, 400)

    def test_disconnect_user_social_account_anon(self):
        social_account = self.user.socialaccount_set.first()
        response = self.destroy_user_social_account(self.user.username,
                                                    social_account.id)
        self.assertEqual(response.status_code, 401)

    def test_disconnect_user_social_account_unauthorized(self):
        social_account = self.user.socialaccount_set.first()
        self.client.force_authenticate(self.user_2)
        response = self.destroy_user_social_account(self.user.username,
                                                    social_account.id)
        self.assertEqual(response.status_code, 403)

    def test_disconnect_user_social_account_staff(self):
        social_account = self.user.socialaccount_set.first()
        self.user_2.is_staff = True
        self.user_2.save()
        self.client.force_authenticate(self.user_2)
        response = self.destroy_user_social_account(self.user.username,
                                                    social_account.id)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            SocialAccount.objects.filter(pk=social_account.id).exists()
        )

    def test_disconnect_user_social_account_authorized(self):
        social_account = self.user.socialaccount_set.first()
        self.client.force_authenticate(self.user)
        response = self.destroy_user_social_account(self.user.username,
                                                    social_account.id)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            SocialAccount.objects.filter(pk=social_account.id).exists()
        )

    def test_disconnect_user_social_account_staff_invalid(self):
        social_account = self.user_2.socialaccount_set.first()
        self.client.force_authenticate(self.user_2)
        response = self.destroy_user_social_account(self.user_2.username,
                                                    social_account.id)
        self.assertEqual(response.status_code, 400)
