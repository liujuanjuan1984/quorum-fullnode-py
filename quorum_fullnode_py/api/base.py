import json
import logging
from urllib.parse import urlencode

from quorum_fullnode_py.client._http import HttpRequest

logger = logging.getLogger(__name__)


class BaseAPI:
    """
    base apis of the quorum fullnode without params vadiation
    good for quorum chain testing
    """

    def __init__(self, http: HttpRequest, group_id: str):
        self._http = http
        self.group_id = group_id

    def _get(self, endpoint: str, payload: dict = None):
        return self._http.get(endpoint, payload)

    def _post(self, endpoint: str, payload: dict = None):
        return self._http.post(endpoint, payload)

    def _delete(self, endpoint: str, payload: dict = None):
        return self._http.delete(endpoint, payload)

    def _get_node(self):
        """get node info"""
        return self._get("/api/v1/node")

    def _get_groups(self):
        """return list of groups info which this node has joined"""
        return self._get("/api/v1/groups")

    def _get_group(self, group_id: str):
        """return list of groups info which this node has joined"""
        return self._get(f"/api/v1/group/{group_id}")

    def _get_seed(self, group_id: str = None, include_chain_url: bool = False):
        include_chain_url = json.dumps(include_chain_url)
        return self._get(
            f"/api/v1/group/{group_id}/seed?include_chain_url={include_chain_url}"
        )

    def _get_block(self, group_id: str = None, block_id: str = None):
        return self._get(f"/api/v1/block/{group_id}/{block_id}")

    def _get_network(self):
        """get network info of node"""
        return self._get("/api/v1/network")

    def _post_peers(self, payload: dict = None):
        return self._post("/api/v1/network/peers", payload)

    def _create_group(self, payload: dict = None):
        return self._post("/api/v1/group", payload)

    def _join_group(self, payload: dict = None):
        return self._post("/api/v2/group/join", payload)

    def _leave_group(self, payload: dict = None):
        return self._post("/api/v1/group/leave", payload)

    def _clear_group(self, payload: dict = None):
        return self._post("/api/v1/group/clear", payload)

    def _get_token_list(self):
        return self._get("/app/api/v1/token/list")

    def _create_token(self, payload: dict = None):
        return self._post("/app/api/v1/token", payload)

    def _refresh_token(self, payload: dict = None):
        return self._post("/app/api/v1/token/refresh", payload)

    def _revoke_token(self, payload: dict = None):
        return self._post("/app/api/v1/token/revoke", payload)

    def _remove_token(self, payload: dict = None):
        """delete token from config file"""
        return self._delete("/app/api/v1/token", payload)

    def _pubkeytoaddr(self, payload: dict = None):
        return self._post("/api/v1/tools/pubkeytoaddr", payload)

    def _ask_for_relay(self, payload: dict = None):
        return self._post("/api/v1/network/relay", payload)

    def _startsync(self, group_id: str = None):
        return self._post(f"/api/v1/group/{group_id}/startsync")

    def _get_pubqueue(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/pubqueue")

    def _pubqueue_ack(self, payload: dict = None):
        return self._post("/api/v1/trx/ack", payload)

    def _get_trx(self, group_id: str = None, trx_id: str = None):
        return self._get(f"/api/v1/trx/{group_id}/{trx_id}")

    def _post_profile(self, payload: dict = None):
        return self._post("/api/v1/group/profile", payload)

    def _post_content(self, group_id: str = None, payload: dict = None):
        return self._post(f"/api/v1/group/{group_id}/content", payload)

    def _get_content(self, group_id: str = None, query_params: dict = None):
        endpoint = f"/app/api/v1/group/{group_id}/content"
        if query_params:
            for k, v in query_params.items():
                if isinstance(v, bool):
                    query_params[k] = json.dumps(v)
            query_string = urlencode(query_params, doseq=True)
            endpoint = f"{endpoint}?{query_string}"
        return self._get(endpoint)

    def _get_appconfig_keylist(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/appconfig/keylist")

    def _get_appconfig_key(self, group_id: str = None, key=None):
        return self._get(f"/api/v1/group/{group_id}/appconfig/{key}")

    def _post_appconfig(self, payload: dict = None):
        return self._post("/api/v1/group/appconfig", payload)

    def _get_trx_auth(self, group_id: str = None, trx_type=None):
        return self._get(f"/api/v1/group/{group_id}/trx/auth/{trx_type}")

    def _post_chainconfig(self, payload: dict = None):
        return self._post("/api/v1/group/chainconfig", payload)

    def _get_allowlist(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/trx/allowlist")

    def _get_denylist(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/trx/denylist")

    def _announce(self, payload: dict = None):
        return self._post("/api/v1/group/announce", payload)

    def _get_announced_users(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/announced/users")

    def _get_announced_user(self, group_id: str = None, pubkey=None):
        return self._get(f"/api/v1/group/{group_id}/announced/user/{pubkey}")

    def _get_announced_producers(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/announced/producers")

    def _post_user(self, payload: dict = None):
        return self._post("/api/v1/group/user", payload)

    def _get_consensus(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/consensus/")

    def _get_consensus_req(self, group_id: str = None, req_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/consensus/proof/{req_id}")

    def _get_consensus_last(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/consensus/proof/last")

    def _get_consensus_history(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/consensus/proof/history")

    def _get_consensus_current(self, group_id: str = None):
        return self._get(f"/api/v1/group/{group_id}/consensus/proof/current")

    def _update_consensus(self, payload: dict = None):
        return self._post("/api/v1/group/updconsensus", payload)

    def _update_user(self, payload: dict = None):
        return self._post("/api/v1/group/upduser", payload)
