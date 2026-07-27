from massive import RESTClient

class MassiveClient:

    def __init__(self, api_key: str):
        self.client = RESTClient(api_key)

    @property
    def rest(self):
        return self.client
