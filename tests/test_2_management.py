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
from synapse_admin import Management, Room, User
from synapse_admin.base import HTTPConnection, SynapseException, Utility
from uuid import uuid4


with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
mgt_handler = Management(*conn)
room_handler = Room(*conn)
user_handler = User(*conn)
test1_conn = HTTPConnection(
    "http://",
    "localhost",
    8008,
    {"Authorization": f"Bearer {user_access_token}"}
)
test2_token = user_handler.login("test2")
test2_conn = HTTPConnection(
    "http://",
    "localhost",
    8008,
    {"Authorization": f"Bearer {test2_token}"}
)
shared_variable = []


def test_management_announce():
    """TODO: media announcement"""
    assert isinstance(mgt_handler.announce("test1", "This is a test"), str)
    assert isinstance(mgt_handler.announce("test1", "This is a test2"), str)
    assert isinstance(mgt_handler.announce("admin1", "This is a test"), str)


def test_management_announce_all():
    announcement = mgt_handler.announce_all("This is a test")
    assert isinstance(announcement, dict)
    assert len(announcement) == 3


def test_management_version():
    version = mgt_handler.version()
    assert hasattr(version, "server") and hasattr(version, "python")
    assert isinstance(version.server, str) and isinstance(version.python, str)


def create_report():
    roomid, _ = room_handler.create(False, members=["test1", "test2"])
    shared_variable.append(roomid)
    resp = test1_conn.request(
        "PUT",
        f"/_matrix/client/r0/rooms/{roomid}/send/m.room.message/{uuid4()}",
        {"msgtype": "m.text", "body": "Test, report this"}
    )
    test1_msgid = resp.json()["event_id"]
    shared_variable.append(test1_msgid)
    resp = test2_conn.request(
        "POST",
        f"/_matrix/client/r0/rooms/{roomid}/report/{test1_msgid}",
        {"score": -100, "reason": "Reporting"}
    )
    return resp.json()


def test_management_event_reports():
    assert create_report() == {}
    reports = mgt_handler.event_reports(0)
    assert reports == [] and reports.total == 1 and reports.next == 0
    reports = mgt_handler.event_reports(_from=reports.next)
    assert reports.next is None and len(reports) == 1
    report = reports[0]
    assert report["id"] == 2 and report["reason"] == "Reporting"


def test_management_specific_event_report():
    report = mgt_handler.specific_event_report(2)
    assert report["id"] == 2
    assert "event_json" in report
    with pytest.raises(SynapseException):
        mgt_handler.specific_event_report(1)


def test_management_purge_history():
    global shared_variable
    roomid, eventid = shared_variable
    shared_variable = []
    purgeid = mgt_handler.purge_history(roomid, eventid, True)
    assert isinstance(purgeid, str)
    time.sleep(1)
    shared_variable.append(purgeid)
    purgeid = mgt_handler.purge_history(
        roomid,
        Utility.get_current_time(),
        True
    )
    assert isinstance(purgeid, str)
    shared_variable.append(purgeid)
    with pytest.raises(SynapseException):
        purgeid = mgt_handler.purge_history("invalid", eventid, True)
        purgeid = mgt_handler.purge_history("invalid", "invalid", True)
        purgeid = mgt_handler.purge_history(roomid, "invalid", True)


def test_management_purge_history_status():
    purge1, purge2 = shared_variable
    assert mgt_handler.purge_history_status(purge1) == "complete"
    assert mgt_handler.purge_history_status(purge2) == "complete"
    with pytest.raises(SynapseException):
        mgt_handler.purge_history_status("invalid")


def create_group():
    resp = mgt_handler.connection.request(
        "POST",
        "/_matrix/client/r0/create_group",
        {"localpart": "test1", "profile": {"name": "Test"}}
    )
    return resp.json().get("group_id", None)


def test_management_delete_group():
    groupid = create_group()
    assert isinstance(groupid, str)
    _groupid = groupid[1:].replace(":localhost", "")
    assert mgt_handler.delete_group(_groupid)
    assert test1_conn.request(
        "GET",
        f"/_matrix/client/r0/groups/{groupid}/summary"
    ).status_code == 404
    with pytest.raises(SynapseException):
        mgt_handler.delete_group("+invalid:localhost")


def test_management_background_updates_get():
    enabled, _ = mgt_handler.background_updates_get()
    assert enabled


def test_management_background_updates_set():
    assert mgt_handler.background_updates_set(True)
    assert not mgt_handler.background_updates_set(False)
    enabled, _ = mgt_handler.background_updates_get()
    assert not enabled
    assert mgt_handler.background_updates_set(True)
    enabled, _ = mgt_handler.background_updates_get()
    assert enabled
