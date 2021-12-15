"""MIT License

Copyright (c) 2021 Knugi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import pytest
import time
from synapse_admin import User, Room
from synapse_admin.client import ClientAPI
from synapse_admin.base import SynapseException, Utility
from yaml import load, CLoader


with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")

config = load(open("synapse_test/homeserver.yaml", "r"), Loader=CLoader)


conn = ("localhost", 8008, admin_access_token, "http://")
user_handler = User(*conn)


def test_user_list():
    exist_users = []
    for user in user_handler.lists():
        exist_users.append(user["name"][1:])
    assert exist_users == ["admin1:localhost", "test1:localhost"]


def test_user_create():
    user_handler.create(
        "test2",
        password="12345678",
        displayname="Test 2",
        admin=False,
        threepids=[{
            "medium": "email",
            "address": "test2@example.com"
        }],
        external_ids=[{
            "auth_provider": "https://example.com/test",
            "external_id": "test2"
        }]
    )
    assert user_handler.lists().total == 3


def test_user_modify():
    assert user_handler.create("test2", displayname="This is a test")


def test_user_query():
    test2 = user_handler.query("test2")
    assert test2["name"] == "@test2:localhost"
    assert test2["displayname"] == "This is a test"
    assert test2["admin"] == 0
    assert test2["threepids"][0]["medium"] == "email"
    assert test2["threepids"][0]["address"] == "test2@example.com"
    assert test2["external_ids"] == [{
            "auth_provider": "https://example.com/test",
            "external_id": "test2"
        }]


def test_user_active_session():
    assert user_handler.active_sessions("test2") == []


def test_user_deactivate():
    assert user_handler.deactivate("test2")
    with pytest.raises(SynapseException):
        user_handler.deactivate("invalid")
        assert ClientAPI.admin_login(
            "http://", "localhost",
            8008,
            "test2",
            "12345678",
            no_admin=True
        )


def test_user_reactivate():
    assert user_handler.reactivate("test2", "123456789123456789")
    assert ClientAPI.admin_login(
        "http://",
        "localhost",
        8008,
        "test2",
        "123456789123456789",
        no_admin=True
    )


def test_user_reset_password():
    assert user_handler.reset_password("test2", "12345678")
    with pytest.raises(SynapseException):
        assert ClientAPI.admin_login(
            "http://",
            "localhost",
            8008,
            "test2",
            "123456789123456789",
            no_admin=True
        )
    assert ClientAPI.admin_login(
        "http://",
        "localhost",
        8008,
        "test2",
        "12345678",
        no_admin=True
    )


def test_user_set_admin():
    assert user_handler.set_admin("test2", True) == (True, True)
    assert user_handler.set_admin("test2") == (True, False)
    assert user_handler.set_admin("test2") == (True, True)
    assert user_handler.set_admin("test2", False) == (True, False)
    with pytest.raises(SynapseException):
        user_handler.set_admin("invalid", True)


def test_user_is_admin():
    assert not user_handler.is_admin("test2")
    assert user_handler.is_admin("admin1")
    assert not user_handler.is_admin("invalid")


id, _ = Room(*conn).create(
    True,
    name="test",
    members=["test1"],
    encrypted=False
)


def test_user_join_room():
    assert user_handler.join_room("test2", id)
    with pytest.raises(SynapseException):
        user_handler.join_room("test2", "invalid")


def test_user_joined_room():
    assert user_handler.joined_room("test1") == [id]
    assert user_handler.joined_room("test2") == [id]
    assert user_handler.joined_room("invalid") == []


def test_user_validity():
    validity = int(time.time()) + 1234
    assert user_handler.validity("test2", validity) == validity
    assert user_handler.validity("test2") == 0


def test_user_register():
    shared_secret = config["registration_shared_secret"]
    reg = user_handler.register(
        "test3",
        shared_secret,
        displayname="Test3",
        password="123456789123456789"
    )
    assert "access_token" in reg and reg.get("access_token")[:4] == "syt_"

    wrong_shared_secret = b"invalid"
    with pytest.raises(SynapseException):
        user_handler.register(
            "test4",
            wrong_shared_secret,
            displayname="Test4",
            password="123456789123456789"
        )


def test_user_list_media():
    assert user_handler.list_media("test1") == []
    with pytest.raises(SynapseException):
        user_handler.list_media("invalid")


def test_user_login():
    user_token = user_handler.login("test2")
    assert isinstance(user_token, str) and user_token[:4] == "syt_"


def test_user_set_ratelimit():
    assert user_handler.set_ratelimit("test2", 10, 30) == (10, 30)
    with pytest.raises(SynapseException):
        user_handler.set_ratelimit("invalid", 10, 30)


def test_user_get_ratelimit():
    assert user_handler.get_ratelimit("test2") == (10, 30)
    with pytest.raises(SynapseException):
        user_handler.get_ratelimit("invalid")


def test_user_disable_ratelimit():
    assert user_handler.disable_ratelimit("test2") == (0, 0)
    with pytest.raises(SynapseException):
        user_handler.disable_ratelimit("invalid")


def test_user_delete_ratelimit():
    assert user_handler.delete_ratelimit("test2")
    assert user_handler.get_ratelimit("test2") == {}
    with pytest.raises(SynapseException):
        user_handler.delete_ratelimit("invalid")


def test_user_pushers():
    assert user_handler.pushers("test1") == []
    with pytest.raises(SynapseException):
        user_handler.pushers("invalid")


def test_user_shadow_ban():
    assert user_handler.shadow_ban("test2")
    assert user_handler.shadow_ban("test2")
    with pytest.raises(SynapseException):
        user_handler.shadow_ban("invalid")


def test_user_unshadow_ban():
    assert user_handler.unshadow_ban("test2")
    assert user_handler.unshadow_ban("test2")
    with pytest.raises(SynapseException):
        user_handler.shadow_ban("invalid")


def test_user_device_lists():
    for _ in range(3):
        ClientAPI.admin_login(
            "http://",
            "localhost",
            8008,
            "test2",
            "12345678",
            no_admin=True
        )

    devices = user_handler.devices.lists("test2")
    assert len(devices) == 4
    assert devices[0]["display_name"] == "matrix-synapse-admin"
    with pytest.raises(SynapseException):
        user_handler.devices.lists("invalid")


def test_user_device_update():
    devices = user_handler.devices.lists("test2")
    target = devices[0]["device_id"]
    assert user_handler.devices.update("test2", target, "testing_client")
    with pytest.raises(SynapseException):
        assert user_handler.devices.update("invalid", target, "testing_client")


def test_user_device_show():
    devices = user_handler.devices.lists("test2")
    target = devices[0]["device_id"]
    device = user_handler.devices.show("test2", target)
    assert device["display_name"] == "testing_client"
    with pytest.raises(SynapseException):
        assert user_handler.devices.show("invalid", target)


def test_user_device_delete():
    devices = user_handler.devices.lists("test2")
    assert user_handler.devices.delete("test2", devices[0]["device_id"])
    assert len(user_handler.devices.lists("test2")) == 3
    assert user_handler.devices.delete("test2", [devices[1]["device_id"]])
    assert len(user_handler.devices.lists("test2")) == 2
    with pytest.raises(SynapseException):
        user_handler.devices.delete("invalid", "invalid")


def test_user_device_delete_multiple():
    devices = user_handler.devices.lists("test2")
    delete_devices = []
    for device in devices:
        delete_devices.append(device["device_id"])
    assert user_handler.devices.delete("test2", delete_devices)
    with pytest.raises(SynapseException):
        user_handler.devices.delete("invalid", ["invalid", "invalid2"])


def test_user_username_available():
    assert not user_handler.username_available("test2")
    assert user_handler.username_available("test4")
    with pytest.raises(SynapseException):
        user_handler.username_available("invalid@@@#")


def test_user_registration_tokens_lists():
    assert user_handler.registration_tokens.lists() == []
    for _ in range(2):
        assert user_handler.registration_tokens.create()
    assert len(user_handler.registration_tokens.lists()) == 2
    assert user_handler.registration_tokens.create(
        expiry_time=Utility.get_current_time(5)
    )
    time.sleep(5)
    assert len(user_handler.registration_tokens.lists(True)) == 2
    assert len(user_handler.registration_tokens.lists(False)) == 1
    assert len(user_handler.registration_tokens.lists()) == 3


def test_user_registration_tokens_query():
    for token in user_handler.registration_tokens.lists():
        result = user_handler.registration_tokens.query(token["token"])
        assert result == token
    with pytest.raises(SynapseException):
        user_handler.registration_tokens.query("invalid")


def test_user_registration_tokens_create():
    result = user_handler.registration_tokens.create("testing", length=10)
    result2 = user_handler.registration_tokens.create("testing1")
    result2["token"] = "testing"
    assert result == result2
    assert result == {
        "token": "testing",
        "uses_allowed": None,
        "pending": 0,
        "completed": 0,
        "expiry_time": None
    }
    result = user_handler.registration_tokens.create(
        uses_allowed=10,
        length=10
    )
    assert len(result["token"]) == 10
    assert result["uses_allowed"] == 10
    expiry = Utility.get_current_time(3)
    result = user_handler.registration_tokens.create(
        expiry_time=expiry
    )
    assert result["expiry_time"] == expiry
    with pytest.raises(SynapseException):
        user_handler.registration_tokens.create("testing")


def test_user_registration_tokens_update():
    result = user_handler.registration_tokens.update(
        "testing",
        uses_allowed=12
    )
    assert result == {
        "token": "testing",
        "uses_allowed": 12,
        "pending": 0,
        "completed": 0,
        "expiry_time": None
    }
    expiry = Utility.get_current_time(120)
    result = user_handler.registration_tokens.update(
        "testing1",
        expiry_time=expiry
    )
    assert result == {
        "token": "testing1",
        "uses_allowed": None,
        "pending": 0,
        "completed": 0,
        "expiry_time": expiry
    }
    with pytest.raises(SynapseException):
        user_handler.registration_tokens.update("invalid", 20)


def test_user_registration_tokens_delete():
    total = len(user_handler.registration_tokens.lists())
    for token in user_handler.registration_tokens.lists():
        assert user_handler.registration_tokens.delete(token["token"])
        total -= 1
        assert total == len(user_handler.registration_tokens.lists())
    with pytest.raises(SynapseException):
        user_handler.registration_tokens.delete("invalid")
