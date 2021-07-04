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

from synapse_admin import User
from synapse_admin.base import Admin, SynapseException
from typing import Tuple, Union


class Management(Admin):
    """
    Wapper class for admin API for server management

    Reference:
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/server_notices.md
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/version_api.md
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/register_api.md
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/purge_history_api.md
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/delete_group.md
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/event_reports.md
    """

    def __init__(
        self,
        server_addr=None,
        server_port=443,
        access_token=None,
        server_protocol=None,
        suppress_exception=False
    ):
        super().__init__(
            server_addr,
            server_port,
            access_token,
            server_protocol,
            suppress_exception
        )
        self.user = User()

    def announce(self, userid: str, announcement: str) -> str:
        """Send an announcement to a specific user

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/server_notices.md#server-notices

        Args:
            userid (str): the user that the announcement should be delivered to
            announcement (str): the announcement

        Returns:
            str: event id of the announcement
        """
        userid = self.validate_username(userid)
        data = {
            "user_id": userid,
            "content": {
                "msgtype": "m.text",
                "body": announcement
            }
        }
        resp = self.connection.request(
            "POST",
            self.admin_patterns("/send_server_notice", 1),
            json=data
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["event_id"]
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def announce_all(self, announcement: str) -> dict:
        """Send an announcement to all local users

        Args:
            announcement (str): the announcement

        Returns:
            dict: a dict with user id as key and the event id as value
        """
        users, _, _ = self.user.lists()
        events = {}
        for user in users:
            events[user["name"]] = self.announce(user["name"], announcement)
        return events

    def version(self) -> Tuple[str, str]:
        """Get the server and python version

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/version_api.md#version-api

        Returns:
            Tuple[str, str]: server version, python version
        """
        resp = self.connection.request(
            "GET",
            self.admin_patterns("/server_version", 1)
        )
        data = resp.json()
        return data["server_version"], data["python_version"]

    def purge_history(
        self,
        roomid: str,
        event_id_ts: Union[str, int],
        include_local_event: bool = False
    ) -> str:
        """Purge old events in a room from database

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/purge_history_api.md#purge-history-api

        Args:
            roomid (str): the room you want to perform the purging
            event_id_ts (Union[str, int]): purge up to an event id or timestamp
            include_local_event (bool, optional): whether to purge local events. Defaults to False. # noqa: E501

        Returns:
            str: purge id
        """
        roomid = self.validate_room(roomid)
        data = {"delete_local_events": include_local_event}
        if isinstance(event_id_ts, str):
            data["purge_up_to_event_id"] = event_id_ts
        elif isinstance(event_id_ts, int):
            data["purge_up_to_ts"] = event_id_ts
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/purge_history/{roomid}", 1),
            json=data
        )
        data = resp.json()["purge_id"]
        if resp.status_code == 200:
            return data
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def purge_history_status(self, purge_id: str) -> str:
        """Query the purge job status

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/purge_history_api.md#purge-status-query

        Args:
            purge_id (str): the purge id you want to query

        Returns:
            str: the status of the purge job
        """
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/purge_history_status/{purge_id}", 1)
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["status"]
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def event_reports(
        self,
        limit: int = 100,
        _from: int = 0,
        recent_first: bool = True,
        userid: str = None,
        roomid: str = None
    ) -> Tuple[dict, int, int]:
        """Query all reported events

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/event_reports.md#show-reported-events

        Args:
            limit (int, optional): equivalent to "limit". Defaults to 100.
            _from (int, optional): equivalent to "from". Defaults to 0.
            recent_first (bool, optional): equivalent to "dir". True as "b" False as "f" Defaults to True. # noqa: E501
            userid (str, optional): equivalent to "user_id". Defaults to None.
            roomid (str, optional): equivalent to "room_id". Defaults to None.

        Returns:
            Tuple[dict, int, int]: list of reported events, total number of returned reports, next token if presented
        """
        if recent_first:
            recent_first = "b"
        else:
            recent_first = "f"
        optional_str = ""
        if userid is not None:
            optional_str += f"&user_id={userid}"
        if roomid is not None:
            roomid = self.validate_room(roomid)
            optional_str += f"&room_id={roomid}"

        resp = self.connection.request(
            "GET",
            self.admin_patterns(
                f"/event_reports?from={_from}"
                f"&limit={limit}&dir={recent_first}"
                f"{optional_str}", 1
            )
        )
        data = resp.json()
        if data["total"] == 0:
            return None
        return (
            data["event_reports"],
            data["total"],
            data.get("next_token", None)
        )

    def specific_event_report(self, reportid: int) -> dict:
        """Query specific event report

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/event_reports.md#show-details-of-a-specific-event-report

        Args:
            reportid (int): the report id

        Returns:
            dict: a dict with all details of the report
        """
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/event_reports/{reportid}", 1)
        )
        data = resp.json()
        if resp.status_code == 200:
            return data
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete_group(self, groupid: str) -> bool:
        """Delete a local group

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/delete_group.md#delete-a-local-group

        Args:
            groupid (str): the group id you want to delete

        Returns:
            bool: the deletion is successful or not
        """
        groupid = self.validate_group(groupid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/delete_group/{groupid}", 1)
        )
        data = resp.json()
        if resp.status_code == 200:
            return data == {}
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])
