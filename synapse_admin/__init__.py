import sys
if sys.version_info < (3, 6):
    print("Synapse Admin API requires Python 3.6 or above.")
    sys.exit(1)

__version__ = "0.1.0"

from synapse_admin.user import User
from synapse_admin.management import Management
from synapse_admin.media import Media
from synapse_admin.room import Room
import synapse_admin.base as base
