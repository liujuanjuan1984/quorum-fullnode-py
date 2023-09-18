import base64
import datetime
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


def _get_isoday(timedelta_days=0):
    """return iso day format string 2027-04-28T08:10:36.675204+00:00"""
    now = datetime.datetime.now(datetime.timezone.utc)
    day = now + datetime.timedelta(days=timedelta_days)
    iso = day.isoformat(timespec="seconds")
    return iso


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
        self,
        role: str = None,
        name: str = None,
        group_id: str = None,
        expires_at: str = None,
    ):
        """
        Create a new auth token, only allow access from localhost
        expires_at: ISO time 2027-04-28T08:10:36.675204+00:00
        """

        role = role or "node"
        if role not in ("node", "chain"):
            raise ParamValueError("role must be one of ['node','chain']")
        if role == "chain":
            group_id = None
            name = name or "allow-chain"
        else:
            group_id = self._check_group_id_as_required(group_id)
            name = name or f"allow-{group_id}"

        expires_at = expires_at or _get_isoday(5 * 365)
        payload = {
            "name": name,
            "role": role,
            "group_id": group_id,
            "expires_at": expires_at,
        }
        return super()._create_token(payload)

    def refresh_token(self):
        """
        refresh auth token.
        For example, when the token is about to expire,
        they can use this interface to obtain a new token.
        """
        return super()._refresh_token()

    def list_token(self):
        """list all jwt tokens"""
        return super()._get_token_list()

    def revoke_token(
        self, token: str = None, role: str = None, group_id: str = None
    ):
        """
        to revoke a usable token and make it unusable,
        then add it to the "revoke list" in the config file.
        """
        role = role or "node"
        if role not in ("node", "chain"):
            raise ParamValueError("role must be one of ['node','chain']")
        if role == "chain":
            group_id = None
        else:
            group_id = self._check_group_id_as_required(group_id)
        payload = {
            "role": role,
            "group_id": group_id,
            "token": token,
        }
        return super()._revoke_token(payload)

    def remove_token(
        self, token: str = None, role: str = None, group_id: str = None
    ):
        """to delete token from config file"""
        role = role or "node"
        if role not in ("node", "chain"):
            raise ParamValueError("role must be one of ['node','chain']")
        if role == "chain":
            group_id = None
        else:
            group_id = self._check_group_id_as_required(group_id)
        payload = {
            "role": role,
            "group_id": group_id,
            "token": token,
        }
        return super()._remove_token(payload)

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
        return super()._get_group(group_id)

    def create_group(
        self,
        group_name: str,
        app_key: str = "group_timeline",
        consensus_type: str = "poa",
        encryption_type: str = "public",
        include_chain_url: bool = False,
    ) -> dict:
        """create a group, return the seed of the group."""

        payload = {
            "group_name": group_name,
            "app_key": app_key,
            "consensus_type": consensus_type.lower(),
            "encryption_type": encryption_type.lower(),
            "include_chain_url": include_chain_url,
        }

        return super()._create_group(payload)

    def seed(
        self, group_id: str = None, include_chain_url: bool = False
    ) -> str:
        """get the seed of a group which you've joined in."""
        group_id = self._check_group_joined_as_required(group_id)
        resp = super()._get_seed(group_id, include_chain_url)
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
        start_trx: str = None,
        group_id: str = None,
        num: int = 20,
        reverse: bool = False,
        include_start_trx: bool = False,
        senders: list = None,
    ) -> list:
        group_id = self._check_group_id_as_required(group_id)
        params = {
            "num": num,
            "reverse": reverse,
        }
        if start_trx:
            params["start_trx"] = start_trx
            params["include_start_trx"] = include_start_trx
        if senders:
            params["senders"] = senders
        trxs = []
        for trx in super()._get_content(group_id, params):
            # private group will return trx without Data
            try:
                trx["Data"] = json.loads(base64.b64decode(trx["Data"]))
            except Exception as err:
                logger.warning(f"decode trx data error: {err}\n{trx}")
            trxs.append(trx)
        return trxs

    def trx(self, trx_id: str, group_id: str = None):
        """get trx data by trx_id"""
        trx = {}
        if not trx_id:
            return trx

        trxs = self.get_content(
            start_trx=trx_id, num=1, include_start_trx=True, group_id=group_id
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
        """get the producers pubkey list of the group"""
        bps = self.get_consensus(group_id).get("producers", [])
        return [bp["ProducerPubkey"] for bp in bps]

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
        return super()._update_consensus(payload)

    def remove_producer(self, pubkeys: list, group_id: str = None):
        """remove pubkey as group producer from the group"""
        payload = {
            "producer_pubkey": pubkeys,
            "group_id": group_id,
            "action": "remove",
        }
        return super()._update_consensus(payload)

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

    def get_consensus(self, group_id: str = None):
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_consensus(group_id)

    def get_consensus_req(self, req_id: str, group_id: str = None):
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_consensus_req(group_id, req_id)

    def get_consensus_last(self, group_id: str = None):
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_consensus_last(group_id)

    def get_consensus_history(self, group_id: str = None):
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_consensus_history(group_id)

    def get_consensus_current(self, group_id: str = None):
        group_id = self._check_group_id_as_required(group_id)
        return super()._get_consensus_current(group_id)

    def update_consensus(
        self,
        start_from_epoch: int = None,
        trx_epoch_tick: int = None,
        agreement_tick_length: int = None,
        agreement_tick_count=None,
        producer_pubkey: list = None,
        group_id: str = None,
    ):
        group_id = self._check_group_id_as_required(group_id)
        req_id = self.get_consensus(group_id).get("proof_req_id")
        reqs = self.get_consensus_req(req_id, group_id).get("resps", [])
        if not reqs:
            req = {}
        else:
            req = reqs[0]["Req"]

        if start_from_epoch is None:
            start_from_epoch = 1
        if trx_epoch_tick and trx_epoch_tick < 500:
            raise ValueError("trx_epoch_tick should be greater than 500(ms)")
        if agreement_tick_length and agreement_tick_length < 1000:
            raise ValueError(
                "agreement_tick_length should be greater than 1000(ms)"
            )
        if agreement_tick_count and agreement_tick_count < 10:
            raise ValueError("agreement_tick_count should be greater than 10")

        _exist = {
            "group_id": group_id,
            "start_from_epoch": req.get("StartFromEpoch") or 1,
            "trx_epoch_tick": req.get("TrxEpochTickLenInMs") or 500,
            "agreement_tick_Length": req.get("AgreementTickLenInMs") or 1000,
            "agreement_tick_count": req.get("AgreementTickCount") or 10,
            "producer_pubkey": req.get("ProducerPubkeyList") or [],
        }

        payload = {
            "group_id": group_id,
            "start_from_epoch": start_from_epoch or _exist["start_from_epoch"],
            "trx_epoch_tick": trx_epoch_tick or _exist["trx_epoch_tick"],
            "agreement_tick_Length": agreement_tick_length
            or _exist["agreement_tick_Length"],
            "agreement_tick_count": agreement_tick_count
            or _exist["agreement_tick_count"],
            "producer_pubkey": producer_pubkey or _exist["producer_pubkey"],
        }

        if payload == _exist:
            return {"message": "Nothing to update"}

        if payload["trx_epoch_tick"] < payload["agreement_tick_Length"]:
            logger.warning(
                "trx_epoch_tick %s should be greater than agreement_tick_Length %s",
                payload["trx_epoch_tick"],
                payload["agreement_tick_Length"],
            )
        return super()._update_consensus(payload)

    def update_user(self, payload: dict = None):
        return super()._update_user(payload)

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
