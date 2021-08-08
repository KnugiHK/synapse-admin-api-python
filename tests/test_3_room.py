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
from synapse_admin.base import SynapseException, HTTPConnection
from synapse_admin import Room


with open("synapse_test/admin.token", "r") as f:
    admin_access_token = f.read().replace("\n", "")

with open("synapse_test/user.token", "r") as f:
    user_access_token = f.read().replace("\n", "")


conn = ("localhost", 8008, admin_access_token, "http://")
room_handler = Room(*conn)
test1_conn = HTTPConnection(
    "http://",
    "localhost",
    8008,
    {"Authorization": f"Bearer {user_access_token}"}
)
shared_variable = None


def test_room_lists():
    rooms = room_handler.lists()
    assert rooms.total == 6
    assert len(rooms) == 6
    assert "room_id" in rooms[0]
    rooms = room_handler.lists(limit=1)
    assert rooms.total == 6
    assert rooms.next == 1


def test_room_details():
    roomid = room_handler.lists(limit=1)[0]["room_id"]
    room = room_handler.details(roomid)
    assert "avatar" in room and "topic" in room
    assert "joined_local_devices" in room
    with pytest.raises(SynapseException):
        room_handler.details("invalid")


def test_room_list_members():
    roomid = room_handler.lists(limit=1)[0]["room_id"]
    members_list = [
        '@admin1:localhost',
        '@test1:localhost',
        '@test2:localhost'
    ]
    assert room_handler.list_members(roomid) == members_list
    with pytest.raises(SynapseException):
        room_handler.list_members("invalid")


def test_room_forward_extremities_check():
    global shared_variable
    roomid = room_handler.lists()[1]["room_id"]
    shared_variable = roomid
    forward = room_handler.forward_extremities_check(roomid)
    assert len(forward) == 1
    assert "event_id" in forward[0]
    assert room_handler.forward_extremities_check("invalid") == []


def test_room_forward_extremities_delete():
    roomid = shared_variable
    assert room_handler.forward_extremities_delete(roomid) == 0  # Weird
    with pytest.raises(SynapseException):
        room_handler.forward_extremities_delete("invalid")
    assert len(room_handler.forward_extremities_check(roomid)) == 1


def test_room_create():
    """TODO: test encryption"""
    roomid, _ = room_handler.create(
        True,
        alias="testing",
        name="Testing",
        members=["test1"],
        federation=False,
        leave=True
    )
    global shared_variable
    shared_variable = roomid
    room = room_handler.details(roomid)
    assert room["canonical_alias"] == "#testing:localhost"
    assert room["name"] == "Testing"
    assert room["public"] and not room["federatable"]
    assert room_handler.list_members(roomid) == ['@test1:localhost']

    with pytest.raises(ValueError):
        room_handler.create(
            True,
            alias="testing",
            name="Testing",
            members=None,
            federation=False,
            leave=True
        )


def test_room_delete():
    global shared_variable
    roomid = shared_variable
    deleted = room_handler.delete(
        roomid,
        "@admin1:localhost",
        "Deleted",
        "A room deleted",
        True,
        True
    )
    assert deleted["kicked_users"] == ["@test1:localhost"]
    assert deleted["local_aliases"] == ["#testing:localhost"]
    with pytest.raises(SynapseException):
        room_handler.details(roomid)
    new_roomid = deleted["new_room_id"]
    shared_variable = new_roomid
    room = room_handler.details(new_roomid)
    assert room["name"] == "Deleted"
    members_list = ['@admin1:localhost', '@test1:localhost']
    assert room_handler.list_members(new_roomid) == members_list


def test_room_get_state():
    roomid = shared_variable
    room_state = room_handler.get_state(roomid)
    assert room_state[0]["type"] == "m.room.create"
    assert room_state[0]["room_id"] == roomid
    with pytest.raises(SynapseException):
        room_handler.get_state("invalid")


def test_room_set_admin():
    """TODO: test set_admin with userid=None"""
    roomid = shared_variable
    assert room_handler.set_admin(roomid, "test1")
    resp = test1_conn.request(
        "POST",
        f"/_matrix/client/r0/rooms/{roomid}/upgrade",
        {"new_version": "6"}
    )
    roomid = resp.json()["replacement_room"]


def test_room_event_context():
    roomid = shared_variable
    evenid = room_handler.get_state(roomid)[2]["event_id"]
    events = room_handler.event_context(roomid, evenid)["events_after"]
    assert len(events) > 2
    assert events[0]["room_id"] == roomid
