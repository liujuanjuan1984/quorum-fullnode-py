import json
import logging

from quorum_fullnode_py.api.base import BaseAPI
from quorum_fullnode_py.exceptions import ParamValueError, RumChainException

logger = logging.getLogger(__name__)

TRX_TYPES = [
    "POST",
    "ANNOUNCE",
    "REQ_BLOCK_FORWARD",
    "REQ_BLOCK_BACKWARD",
    "BLOCK_SYNCED",
    "BLOCK_PRODUCED",
    "ASK_PEERID",
]


def _check_trx_type(trx_type: str):
    trx_type = trx_type.upper()
    if trx_type not in TRX_TYPES:
        raise ParamValueError(f"{trx_type} must be one of {TRX_TYPES}")
    return trx_type


def _check_trx_mode(mode: str):
    if mode.lower() in ["dny", "deny"]:
        return "dny"
    if mode.lower() in ["alw", "allow"]:
        return "alw"
    raise ParamValueError(f"{mode} mode must be one of ['deny','allow']")


class FullNodeAPI(BaseAPI):
    def _check_group_id_as_required(self, group_id: str = None):
        group_id = group_id or self.group_id
        if not group_id:
            raise ParamValueError("group_id is required")
        return group_id

    def _check_group_joined_as_required(self, group_id: str = None):
        group_id = self._check_group_id_as_required(group_id)
        if group_id not in self.groups_id:
            raise RumChainException(f"You are not in this group: <{group_id}>.")
        return group_id

    def _check_group_owner_as_required(self, group_id: str = None):
        group_id = self._check_group_joined_as_required(group_id)
        info = self.group_info(group_id)
        if info.get("user_pubkey", "user") != info.get("owner_pubkey", "owner"):
            raise RumChainException(
                f"You are not the owner of this group: <{group_id}>."
            )
        return group_id

    def node_info(self):
        return super()._get_node()

    def network(self):
        return super()._get_network()

    def connect_peers(self, peers: list):
        """connect to peers.
        one peer in the list is like:
        "/ip4/10x.xx.xxx.xxx/tcp/31124/p2p/16Uiu2H...uisLB"
        """
        return super()._post_peers(peers)

    def ask_for_relay(self, peers: list):
        """node in private network ask for relay servers
        one peer in the list is like:
        "/ip4/10x.xx.xxx.xxx/tcp/31124/p2p/16Uiu2H...uisLB"
        """
        return super()._ask_for_relay(peers)

    def groups(self) -> list:
        data = super()._get_groups() or {}
        return data.get("groups") or []

    @property
    def groups_id(self) -> list:
        """return list of group_id which node has joined"""
        return [i["group_id"] for i in self.groups()]

    def pubkeytoaddr(self, pubkey: str):
        """convert pubkey to address"""
        resp = super()._pubkeytoaddr({"encoded_pubkey": pubkey})
        return resp.get("addr", resp)

    def create_token(
        self, name: str, role: str, allow_groups: list, expires_at: int
    ):
        """Create a new auth token, only allow access from localhost"""
        payload = {
            "name": name,
            "role": role,
            "allow_groups": allow_groups,
            "expires_at": expires_at,
        }
        return super()._create_token(payload)

    def refresh_token(self, payload):
        """Get a new auth token"""
        return super()._refresh_token(payload)

    def group_network(self, group_id: str = None):
        """return the peers connented to the group"""
        group_id = self._check_group_id_as_required(group_id)
        rlt = []
        groups = super()._get_network().get("groups", [])
        for i in groups:
            if i.get("GroupId") == group_id:
                rlt = i.get("Peers", [])
                break
        return rlt

    def group_info(self, group_id: str = None) -> dict:
        """get the group info"""
        group_id = self._check_group_joined_as_required(group_id)
        info = {}
        groups = super()._get_groups().get("groups", [])
        for _info in groups:
            if _info["group_id"] == group_id:
                info = _info
                break
        return info

    def create_group(
        self,
        group_name: str,
        app_key: str = "group_timeline",
        consensus_type: str = "poa",
        encryption_type: str = "public",
    ) -> dict:
        """create a group, return the seed of the group.

        group_name: 自定义，创建后不可更改
        consensus_type: poa，pos 等，目前只支持了 poa
        encryption_type: "public","private"
        app_key: 可以为自定义。如果想要和已有的 app 兼容，推荐采用 group_timeline, group_post, group_note 等
        """

        payload = {
            "group_name": group_name,
            "app_key": app_key,
            "consensus_type": consensus_type.lower(),
            "encryption_type": encryption_type.lower(),
        }

        return super()._create_group(payload)

    def seed(self, group_id: str = None) -> str:
        """get the seed of a group which you've joined in."""
        group_id = self._check_group_joined_as_required(group_id)
        resp = super()._get_seed(group_id)
        return resp.get("seed", resp)

    def join_group(self, seed: str):
        """join a group with the seed of the group
        the seed is string startswith rum://
        """
        return super()._join_group({"seed": seed})

    def leave_group(self, group_id: str = None):
        """leave a group"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._leave_group({"group_id": group_id})

    def clear_group(self, group_id: str = None):
        """clear data of a group"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._clear_group({"group_id": group_id})

    def post_content(self, data: dict, group_id: str = None):
        """post trx to group"""
        group_id = self._check_group_joined_as_required(group_id)
        return super()._post_content(group_id, {"data": data})

    def get_content(
        self,
        starttrx: str = None,
        group_id: str = None,
        num: int = 20,
        reverse: bool = False,
        includestarttrx: bool = False,
        senders: list = None,
    ) -> list:
        """requests the content trxs of a group,return the list of the trxs data.
        reverse: 默认按顺序获取, 如果是 True, 从最新的内容开始获取
        starttrx: 某条内容的 Trx ID, 如果提供, 从该条之后(不包含)获取
        num: 要获取内容条数, 默认获取最前面的 20 条内容
        includestarttrx: 如果是 True, 获取内容包含 Trx ID 这条内容
        """
        group_id = self._check_group_id_as_required(group_id)

        params = {
            "num": num,
            "reverse": reverse,
        }
        if starttrx:
            params["starttrx"] = starttrx
            params["includestarttrx"] = includestarttrx
        if senders:
            params["senders"] = senders
        return super()._get_content(group_id, params)

    def trx(self, trx_id: str, group_id: str = None):
        """get trx data by trx_id"""
        trx = {}
        if not trx_id:
            return trx

        trxs = self.get_content(
            starttrx=trx_id, num=1, includestarttrx=True, group_id=group_id
        )
        if trxs:
            trx = trxs[0]
        else:
            trx = self.get_trx(trx_id, group_id)
        return trx

    def get_block(self, block_id, group_id: str = None):
        """get the info of a block in a group"""
        group_id = self._check_group_joined_as_required(group_id)
        return super()._get_block(group_id, block_id)

    def startsync(self, group_id: str = None):
        """start sync data of a group"""
        group_id = self._check_group_joined_as_required(group_id)
        return super()._startsync(group_id)

    def get_trx(self, trx_id: str, group_id: str = None):
        group_id = self._check_group_joined_as_required(group_id)
        return super()._get_trx(group_id, trx_id)

    def pubqueue(self, group_id: str = None) -> list:
        """get the pub queue list"""
        group_id = self._check_group_id_as_required(group_id)
        resp = super()._get_pubqueue(group_id)
        return resp.get("Data", resp)

    def ack(self, trx_ids: list):
        """ack the trxs"""
        if trx_ids == []:
            return True
        return super()._pubqueue_ack({"trx_ids": trx_ids})

    def autoack(self, group_id: str = None):
        """auto ack the  Fail trxs"""
        group_id = self._check_group_id_as_required(group_id)
        tids = [
            i["Trx"]["TrxId"]
            for i in self.pubqueue(group_id)
            if i["State"] == "FAIL"
        ]
        return self.ack(tids)

    def get_keylist(self, group_id: str = None):
        """get the keylist of the group appconfig"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_appconfig_keylist(group_id)

    def get_key(self, key: str, group_id: str = None):
        """get the key value of the group appconfig by keyname"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_appconfig_key(group_id, key)

    def update_appconfig(
        self,
        name: str,
        _type: str,
        value: str,
        action: str = "add",
        memo: str = None,
        group_id: str = None,
    ):
        group_id = self._check_group_owner_as_required(group_id)

        if action.lower() not in ["add", "remove"]:
            raise ParamValueError("action must be add or remove")
        payload = {
            "action": action.lower() or "add",
            "group_id": group_id,
            "name": name,
            "type": _type,
            "value": value,
            "memo": memo or f"update {name}",
        }
        return super()._post_appconfig(payload)

    def get_trx_auth(self, trx_type: str = "POST", group_id: str = None):
        """get the trx mode of trx type
        trx_type: "POST","ANNOUNCE","REQ_BLOCK_FORWARD","REQ_BLOCK_BACKWARD",
        "BLOCK_SYNCED","BLOCK_PRODUCED" or "ASK_PEERID"
        """
        group_id = self._check_group_id_as_required(group_id)
        trx_type = _check_trx_type(trx_type)
        return super()._get_trx_auth(group_id, trx_type)

    def get_auth(self):
        """get the trx mode of all the trx types"""
        rlt = {}
        for itype in TRX_TYPES:
            resp = self.get_trx_auth(itype)
            rlt[resp["TrxType"]] = resp["AuthType"]
        return rlt

    def set_trx_auth(
        self,
        trx_type: str,
        mode: str,
        memo: str = "set trx auth type",
        group_id: str = None,
    ):
        """set the trx mode of trx type
        trx_type: "POST","ANNOUNCE","REQ_BLOCK_FORWARD","REQ_BLOCK_BACKWARD",
            "BLOCK_SYNCED","BLOCK_PRODUCED" or "ASK_PEERID"
        mode:
            alw "follow_alw_list"
            dny "follow_dny_list"
        """
        group_id = self._check_group_owner_as_required(group_id)
        mode = _check_trx_mode(mode)
        trx_type = _check_trx_type(trx_type)
        payload = {
            "group_id": group_id,
            "type": "set_trx_auth_mode",
            "config": json.dumps(
                {"trx_type": trx_type, "trx_auth_mode": f"follow_{mode}_list"}
            ),
            "Memo": memo,
        }
        return super()._post_chainconfig(payload)

    def get_allow_list(self, group_id: str = None):
        """get allow list"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_allowlist(group_id) or []

    def get_deny_list(self, group_id: str = None):
        """get deny list"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_denylist(group_id) or []

    def _update_list(
        self,
        pubkey: str,
        mode: str,
        memo: str = "update list",
        action: str = "add",
        trx_types: list = None,
        group_id: str = None,
    ):
        """update the list for the trx mode"""
        group_id = self._check_group_owner_as_required(group_id)
        mode = _check_trx_mode(mode)
        trx_types = trx_types or ["post"]
        trx_types = [_check_trx_type(trx_type) for trx_type in trx_types]
        if action not in ["add", "remove"]:
            raise ParamValueError("action must be add or remove")
        _params = {"action": action, "pubkey": pubkey, "trx_type": trx_types}
        payload = {
            "group_id": group_id,
            "type": f"upd_{mode}_list",
            "config": json.dumps(_params),
            "Memo": memo,
        }
        return super()._post_chainconfig(payload)

    def add_allow_list(
        self, pubkey: str, trx_types: list = None, group_id: str = None
    ):
        """add pubkey to allow list of trx types"""
        return self._update_list(
            pubkey,
            mode="alw",
            memo="add allow list",
            action="add",
            trx_types=trx_types,
            group_id=group_id,
        )

    def remove_allow_list(
        self, pubkey: str, trx_types: list = None, group_id: str = None
    ):
        """remove pubkey from allow list of trx types"""
        return self._update_list(
            pubkey,
            mode="alw",
            memo="remove allow list",
            action="remove",
            trx_types=trx_types,
            group_id=group_id,
        )

    def add_deny_list(
        self, pubkey: str, trx_types: list = None, group_id: str = None
    ):
        """add pubkey to deny list of trx types"""
        return self._update_list(
            pubkey,
            mode="dny",
            memo="add deny list",
            action="add",
            trx_types=trx_types,
            group_id=group_id,
        )

    def remove_deny_list(
        self, pubkey: str, trx_types: list = None, group_id: str = None
    ):
        """remove pubkey from deny list of trx types"""
        return self._update_list(
            pubkey,
            mode="dny",
            memo="remove deny list",
            action="remove",
            trx_types=trx_types,
            group_id=group_id,
        )

    def producers(self, group_id: str = None):
        """get the producers of the group"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_producers(group_id)

    def get_announced_producers(self, group_id: str = None):
        """get the announced producers to be approved"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_announced_producers(group_id)

    def add_producer(self, pubkeys: list, group_id: str = None):
        """add pubkey as group producer to the group"""
        payload = {
            "producer_pubkey": pubkeys,
            "group_id": group_id,
            "action": "add",
        }
        return super()._post_producer(payload)

    def remove_producer(self, pubkeys: list, group_id: str = None):
        """remove pubkey as group producer from the group"""
        payload = {
            "producer_pubkey": pubkeys,
            "group_id": group_id,
            "action": "remove",
        }
        return super()._post_producer(payload)

    def announce_as_producer(self, group_id: str = None, memo: str = None):
        """announce fullnode self as producer"""
        group_id = self._check_group_id_as_required(group_id)
        payload = {
            "group_id": group_id,
            "action": "add",
            "type": "producer",
            "memo": memo or "announce self as producer",
        }
        return super()._announce(payload)

    def announce_as_producer_to_remove(
        self, group_id: str = None, memo: str = None
    ):
        """announce fullnode self as producer to remove"""
        group_id = self._check_group_id_as_required(group_id)
        payload = {
            "group_id": group_id,
            "action": "remove",
            "type": "producer",
            "memo": memo or "announce self as producer to remove",
        }
        return super()._announce(payload)

    def get_announced_users(self, group_id: str = None):
        """get the announced users to approve(add or remove)"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_announced_users(group_id)

    def get_announced_user(self, pubkey: str, group_id: str = None):
        """check the user is announced or not"""
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_announced_user(group_id, pubkey)

    def announce_as_user(self, memo: str = None, group_id: str = None):
        """announce as user"""
        group_id = self._check_group_id_as_required(group_id)
        payload = {
            "group_id": group_id,
            "action": "add",
            "type": "user",
            "memo": memo or "announce self as user",
        }
        return super()._announce(payload)

    def _approve_user(self, pubkey: str, action: str, group_id: str = None):
        """update the user of the group
        action: "add" or "remove"
        """
        group_id = self._check_group_owner_as_required(group_id)
        if action.lower() not in ["add", "remove"]:
            raise ParamValueError("action must be one of these: add, remove")
        payload = {
            "user_pubkey": pubkey,
            "group_id": group_id,
            "action": action.lower(),
        }
        return super()._post_user(payload)

    def add_user(self, pubkey: str, group_id: str = None):
        """add pubkey as group user to the group"""
        try:
            status = self.get_announced_user(pubkey)
            if status.get("Result") == "APPROVED":
                return status
        except Exception as err:
            logger.debug(err)
        return self._approve_user(pubkey, "add", group_id)

    def remove_user(self, pubkey: str, group_id: str = None):
        """remove pubkey as group user from the group"""
        return self._approve_user(pubkey, "remove", group_id)
