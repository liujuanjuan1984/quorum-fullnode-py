import logging

from quorum_fullnode_py.client import FullNode, HttpRequest
from quorum_fullnode_py.types import FeedData

__version__ = "1.0.1"
__author__ = "liujuanjuan1984"

# Set default logging handler to avoid "No handler found" warnings.
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
