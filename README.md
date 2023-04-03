# quorum_fullnode_py

Python SDK for Quorum FullNode.

More about QuoRum:

- https://rumsystem.net/
- https://github.com/rumsystem/quorum

### Install

```sh
pip install quorum_fullnode_py
```

### Usage

```python
from quorum_fullnode_py import FullNode

url = "http://127.0.0.1:11002"
jwt = "eyJhbGciO...VCJ9.eyJhbGxvd0...pbiJ9.FeyMWvzweE...o66QZ735nsrU"

# connect to a quorum fullnode with api url and chain jwt_token
client = FullNode(api_base=url, jwt_token=jwt)

# check node_status is online.
client.api.node_info().get("node_status") == "NODE_ONLINE"

# create a group chain for test
info = client.api.create_group("test_group")
client.group_id = info["group_id"]

# send a new post to the group chain
data = {
    "type": "Create",
    "object": {
        "type": "Note",
        "content": "nice to meet u!",
        "name": "hi",
        "id": "efb14f14-f849-4cf3-bcb6-c3598e857adb",
    },
}
resp = client.api.post_content(data)

# get trx from group chain
trx = client.api.trx(resp['trx_id'])

# get content:
trxs = client.api.get_content()

```

### Source

- quorum fullnode sdk for python: https://github.com/liujuanjuan1984/quorum-fullnode-py 
- quorum mininode sdk for python: https://github.com/liujuanjuan1984/quorum-mininode-py 
- and more ...  https://github.com/okdaodine/awesome-quorum

### License

This work is released under the `MIT` license. A copy of the license is provided in the [LICENSE](https://github.com/liujuanjuan1984/quorum_fullnode_py/blob/master/LICENSE) file.
