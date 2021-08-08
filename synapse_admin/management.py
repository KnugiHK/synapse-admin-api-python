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
import os
from synapse_admin import User
from synapse_admin.base import Admin, SynapseException, Contents
from synapse_admin.client import ClientAPI
from typing import NamedTuple, Union, Tuple


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

    class SynapseVersion(NamedTuple):
        server: str
        python: str

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
        if server_addr is not None and access_token is not None:
            self.user = User(
                server_addr,
                server_port,
                access_token,
                server_protocol,
                suppress_exception
            )
            self.client = ClientAPI(
                server_addr,
                server_port,
                access_token,
                server_protocol,
                suppress_exception
            )
        else:
            self.user = User()
            self.client = ClientAPI()
        self._create_alias()

    def _create_alias(self) -> None:
        """Create alias for some methods"""
        self.event_report = self.specific_event_report

    def _prepare_attachment(
        self,
        attachment: Union[str, bytes]
    ) -> Tuple[str, str, str]:
        """Upload a media and return its information

        Args:
            attachment (Union[str, bytes]): the media, either in str or bytes

        Returns:
            Tuple[str, str, str]: media id, message type defined in matrix, file name  # noqa: E501
        """
        mediaid, mime = self.client.client_upload_attachment(attachment)
        if isinstance(attachment, bytes):
            filename = "unknown"
        else:
            filename = os.path.basename(attachment)
        if "image/" in mime:
            msgtype = "m.image"
        elif "video/" in mime:
            msgtype = "m.video"
        elif "audio/" in mime:
            msgtype = "m.audio"
        else:
            msgtype = "m.file"

        return mediaid, msgtype, filename

    def announce(
        self,
        userid: Union[str, bool],
        announcement: str = None,
        attachment: Union[str, bytes] = None
    ) -> Union[str, list]:
        """Send an announcement to a user or a batch of users

        Args:
            userid (Union[str, bool]): user you want to send them annoucement or set True to send the announcement to all users  # noqa: E501
            announcement (str, optional): a text-based announcement. Defaults to None.
            attachment (Union[str, bytes], optional): the media you want to send or to attach. Either provide a path to the file or the stream. Defaults to None.

        Returns:
            Union[str, list]: if either announcement or attachment is specified, return the event id
                if both announcement and attachment are specified, return a list which contains the event id for the attachment and the text
        """
        if isinstance(userid, str):
            invoking_method = self._announce
        elif isinstance(userid, bool) and userid:
            invoking_method = self.announce_all
            raise ValueError("Argument must be a non-empty str or True")
        if announcement is None and attachment is None:
            raise ValueError(
                "You must at least specify"
                "announcement or attachment"
            )
        userid = self.validate_username(userid)
        if attachment is not None:
            mediaid, msgtype, filename = self._prepare_attachment(
                attachment
            )
            data = {
                "user_id": userid,
                "content": {
                    "body": filename,
                    "msgtype": msgtype,
                    "url": mediaid
                }
            }
            if announcement is not None:
                event_ids = []
                event_ids.append(invoking_method(userid, "", data))
                event_ids.append(invoking_method(userid, announcement))
                return event_ids
            else:
                announcement = ""
        elif announcement is not None:
            data = None
        return invoking_method(userid, announcement, data)

    def _announce(
        self,
        userid: str,
        announcement: str,
        data: dict = None
    ) -> str:
        """Send an announcement to a specific user

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/server_notices.md#server-notices

        Args:
            userid (str): the user that the announcement should be delivered to
            announcement (str): the announcement

        Returns:
            str: event id of the announcement
        """
        userid = self.validate_username(userid)
        if data is None:
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
            if self.suppress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def announce_all(self, announcement: str, data: dict = None) -> dict:
        """Send an announcement to all local users

        Args:
            announcement (str): the announcement

        Returns:
            dict: a dict with user id as key and the event id as value
        """
        events = {}
        for user in self.user.lists():
            events[user["name"]] = self._announce(
                user["name"],
                announcement,
                data
            )
        return events

    def version(self) -> SynapseVersion:
        """Get the server and python version

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/version_api.md#version-api

        Returns:
            SynapseVersion: server: server version, python: python version  # noqa: E501
        """
        resp = self.connection.request(
            "GET",
            self.admin_patterns("/server_version", 1)
        )
        data = resp.json()
        return Management.SynapseVersion(
            data["server_version"],
            data["python_version"]
        )

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
        data = resp.json()
        if resp.status_code == 200:
            return data["purge_id"]
        else:
            if self.suppress_exception:
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
            if self.suppress_exception:
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
    ) -> Contents:
        """Query all reported events

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/event_reports.md#show-reported-events

        Args:
            limit (int, optional): equivalent to "limit". Defaults to 100.
            _from (int, optional): equivalent to "from". Defaults to 0.
            recent_first (bool, optional): equivalent to "dir". True as "b" False as "f" Defaults to True. # noqa: E501
            userid (str, optional): equivalent to "user_id". Defaults to None.
            roomid (str, optional): equivalent to "room_id". Defaults to None.

        Returns:
            Contents: list of reported events
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
        return Contents(
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
            if self.suppress_exception:
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
            if self.suppress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])
