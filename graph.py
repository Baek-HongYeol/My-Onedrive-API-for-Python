from configparser import SectionProxy
from azure.identity import DeviceCodeCredential, TokenCachePersistenceOptions
from azure.identity import AuthenticationRecord
from msgraph import GraphServiceClient

import requests
import os
import atexit, msal

class Graph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        self.client_id = self.settings['clientId']
        self.tenant_id = self.settings['tenantId']
        self.graph_scopes = self.settings['graphUserScopes'].split(' ')
        self.expires_on = ''
        self.last_updated = ''
        self.device_code_credential = None
        cache = msal.SerializableTokenCache()
        if os.path.exists("my_token_cache.bin"):
            cache.deserialize(open("my_token_cache.bin", "r").read())
        atexit.register(lambda:
            open("my_token_cache.bin", "w").write(cache.serialize())
            # Hint: The following optional line persists only when state changed
            if cache.has_state_changed else None
            )
        if self.device_code_credential == None:
            self.device_code_credential = DeviceCodeCredential(self.client_id, tenant_id = self.tenant_id,_cache=cache, cache_persistence_options=TokenCachePersistenceOptions(allow_unencrypted_storage=True))
        self.user_client = GraphServiceClient(self.device_code_credential, self.graph_scopes)

    async def get_user_token(self):
        graph_scopes = self.settings['graphUserScopes']
        access_token = self.device_code_credential.get_token(graph_scopes)
        self.save_token_cache()
        return access_token.token

    def load_token_cache(self):
        cache = msal.SerializableTokenCache()
        if os.path.exists("my_token_cache.bin"):
            cache.deserialize(open("my_token_cache.bin", "r").read())
        atexit.register(lambda:
            open("my_token_cache.bin", "w").write(cache.serialize())
            # Hint: The following optional line persists only when state changed
            if cache.has_state_changed else None
            )
        self.device_code_credential = DeviceCodeCredential(
            _cache=cache,
            cache_persistence_options=TokenCachePersistenceOptions(allow_unencrypted_storage=True)
        )

    
    def save_token_cache(self):
        with open("my_token_cache.bin", "w") as f:
            f.write(self.device_code_credential._cache.serialize())

    
    async def make_graph_call(self, uri, filter=None):
        URL = 'https://graph.microsoft.com/v1.0/'
        HEADERS = {'Authorization': 'Bearer ' + await self.get_user_token()}
        print(f"send request: {uri}")
        res = requests.get(URL + 'me/drive/root:/' + uri + filter, headers=HEADERS)
        if(res.status_code == 401 or res.status_code == 403):
            self.get_user_token()
            return self.make_graph_call(uri, filter)
        elif res.status_code == 404 or res.status_code == 410:
            raise FileNotFoundError(uri)
        elif res.status_code != 200:
            raise NotImplementedError(f"Error code : {res.status_code}, error: {res.text}")
        items = res.json()
        print(items)
        return items