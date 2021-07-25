from synapse_admin.client import ClientAPI
import pytest

with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
client_handler = ClientAPI(*conn)

def test_client_client_create():
    ...

def test_client_client_leave():
    ...

def test_client_admin_login():
    ...
