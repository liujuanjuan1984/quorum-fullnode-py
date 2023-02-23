import logging

from quorum_fullnode_py.api import FullNodeAPI
from quorum_fullnode_py.client._http import HttpRequest
from quorum_fullnode_py.exceptions import ParamValueError

logger = logging.getLogger(__name__)


class FullNode:
    _group_id = None

    def __init__(
        self,
        api_base: str = None,
        jwt_token: str = None,
        port: int = None,
    ):
        if port:
            api_base = f"http://127.0.0.1:{port}"
        if not api_base:
            raise ParamValueError("api_base is required")

        http = HttpRequest(api_base, jwt_token)
        self.api = FullNodeAPI(http, self.group_id)

    @property
    def group_id(self):
        return self._group_id

    @group_id.setter
    def group_id(self, group_id):
        self._group_id = group_id
        self.api.group_id = group_id
