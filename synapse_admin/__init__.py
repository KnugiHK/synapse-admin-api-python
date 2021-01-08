import sys
if sys.version_info < (3, 6):
    print("Synapse Admin API requires Python 3.6 or above.")
    sys.exit(1)

__version__ = "0.1.0"

from synapse_admin.user import User
import synapse_admin.base as base
