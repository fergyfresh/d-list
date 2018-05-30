import json

from rauth import OAuth1Service, OAuth2Service
from flask import current_app, url_for, request, redirect, session


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True, _scheme='https')

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class AmazonSignIn(OAuthSignIn):
    def __init__(self):
        super(AmazonSignIn, self).__init__('amazon')
        self.service = OAuth2Service(
            name='amazon',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://www.amazon.com/ap/oa',
            access_token_url='https://api.amazon.com/auth/o2/token',
            base_url='https://www.amazon.com/'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='profile',
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        def decode_json(payload):
            return json.loads(payload)

        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()},
            decoder=decode_json
        )
        oauth_session_res = decode_json(oauth_session.access_token_response.content)
        params = {"access_token": oauth_session_res['access_token'] }
        me = oauth_session.request(method="get", url="ap/user/profile", params=params).json()
        return (
            'amazon$' + me['Profile']['CustomerId'],
            me['Profile']['Name'],
            me['Profile']['PrimaryEmail']
        )

