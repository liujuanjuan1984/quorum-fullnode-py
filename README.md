# quorum_fullnode_py

Python SDK for FullNode of [QuoRum](https://github.com/rumsystem/quorum).

### About QuoRum

- https://rumsystem.net/
- https://github.com/rumsystem/quorum
- https://docs.rumsystem.net/docs/data-format-and-examples

### Install

[quorum_fullnode_py@pypi](https://pypi.org/project/quorum_fullnode_py/)

```sh
pip install quorum_fullnode_py
```

### Examples

```python

from quorum_fullnode_py import FullNode
from quorum_fullnode_py import FeedData as feed

bot = FullNode(port=11002)

bot.api.node_info()
info = bot.api.create_group('test_group')
bot.group_id = info['group_id']

data = feed.new_post(content='hello guys',images=[])
bot.api.post_content(data)

data = feed.like('a-post-id')
bot.api.post_content(data)
```

### pylint

```sh
isort ./quorum_fullnode_py/
black ./quorum_fullnode_py/
pylint ./quorum_fullnode_py/ --output=pylint.log

isort ./tests/
black ./tests/
pylint ./tests/ --output=pylint_tests.log

```


### License

This work is released under the `GPL3.0` license. A copy of the license is provided in the [LICENSE](https://github.com/liujuanjuan1984/quorum_fullnode_py/blob/master/LICENSE) file.
