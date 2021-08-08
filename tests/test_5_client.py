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
from synapse_admin.base import SynapseException
from synapse_admin.client import ClientAPI


with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
client_handler = ClientAPI(*conn)


def test_client_admin_login(monkeypatch):
    original = "getpass.getpass.__code__"
    replacement = (lambda _: "0123456789").__code__
    monkeypatch.setattr(original, replacement)

    token = ClientAPI.admin_login(
        "http://",
        "localhost",
        8008,
        "admin1",
        "0123456789",
    )
    assert isinstance(token, str) and token[:4] == "syt_"

    token = ClientAPI.admin_login(
        "http://",
        "localhost",
        8008,
        "test1",
        "123456789",
        no_admin=True
    )
    assert isinstance(token, str) and token[:4] == "syt_"

    token = ClientAPI.admin_login(
        "http://",
        "localhost",
        8008,
        "admin1"
    )
    assert isinstance(token, str) and token[:4] == "syt_"

    with pytest.raises(SynapseException):
        ClientAPI.admin_login(
            "http://",
            "localhost",
            8008,
            "test1",
            "123456789",
            no_admin=False
        )

        ClientAPI.admin_login(
            "http://",
            "localhost",
            8008,
            "admin1",
            "invalid"
        )
