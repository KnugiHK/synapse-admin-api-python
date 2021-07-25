from synapse_admin import base
import pytest

with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
base_handler = base.Admin(*conn)

def test_utility_get_bool():
    ...

def test_utility_get_current_time():
    ...

def test_utility_get_password():
    ...

def test_base_contents():
    ...

def test_base_create_config():
    ...

def test_base_modify_config():
    ...

def test_base_read_config():
    ...

def test_base_validate_server():
    ...

def test_base_validate_username():
    ...

def test_base_validate_room():
    ...

def test_base_validate_group():
    ...

def test_base_validate_alias():
    ...

def test_base_admin_patterns():
    ...

def test_base_client_delete():
    ...

def test_base_httpconnection_request():
    ...
