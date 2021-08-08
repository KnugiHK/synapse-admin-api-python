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

import os
import pytest
import time
from httpx import ConnectError
from pathlib import Path
from synapse_admin import User
from synapse_admin.base import Admin, Client, Utility, Contents


with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
base_handler = Admin(*conn)
client_handler = Client(
    headers={
        "Authorization": f"Bearer {admin_access_token}",
        "User-Agent": "matrix-synpase-admin-python/test"
    }
)
server_part = "http://localhost:8008"
config_path = f"{str(Path.home())}/api.cfg"


def test_utility_get_bool():
    assert Utility.get_bool(True) == "true"
    assert Utility.get_bool(False) == "false"
    with pytest.raises(TypeError):
        Utility.get_bool("True")
        Utility.get_bool(0)


def test_utility_get_current_time():
    assert Utility.get_current_time() // 1000 == int(time.time())


def test_utility_get_password(monkeypatch):
    original = "getpass.getpass.__code__"
    replacement = (lambda _: "password123").__code__
    monkeypatch.setattr(original, replacement)
    assert Utility.get_password() == "password123"


def test_base_contents():
    contens = Contents([1, 2, 3, 4], 4, 5)
    assert contens.total == 4
    assert contens.next == 5
    with pytest.raises(TypeError):
        contens = Contents("Invalid")


def test_base_create_config():
    """TODO: interactive"""
    base_handler.config_path = config_path
    if os.path.isfile(config_path):
        os.remove(config_path)
    assert base_handler.create_config(
        "http://",
        "localhost",
        8008,
        admin_access_token,
        True
    )
    assert os.path.isfile(config_path)
    assert isinstance(User().lists(), Contents)
    os.remove(config_path)

    assert base_handler.create_config(
        "http://",
        "localhost",
        8008,
        admin_access_token,
        False
    )
    assert not os.path.isfile(config_path)

    assert base_handler.create_config(
        "http://",
        "localhost",
        8008,
        admin_access_token,
        True
    )
    assert os.path.isfile(config_path)


def test_base_modify_config():
    user = User()
    user.modify_config("invalid", 80, "invalid", "http://", False)
    with pytest.raises(ConnectError):
        user.lists()
    assert isinstance(User().lists(), Contents)
    user.modify_config("invalid", 80, "invalid", "http://", True)
    with pytest.raises(ConnectError):
        user.lists()
        User().lists()
    assert user.modify_config(
        "localhost",
        8008,
        admin_access_token,
        "http://"
    )
    assert isinstance(user.lists(), Contents)
    assert isinstance(User().lists(), Contents)


def test_base_read_config():
    user = User()
    user.config_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "../synapse_test/api.cfg"
    )
    user.modify_config("invalid", 80, "invalid", "http://", True)
    user.read_config(user.config_path)
    assert user.server_addr == "invalid"
    assert user.server_port == 80
    assert user.access_token == "invalid"


def test_base_validate_server():
    validate_server = base_handler.validate_server
    assert validate_server("server") == "server:localhost"
    assert validate_server("server:localhost") == "server:localhost"


def test_base_validate_username():
    validate_username = base_handler.validate_username
    assert validate_username("username") == "@username:localhost"
    assert validate_username("@username") == "@username:localhost"
    assert validate_username("username:localhost") == "@username:localhost"
    assert validate_username("@username:localhost") == "@username:localhost"


def test_base_validate_room():
    validate_room = base_handler.validate_room
    assert validate_room("room") == "!room:localhost"
    assert validate_room("!room") == "!room:localhost"
    assert validate_room("room:localhost") == "!room:localhost"
    assert validate_room("!room:localhost") == "!room:localhost"


def test_base_validate_group():
    validate_group = base_handler.validate_group
    assert validate_group("group") == "+group:localhost"
    assert validate_group("+group") == "+group:localhost"
    assert validate_group("group:localhost") == "+group:localhost"
    assert validate_group("+group:localhost") == "+group:localhost"


def test_base_validate_alias():
    validate_alias = base_handler.validate_alias
    assert validate_alias("alias") == "#alias:localhost"
    assert validate_alias("#alias") == "#alias:localhost"
    assert validate_alias("alias:localhost") == "#alias:localhost"
    assert validate_alias("#alias:localhost") == "#alias:localhost"


def test_base_admin_patterns():
    expect = "/_synapse/admin/v1/foo/bar"
    assert base_handler.admin_patterns("foo/bar", 1) == expect
    assert base_handler.admin_patterns("/foo/bar", 1) == expect


def test_base_httpconnection_delete():
    path = base_handler.admin_patterns('/media/localhost/fakeid', 1)
    assert client_handler.request(
        "DELETE",
        f"{server_part}{path}"
    ).status_code == 404

    path = base_handler.admin_patterns('/media/localhost/fakeid', 1)
    assert client_handler.request(
        "DELETE",
        f"{server_part}{path}",
        json={}
    ).status_code == 404


def test_base_httpconnection_get():
    path = base_handler.admin_patterns('/server_version', 1)
    assert client_handler.request(
        "GET",
        f"{server_part}{path}"
    ).status_code == 200


def test_base_httpconnection_post():
    path = base_handler.admin_patterns(
        "/deactivate/@invalid:localhost",
        1
    )
    assert client_handler.request(
        "POST",
        f"{server_part}{path}"
    ).status_code == 404


def test_base_httpconnection_put():
    path = base_handler.admin_patterns(
        "/users/@invalid:localhost/devices/INVALID",
        2
    )
    assert client_handler.request(
        "PUT",
        f"{server_part}{path}",
        json={"displayname": "invalid"}
    ).status_code == 404
