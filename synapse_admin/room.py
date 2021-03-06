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
from synapse_admin import User
from synapse_admin.client import ClientAPI
from typing import Tuple


class Room(Admin):
    """
    Wapper class for admin API for room management

    Reference:
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md
        https://github.com/matrix-org/synapse/blob/master/docs/admin_api/shutdown_room.md
        https://github.com/matrix-org/synapse/blob/master/docs/admin_api/purge_room.md
        https://github.com/matrix-org/matrix-python-sdk/blob/master/matrix_client/api.py#L192
        https://github.com/matrix-org/matrix-python-sdk/blob/master/matrix_client/api.py#L527
    """

    order = {
        "alphabetical", "size", "name", "canonical_alias",
        "joined_members", "joined_local_members", "version",
        "creator", "encryption", "federatable", "public",
        "join_rules", "guest_access", "history_visibility", "state_events"
    }

    def __init__(
        self,
        server_addr: str = None,
        server_port: int = 443,
        access_token: str = None,
        server_protocol: str = None,
        suppress_exception: bool = False
    ):
        super().__init__(
            server_addr,
            server_port,
            access_token,
            server_protocol,
            suppress_exception
        )

        self.user = User()
        self.client_api = ClientAPI()

    def lists(
        self,
        _from: int = None,
        limit: int = None,
        orderby: str = None,
        recent_first: bool = True,
        search: str = None
    ) -> Tuple[list, int, str]:
        """List all local rooms

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#list-room-api

        Args:
            _from (int, optional): equivalent to "from". Defaults to None.
            limit (int, optional): equivalent to "limit". Defaults to None.
            orderby (str, optional): equivalent to "order_by". Defaults to None.
            recent_first (bool, optional): equivalent to "dir", True to f False to b. Defaults to True. # noqa: E501
            search (str, optional): equivalent to "search_term". Defaults to None.

        Returns:
            Tuple[list, int, str]: list of room, total number of returned rooms, next token
        """
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
            return (
                data["rooms"],
                data["total_rooms"],
                data.get("next_token", None)
            )
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def details(self, roomid: str) -> dict:
        """Query a room

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#room-details-api

        Args:
            roomid (str): the room you want to query

        Returns:
            dict: a dict containing the room's details
        """
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

    def list_members(self, roomid: str) -> Tuple[list, int]:
        """List all members in the room

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#room-members-api

        Args:
            roomid (str): the room you want to query

        Returns:
            Tuple[list, int]: a list of members, total number of members
        """
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

    def create(
        self,
        public: bool = False,
        *,
        alias: str = None,
        name: str = None,
        members: list = None,
        federation: bool = True,
        leave: bool = False
    ) -> Tuple[str, list]:
        """Create a room and force users to be a member

        Args:
            public (bool, optional): is the room public? Defaults to False.
            alias (str, optional): the alias of the room. Defaults to None.
            name (str, optional): the name of the room. Defaults to None.
            members (list, optional): a list of user that should be the members of the room. Defaults to None. # noqa: E501
            federation (bool, optional): can the room be federated. Defaults to True.
            leave (bool, optional): whether to leave the room yourself after the creation. Defaults to False.

        Returns:
            Tuple[str, list]: room id, a list of joined users
        """
        roomid = self.client_api.client_create(
            public,
            alias,
            name,
            federation=federation
        )
        joined = []
        for member in members:
            userid = self.validate_username(member)
            if self.user.join_room(userid, roomid):
                joined.append(userid)
        if leave:
            self.client_api.client_leave(roomid)
        return roomid, joined

    def delete(
        self,
        roomid: str,
        new_room_userid: str = None,
        room_name: str = None,
        message: str = None,
        block: bool = False,
        purge: bool = True
    ) -> dict:
        """Delete a room

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#delete-room-api

        Args:
            roomid (str): the room you want to delete
            new_room_userid (str, optional): equivalent to "new_room_user_id". Defaults to None. # noqa: E501
            room_name (str, optional): equivalent to "room_name". Defaults to None.
            message (str, optional): equivalent to "message". Defaults to None.
            block (bool, optional): equivalent to "block". Defaults to False.
            purge (bool, optional): whether or not to purge all information of the rooom from the database. Defaults to True.

        Returns:
            dict: a dict cotaining kicked_users, failed_tokick_users, local_aliases, new_room_id
        """
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
        roomid: str,
        new_room_userid: str = None,
        new_room_name: str = None,
        message: str = None,
        block: bool = False,
        purge: bool = True
    ):
        """Old room deletion method. Use the new one."""
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

    def set_admin(self, roomid: str, userid: str) -> bool:
        """Set a member to be the admin in the room

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#make-room-admin-api

        Args:
            roomid (str): the room you want to grant admin privilege to the user # noqa: E501
            userid (str): the user you wanted them as an admin in the room

        Returns:
            bool: The modification is successful or not
        """
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
        """Purge a room. Deprecated in the future (will not be tested)

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/purge_room.md
        """
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
    ):
        """Shut down a room. Deprecated in the future (will not be tested)

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/shutdown_room.md
        """
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

    def forward_extremities_check(self, roomid: str) -> Tuple[list, int]:
        """Query forward extremities in a room

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#check-for-forward-extremities

        Args:
            roomid (str): the room you want to query

        Returns:
            Tuple[list, int]: a list of forward extremities, number of forward extremities # noqa: E501
        """
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/rooms/{roomid}/forward_extremities", 1)
        )
        data = resp.json()
        return data["results"], data["count"]

    def forward_extremities_delete(self, roomid: str) -> int:
        """Delete forward extremities in a room

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#deleting-forward-extremities

        Args:
            roomid (str): the room you want the forward extremities to be deleted # noqa: E501

        Returns:
            int: number of forward extremities deleted
        """
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

    def get_state(self, roomid: str) -> list:
        """Query the room state

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#room-state-api

        Args:
            roomid (str): the room you want to query

        Returns:
            list: a list of state
        """
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

    def event_context(self, roomid: str, event_id: str) -> dict:
        """Query the context of an event

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/rooms.md#event-context-api

        Args:
            roomid (str): the room where the event exist
            event_id (str): the event you want to query

        Returns:
            dict: a dict with event context
        """
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
