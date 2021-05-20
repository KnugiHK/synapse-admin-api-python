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


class Room(Admin):
    """
    Wapper class for admin API for room management

    Reference:
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md
    https://github.com/matrix-org/synapse/blob/master/docs/admin_api/shutdown_room.md
    https://github.com/matrix-org/synapse/blob/master/docs/admin_api/purge_room.md
    """

    order = {
        "alphabetical", "size", "name", "canonical_alias",
        "joined_members", "joined_local_members", "version",
        "creator", "encryption", "federatable", "public",
        "join_rules", "guest_access", "history_visibility", "state_events"
    }

    def __init__(
        self,
        server_addr=None,
        server_port=443,
        access_token=None,
        suppress_exception=False
    ):
        super().__init__(
            server_addr,
            server_port,
            access_token,
            suppress_exception
        )

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

        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms?{optional_str}", 1),
        )
        data = resp.json()
        if resp.status_code == 200:
            return data
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def details(self, roomid):
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms/{roomid}", 1),
        )
        data = resp.json()
        if resp.status_code == 200:
            return data
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def list_members(self, roomid):
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms/{roomid}/members", 1),
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["members"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete(
        self,
        roomid,
        new_room_userid=None,
        room_name=None,
        message=None,
        block=False,
        purge=True
    ):
        roomid = self.validate_room(roomid)
        data = {"block": block, "purge": purge}
        if new_room_userid is not None:
            new_room_userid = self.validate_username(new_room_userid)
            data["new_room_user_id"] = new_room_userid
        if room_name is not None:
            data["room_name"] = room_name
        if message is not None:
            data["message"] = message

        resp = self.connection.request(
            "DELETE",
            self.admin_patterns(f"/rooms/{roomid}", 1),
            json=data,
        )
        data = resp.json()
        if resp.status_code == 200:
            return data
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete_old(
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

        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/rooms/{roomid}/delete", 1),
            json=data
        )
        data = resp.json()
        if resp.status_code == 200:
            return data
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def set_admin(self, roomid, userid):
        roomid = self.validate_room(roomid)
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/rooms/{roomid}/make_room_admin", 1),
            json={"user_id": userid}
        )
        data = resp.json()
        if resp.status_code == 200:
            return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def purge_room(self, roomid):
        # Deprecated in the future (will not be tested)
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns("/purge_room", 1),
            json={"room_id": roomid}
        )
        return resp.json()

    def shutdown_room(
        self,
        roomid,
        new_room_userid,
        new_room_name=None,
        message=None
    ):  # Deprecated in the future (will not be tested)
        roomid = self.validate_room(roomid)
        new_room_userid = self.validate_username(new_room_userid)
        data = {"new_room_user_id": new_room_userid}

        if new_room_name is not None:
            data["room_name"] = new_room_name
        if message is not None:
            data["message"] = message

        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/shutdown_room/{roomid}", 1),
            json=data,
        )
        return resp.json()

    def forward_extremities_check(self, roomid):
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms/{roomid}/forward_extremities", 1)
        )
        data = resp.json()
        return data["results"], data["count"]

    def forward_extremities_delete(self, roomid):
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "DELETE",
            self.admin_patterns(f"/rooms/{roomid}/forward_extremities", 1)
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["deleted"]
        else:
            # Synapse bug: Internal server error
            # raise if the room does not exist
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def get_state(self, roomid):
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms/{roomid}/state", 1),
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["state"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def event_context(self, roomid, event_id):
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms/{roomid}/context/{event_id}", 1),
        )
        data = resp.json()
        if resp.status_code == 200:
            return data
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])
