import logging
import os

import requests

logger = logging.getLogger(__name__)


class HttpRequest:
    """Class for making http requests"""

    def __init__(
        self,
        api_base: str,
        jwt_token: str = None,
    ):
        """Initializes the HttpRequest class"""
        requests.adapters.DEFAULT_RETRIES = 5
        self.api_base = api_base
        self.session = requests.Session()
        headers = {"Content-Type": "application/json"}
        if jwt_token:
            headers.update({"Authorization": f"Bearer {jwt_token}"})
        self.session.headers.update(headers)

        _no_proxy = os.getenv("NO_PROXY", "")
        if self.api_base not in _no_proxy:
            os.environ["NO_PROXY"] = ",".join([_no_proxy, self.api_base])

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: dict = None,
    ):
        url = "".join([self.api_base, endpoint])
        resp = self.session.request(method=method, url=url, json=payload)
        logger.debug("Payload %s", payload)
        return resp.json()

    def get(self, endpoint: str, payload: dict = None):
        return self._request("get", endpoint, payload)

    def post(self, endpoint: str, payload: dict = None):
        return self._request("post", endpoint, payload)
