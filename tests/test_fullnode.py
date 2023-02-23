import time

import pytest

from quorum_fullnode_py import FeedData as feed
from quorum_fullnode_py.exceptions import ParamValueError
from tests import bot


@pytest.mark.run(order=10)
def test_node_info():
    resp = bot.api.node_info()
    assert resp["node_status"] == "NODE_ONLINE"


@pytest.mark.run(order=9)
def test_network():
    resp = bot.api.network()
    assert resp["nat_type"] in ["Public", "Private"]


@pytest.mark.run(order=8)
def test_groups():
    resp = bot.api.groups()
    assert isinstance(resp, list)


def test_create_group():
    info = bot.api.create_group("test_group")
    assert "group_id" in info
    group_id = info["group_id"]

    assert "seed" in info
    seed = info["seed"]

    _seed = bot.api.seed(group_id)
    assert seed == _seed

    resp = bot.api.join_group(seed)
    assert "message" in resp

    bot.group_id = group_id
    assert bot.api.group_id == group_id

    ginfo = bot.api.group_info()
    assert ginfo["group_id"] == group_id


@pytest.mark.run(order=1)
def test_post_content():

    # create group if not exist
    groups_id = bot.api.groups_id
    assert isinstance(groups_id, list)

    if len(groups_id) == 0:
        info = bot.api.create_group("test_group")
        assert "group_id" in info

    group_id = bot.api.groups_id[0]
    bot.group_id = group_id

    # post content with empty data

    resps = []

    data = feed.new_post(content="hello world", images=[])
    resp = bot.api.post_content(data)
    assert "trx_id" in resp
    resps.append(resp)

    data = feed.new_post(
        content="hello world", images=[], post_id="test_postid"
    )
    resp = bot.api.post_content(data)
    assert "trx_id" in resp
    resps.append(resp)

    data = feed.new_post(content="hello world", images=[], name="test_postid")
    resp = bot.api.post_content(data)
    assert "trx_id" in resp
    resps.append(resp)

    try:
        data = feed.new_post(content=None, images=[], name="test_postid")
        resp = bot.api.post_content(data)
    except ParamValueError:
        pass

    for resp in resps:
        onchain = False
        for i in range(50):
            _trx = bot.api.trx(resp["trx_id"])
            if _trx.get("TrxId") == resp["trx_id"]:
                onchain = True
                break
            time.sleep(0.1)
        assert onchain

    trxs = bot.api.get_content()
    assert len(trxs) >= 0


@pytest.mark.run(order=-2)
def test_clear_group():
    groups_id = bot.api.groups_id
    assert isinstance(groups_id, list)
    for group_id in groups_id:
        resp = bot.api.leave_group(group_id)
        assert resp["group_id"] == group_id
        resp = bot.api.clear_group(group_id)
        assert resp["group_id"] == group_id
    assert len(bot.api.groups_id) == 0
