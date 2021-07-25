from synapse_admin import Room
import pytest

with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
room_handler = Room(*conn)

def test_room_lists():
    ...

def test_room_details():
    ...

def test_room_list_members():
    ...

def test_room_create():
    ...

def test_room_delete():
    ...

def test_room_set_admin():
    ...

def test_room_forward_extremities_check():
    ...

def test_room_forward_extremities_delete():
    ...

def test_room_get_state():
    ...

def test_room_event_context():
    ...
