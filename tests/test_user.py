from synapse_admin import User
import pytest

with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
user_handler = User(*conn)

def test_user_list():
    ...

def test_user_create():
    ...

def test_user_modify():
    ...

def test_user_query():
    ...

def test_user_active_session():
    ...

def test_user_deactivate():
    ...

def test_user_reactivate():
    ...

def test_user_reset_password():
    ...

def test_user_set_admin():
    ...

def test_user_is_admin():
    ...

def test_user_join_room():
    ...

def test_user_joined_room():
    ...

def test_user_validity():
    ...

def test_user_register():
    ...

def test_user_list_media():
    ...

def test_user_login():
    ...

def test_user_get_ratelimit():
    ...

def test_user_get_ratelimit():
    ...

def test_user_set_ratelimit():
    ...

def test_user_disable_ratelimit():
    ...

def test_user_delete_ratelimit():
    ...

def test_user_pushers():
    ...

def test_user_shadow_ban():
    ...

def test_user_device_lists():
    ...

def test_user_device_delete():
    ...

def test_user_device_delete_multiple():
    ...

def test_user_device_show():
    ...

def test_user_device_update():
    ...
