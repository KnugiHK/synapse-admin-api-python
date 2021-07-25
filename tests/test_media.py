from synapse_admin import Media
import pytest

with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
media_handler = Media(*conn)

def test_media_statistics():
    ...

def test_media_list_media():
    ...

def test_media_quarantine_id():
    ...

def test_media_quarantine_room():
    ...

def test_media_quarantine_user():
    ...

def test_media_quarantine_remove():
    ...

def test_media_protect_media():
    ...

def test_media_unprotect_media():
    ...

def test_media_delete_media():
    ...

def test_media_delete_local_media():
    ...

def test_media_delete_local_media_by_condition():
    ...

def test_media_purge_remote_media():
    ...
