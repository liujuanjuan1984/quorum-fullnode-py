import pytest

from quorum_fullnode_py import FullNode
from tests._config import API_BASE, JWT

bot = FullNode(api_base=API_BASE, jwt_token=JWT)
