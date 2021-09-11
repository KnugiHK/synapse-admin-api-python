import sys
if sys.version_info < (3, 7):
    print("matrix-synapse-admin requires Python 3.7 or above.")
    sys.exit(1)

__version__ = "0.5.6"

from synapse_admin.user import User  # noqa: F401
from synapse_admin.management import Management  # noqa: F401
from synapse_admin.media import Media  # noqa: F401
from synapse_admin.room import Room  # noqa: F401
import synapse_admin.base as base  # noqa: F401
Mgt = Management  # Alias
