"""MIT License

Copyright (c) 2020 Knugi

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

from synapse_admin.base import Admin, SynapseException
import json


class Room(Admin):
    """
    Wapper class for admin API for room management

    Reference:
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md
    """

    order = {
        "alphabetical", "size", "name", "canonical_alias",
        "joined_members", "joined_local_members", "version",
        "creator", "encryption", "federatable", "public",
        "join_rules", "guest_access", "history_visibility", "state_events"
    }

    def __init__(self):
        super().__init__()

    # Not yet tested

    def lists(
        self,
        _from=None,
        limit=None,
        orderby=None,
        recent_first=True,
        search=None
    ):
        if recent_first:
            optional_str = "dir=b"
        else:
            optional_str = "dir=f"

        if _from is not None:
            optional_str += f"&from={_from}"

        if limit is not None:
            optional_str += f"&limit={limit}"

        if orderby is not None:
            if not isinstance(orderby, str):
                raise TypeError(
                    "Argument 'orderby' should be a "
                    f"str but not {type(orderby)}"
                )
            elif orderby not in Room.order:
                raise ValueError(
                    "Argument 'orderby' must be included in Room.order, "
                    "for details please read documentation."
                )
            optional_str += f"&orderby={orderby}"

        if search:
            optional_str += f"&search_term={search}"

        self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms?{optional_str}", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())

    def details(self, roomid):
        roomid = self.validate_room(roomid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms/{roomid}", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())

    def list_members(self, roomid):
        roomid = self.validate_room(roomid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms/{roomid}/members", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        return data["members"], data["total"]

    def delete(
        self,
        roomid,
        new_room_userid=None,
        new_room_name=None,
        message=None,
        block=False,
        purge=True
    ):
        roomid = self.validate_room(roomid)

        data = {"block": block, "purge": purge}
        if new_room_userid is not None:
            new_room_userid = self.validate_username(new_room_userid)
            data["new_room_user_id"] = new_room_userid
        if new_room_name is not None:
            data["room_name"] = new_room_name
        if message is not None:
            data["message"] = message

        self.connection.request(
            "POST",
            self.admin_patterns(f"/rooms/{roomid}/delete", 1),
            body=json.dumps(data),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())

    def set_admin(self, roomid, userid):
        roomid = self.validate_room(roomid)
        userid = self.validate_username(userid)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/rooms/{roomid}/make_room_admin", 1),
            body=json.dumps({"user_id": userid}),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())
