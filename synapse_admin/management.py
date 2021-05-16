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
import json


class Management(Admin):
    """
    Wapper class for admin API for server management

    Reference:
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/server_notices.md
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/version_api.rst
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/register_api.rst
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/purge_history_api.rst
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/delete_group.md
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/event_reports.md
    """

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
        self.user = User()

    def announce(self, user, announcement):
        user = self.validate_username(user)
        data = {
            "user_id": user,
            "content": {
                "msgtype": "m.text",
                "body": announcement
            }
        }
        self.connection.request(
            "POST",
            self.admin_patterns("/send_server_notice", 1),
            body=json.dumps(data),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data["event_id"]
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def announce_all(self, announcement):
        # Not a standard API
        users, _ = self.user.lists()
        for user in users:
            self.announce(user["name"], announcement)

    def version(self):
        self.connection.request(
            "GET",
            self.admin_patterns("/server_version", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        return data["server_version"], data["python_version"]

    def purge_history(self, roomid, event_id_ts, include_local_event=False):
        roomid = self.validate_room(roomid)
        data = {"delete_local_events": include_local_event}
        if isinstance(event_id_ts, str):
            data["purge_up_to_event_id"] = event_id_ts
        elif isinstance(event_id_ts, int):
            data["purge_up_to_ts"] = event_id_ts
        self.connection.request(
            "POST",
            self.admin_patterns(f"/purge_history/{roomid}", 1),
            body=json.dumps(data),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())["purge_id"]
        if resp.status == 200:
            return data
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def purge_history_status(self, purge_id):
        self.connection.request(
            "GET",
            self.admin_patterns(f"/purge_history_status/{purge_id}", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data["status"]
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def event_reports(
        self,
        limit=100,
        _from=0,
        recent_first=True,
        userid=None,
        roomid=None
    ):
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

        self.connection.request(
            "GET",
            self.admin_patterns(
                f"/event_reports?from={_from}"
                f"&limit={limit}&dir={recent_first}"
                f"{optional_str}", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if data["total"] == 0:
            return None
        return data["event_reports"], data["total"]

    def specific_event_report(self, reportid):
        self.connection.request(
            "GET",
            self.admin_patterns(f"/event_reports/{reportid}", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete_group(self, groupid):
        self.connection.request(
            "POST",
            self.admin_patterns(f"/delete_group/{groupid}", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())
