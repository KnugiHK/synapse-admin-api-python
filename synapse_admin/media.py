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


class Media(Admin):
    """
    Wapper class for admin API for media management

    Reference:
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/statistics.md
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md
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

    def statistics(self):
        self.connection.request(
            "GET",
            self.admin_patterns("/statistics/users/media", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        return data["users"], data["total"]

    def list_media(self, roomid):
        roomid = self.validate_room(roomid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/room/{roomid}/media", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        return data["local"], data["remote"]

    def quarantine_id(self, mediaid, server_name=None):
        if server_name is None:
            server_name = self.server_addr
        self.connection.request(
            "POST",
            self.admin_patterns(
                f"/media/quarantine/"
                f"{server_name}/{mediaid}", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        if len(json.loads(resp.read())) == 0:
            return True
        return False

    def quarantine_room(self, roomid):
        roomid = self.validate_room(roomid)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/room/{roomid}/media/quarantine", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())["num_quarantined"]

    def quarantine_user(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/user/{userid}/media/quarantine", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())["num_quarantined"]

    def protect_media(self, mediaid):
        self.connection.request(
            "POST",
            self.admin_patterns(f"/media/protect/{mediaid}", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if len(data) == 0:
            return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete_local_media(self, mediaid, server_name=None):
        if server_name is None:
            server_name = self.server_addr

        self.connection.request(
            "DELETE",
            self.admin_patterns(f"/media/{server_name}/{mediaid}", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data["deleted_media"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete_local_media_by_condition(
        self,
        timestamp=Admin.get_current_time(),
        size_gt=None,
        keep_profiles=True,
        server_name=None
    ):
        if server_name is None:
            server_name = self.server_addr

        optional_str = ""
        if keep_profiles:
            optional_str += "&keep_profiles=true"

        if size_gt is not None:
            if size_gt < 0:
                raise ValueError(
                    "Argument 'size_gt' must "
                    "be a positive integer"
                )
            optional_str += f"&size_gt={size_gt}"

        self.connection.request(
            "POST",
            self.admin_patterns(
                f"/media/{server_name}/delete?before_ts="
                f"{timestamp}{optional_str}", 1
            ),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        return data["deleted_media"], data["total"]

    def purge_remote_media(self, timestamp=Admin.get_current_time()):
        if not isinstance(timestamp, int):
            raise TypeError(
                "Argument 'timestamp' should be a "
                f"int but not {type(timestamp)}"
            )
        self.connection.request(
            "POST",
            self.admin_patterns(
                "/purge_media_cache?"
                f"before_ts={timestamp}", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())["deleted"]
