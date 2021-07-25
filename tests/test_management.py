from synapse_admin import Management
import pytest

with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
mgt_handler = Management(*conn)

def test_management_announce():
    ...

def test_management_announce_all():
    ...

def test_management_version():
    ...

def test_management_purge_history():
    ...

def test_management_purge_history_status():
    ...

def test_management_event_reports():
    ...

def test_management_specific_event_report():
    ...

def test_management_delete_group():
    ...
