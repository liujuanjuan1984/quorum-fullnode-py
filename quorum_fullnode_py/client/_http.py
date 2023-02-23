import logging

import requests

logger = logging.getLogger(__name__)


class HttpRequest:
    def __init__(
        self,
        api_base: str,
        jwt_token: str = None,
    ):

        requests.adapters.DEFAULT_RETRIES = 5
        self.api_base = api_base
        self._session = requests.Session()
        self.headers = {
            "USER-AGENT": "quorum_fullnode_py.http_request",
            "Content-Type": "application/json",
        }
        if jwt_token:
            self.headers.update({"Authorization": f"Bearer {jwt_token}"})

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: dict = None,
    ):
        url = "".join([self.api_base, endpoint])
        resp = self._session.request(
            method=method, url=url, json=payload, headers=self.headers
        )

        logger.debug(
            "method: %s, resp.status_code: %s, url: %s\njson: %s\nresp: %s",
            method,
            resp.status_code,
            url,
            payload,
            resp,
        )

        return resp.json()

    def get(self, endpoint: str, payload: dict = None):
        return self._request("get", endpoint, payload)

    def post(self, endpoint: str, payload: dict = None):
        return self._request("post", endpoint, payload)
