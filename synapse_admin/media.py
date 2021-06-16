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

from synapse_admin.base import Admin, SynapseException, Utility
from typing import Tuple, Union


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

    def statistics(self):
        resp = self.connection.request(
            "GET",
            self.admin_patterns("/statistics/users/media", 1),
        )
        data = resp.json()
        return data["users"], data["total"]

    def list_media(self, roomid: str) -> Tuple[list, list]:
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/room/{roomid}/media", 1),
        )
        data = resp.json()
        return data["local"], data["remote"]

    def quarantine_id(self, mediaid: str, server_name: str = None) -> bool:
        if server_name is None:
            server_name = self.server_addr
        resp = self.connection.request(
            "POST",
            self.admin_patterns(
                f"/media/quarantine/"
                f"{server_name}/{mediaid}",
                1
            ),
            json={},
        )
        if len(resp.json()) == 0:
            return True
        return False

    def quarantine_room(self, roomid: str) -> int:
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/room/{roomid}/media/quarantine", 1),
            json={},
        )
        return resp.json()["num_quarantined"]

    def quarantine_user(self, userid: str) -> int:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/user/{userid}/media/quarantine", 1),
            json={},
        )
        return resp.json()["num_quarantined"]

    def quarantine_remove(self, mediaid: str, server_name: str = None) -> bool:
        if server_name is None:
            server_name = self.server_addr
        resp = self.connection.request(
            "POST",
            self.admin_patterns(
                f"/media/unquarantine/"
                f"{server_name}/{mediaid}",
                1
            ),
            json={},
        )
        if resp.json() == {}:
            return True
        return False

    def protect_media(self, mediaid: str) -> bool:
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/media/protect/{mediaid}", 1),
            json={},
        )
        data = resp.json()
        if len(data) == 0:
            return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def unprotect_media(self, mediaid: str) -> bool:
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/media/unprotect/{mediaid}", 1),
            json={},
        )
        data = resp.json()
        if data == {}:
            return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete_media(
        self,
        mediaid: str = None,
        *,
        timestamp: int = None,
        size_gt: int = None,
        keep_profiles: bool = None,
        server_name: str = None,
        remote: bool = False
    ) -> Union[Tuple[list, int], int]:
        """Helper method for deleting both local and remote media

        Args:
            mediaid (str, optional): the media id that is intended for deletion. Defaults to None. # noqa: E501
            timestamp (int, optional): timestamp in millisecond. Defaults to None. # noqa: E501
            size_gt (int, optional): file size in byte. Defaults to None.
            keep_profiles (bool, optional): whether to keep media related to profiles. Defaults to None. # noqa: E501
            server_name (str, optional): designated homeserver address. Defaults to None. # noqa: E501
            remote (bool, optional): whether to delete remote media cache. Defaults to False. # noqa: E501

        Returns:
            If remote is True returns int: number of deleted media
            If remote is False returns Tuple[list, int]: list of deleted media id and their number in total
        """
        if mediaid and (timestamp or size_gt or keep_profiles):
            raise ValueError(
                "Argument mediaid cannot be mixed with "
                "timestamp, size_gt and keep_profiles"
            )

        if remote:
            if mediaid:
                print(
                    "WARNING! argument mediaid is"
                    "ignored when remote is True"
                )
            return self.purge_remote_media(Utility.get_current_time())

        if mediaid:
            return self.delete_local_media(mediaid, server_name)

        if timestamp or size_gt or keep_profiles:
            if timestamp is None:
                timestamp = Utility.get_current_time()
            if keep_profiles is None:
                keep_profiles = True

            return self.delete_local_media_by_condition(
                timestamp,
                size_gt,
                keep_profiles,
                server_name
            )

    def delete_local_media(
        self,
        mediaid: str,
        server_name: str = None
    ) -> Tuple[list, int]:
        if server_name is None:
            server_name = self.server_addr

        resp = self.connection.request(
            "DELETE",
            self.admin_patterns(f"/media/{server_name}/{mediaid}", 1),
            json={},
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["deleted_media"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete_local_media_by_condition(
        self,
        timestamp: int = Utility.get_current_time(),
        size_gt: int = None,
        keep_profiles: bool = True,
        server_name: str = None
    ) -> Tuple[list, int]:
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

        resp = self.connection.request(
            "POST",
            self.admin_patterns(
                f"/media/{server_name}/delete?before_ts="
                f"{timestamp}{optional_str}", 1
            ),
            json={},
        )
        data = resp.json()
        return data["deleted_media"], data["total"]

    def purge_remote_media(
        self,
        timestamp: int = Utility.get_current_time()
    ) -> int:
        """Purge remote homeserver media

        Args:
            timestamp (int, optional): timestamp in millisecond. Defaults to Utility.get_current_time(). # noqa: E501

        Returns:
            list: number of deleted media
        """
        if not isinstance(timestamp, int):
            raise TypeError(
                "Argument 'timestamp' should be an "
                f"int but not {type(timestamp)}"
            )
        resp = self.connection.request(
            "POST",
            self.admin_patterns(
                "/purge_media_cache?"
                f"before_ts={timestamp}",
                1
            ),
            json={},
        )
        return resp.json()["deleted"]
