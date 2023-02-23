""" 
pip install pytest-ordering

"""

import os
import sys

import pytest

repo = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, repo)

from quorum_fullnode_py import FeedData, FullNode
from tests._config import API_BASE, JWT

bot = FullNode(api_base=API_BASE, jwt_token=JWT)
