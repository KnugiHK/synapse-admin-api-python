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

from synapse_admin.base import Admin, SynapseException, Utility, Contents
from typing import NamedTuple, Union


class Media(Admin):
    """
    Wapper class for admin API for media management

    Reference:
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/statistics.md
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md
    """

    order = {"user_id", "displayname", "media_length", "media_count"}

    class ListOfMedia(NamedTuple):
        local: list
        remote: list

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
        self._create_alias()

    def _create_alias(self) -> None:
        """Create alias for some methods"""
        self.lists = self.list = self.list_media
        self.protect = self.protect_media
        self.unprotect = self.unprotect_media

    def statistics(
        self,
        _from: int = None,
        limit: int = None,
        orderby: str = None,
        from_ts: int = None,
        until_ts: int = None,
        search: str = None,
        forward: bool = False
    ) -> Contents:
        """Query the media usage statistics

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/statistics.md#users-media-usage-statistics

        Args:
            _from (int, optional): equivalent to "from". Defaults to None.
            limit (int, optional): equivalent to "limit". Defaults to None.
            orderby (str, optional): equivalent to "order_by". Defaults to None.
            from_ts (int, optional): equivalent to "from_ts". Defaults to None.
            until_ts (int, optional): equivalent to "until_ts". Defaults to None.
            search (str, optional): equivalent to "search_term". Defaults to None.
            forward (bool, optional): equivalent to "dir". True to forward False to backward Defaults to False. # noqa: E501

        Returns:
            Contents: list of media usage per user
        """
        if forward:
            optional_str = "dir=f"
        else:
            optional_str = "dir=b"

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
            elif orderby not in Media.order:
                raise ValueError(
                    "Argument 'orderby' must be included in Media.order, "
                    "for details please read documentation."
                )
            optional_str += f"&orderby={orderby}"

        if from_ts:
            optional_str += f"&from_ts={from_ts}"

        if until_ts:
            optional_str += f"&until_ts={until_ts}"

        if search:
            optional_str += f"&search_term={search}"

        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/statistics/users/media?{optional_str}", 1),
        )
        data = resp.json()
        return Contents(
            data["users"],
            data["total"],
            data.get("next_token", None)
        )

    def list_media(self, roomid: str) -> ListOfMedia:
        """List all media in a specific room

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#list-all-media-in-a-room

        Args:
            roomid (str): the room you want to query

        Returns:
            ListOfMedia: local: list of local media, remote: list of remote media  # noqa: E501
        """
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/room/{roomid}/media", 1),
        )
        data = resp.json()
        return Media.ListOfMedia(data["local"], data["remote"])

    def quarantine_id(self, mediaid: str, server_name: str = None) -> bool:
        """Quarantine a media by its id

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#quarantining-media-by-id

        Args:
            mediaid (str): the media you want it to be quarantined
            server_name (str, optional): the source of the media. Defaults to your local server name (None). # noqa: E501

        Returns:
            bool: the operation is successful or not
        """
        if server_name is None:
            server_name = self.server_addr
        mediaid = self.extract_media_id(mediaid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(
                f"/media/quarantine/"
                f"{server_name}/{mediaid}",
                1
            ),
            json={},
        )
        return len(resp.json()) == 0

    def quarantine_room(self, roomid: str) -> int:
        """Quarantine all media in a room

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#quarantining-media-in-a-room

        Args:
            roomid (str): the room you want its media to be quarantined

        Returns:
            int: number of quarantined media
        """
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/room/{roomid}/media/quarantine", 1),
            json={},
        )
        return resp.json()["num_quarantined"]

    def quarantine_user(self, userid: str) -> int:
        """Quarantine all media sent by a specific user

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#quarantining-all-media-of-a-user

        Args:
            userid (str): the user you want their media to be quarantined

        Returns:
            int: number of quarantined media
        """
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/user/{userid}/media/quarantine", 1),
            json={},
        )
        return resp.json()["num_quarantined"]

    def quarantine_remove(self, mediaid: str, server_name: str = None) -> bool:
        """Remove a media from quarantine

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#remove-media-from-quarantine-by-id

        Args:
            mediaid (str): the media you want to remove from quarantine
            server_name (str, optional): the source of the media. Defaults to your local server name (None). # noqa: E501

        Returns:
            bool: the operation is successful or not
        """
        if server_name is None:
            server_name = self.server_addr
        mediaid = self.extract_media_id(mediaid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(
                f"/media/unquarantine/"
                f"{server_name}/{mediaid}",
                1
            ),
            json={},
        )
        return resp.json() == {}

    def protect_media(self, mediaid: str) -> bool:
        """Protect a media from being quarantined

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#protecting-media-from-being-quarantined

        Args:
            mediaid (str): the media you want to protect from quarantine

        Returns:
            bool: the operation is successful or not
        """
        mediaid = self.extract_media_id(mediaid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/media/protect/{mediaid}", 1),
            json={},
        )
        data = resp.json()
        if len(data) == 0:
            return True
        else:
            if self.suppress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def unprotect_media(self, mediaid: str) -> bool:
        """Remove quarantine protection for a media

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#unprotecting-media-from-being-quarantined

        Args:
            mediaid (str): the media you want to unprotect from quarantine

        Returns:
            bool: the operation is successful or not
        """
        mediaid = self.extract_media_id(mediaid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/media/unprotect/{mediaid}", 1),
            json={},
        )
        data = resp.json()
        if data == {}:
            return True
        else:
            if self.suppress_exception:
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
    ) -> Union[bool, int]:
        """Helper method for deleting both local and remote media

        Args:
            mediaid (str, optional): the media id that is intended for deletion. Defaults to None. # noqa: E501
            timestamp (int, optional): timestamp in millisecond. Defaults to None. # noqa: E501
            size_gt (int, optional): file size in byte. Defaults to None.
            keep_profiles (bool, optional): whether to keep media related to profiles. Defaults to None. # noqa: E501
            server_name (str, optional): designated homeserver address. Defaults to None. # noqa: E501
            remote (bool, optional): whether to delete remote media cache. Defaults to False. # noqa: E501

        Returns:
            If mediaid is not None return bool: the deletion is success or not
            If remote is False returns Contents: a list of deleted media
            If remote is True returns int: number of deleted media
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
            mediaid = self.extract_media_id(mediaid)
            return self.delete_local_media(mediaid, server_name)

        if timestamp or size_gt or keep_profiles:
            if timestamp is None:
                timestamp = Utility.get_current_time()
            if keep_profiles is None:
                keep_profiles = True
            if size_gt is None:
                size_gt = 0

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
    ) -> bool:
        """Delete a local media

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#delete-a-specific-local-media

        Args:
            mediaid (str): the media you want to delete
            server_name (str, optional): the source of the media. Defaults to your local server name (None). # noqa: E501

        Returns:
            str: the deletion is success or not
        """
        if server_name is None:
            server_name = self.server_addr
        mediaid = self.extract_media_id(mediaid)

        resp = self.connection.request(
            "DELETE",
            self.admin_patterns(f"/media/{server_name}/{mediaid}", 1),
            json={},
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["deleted_media"][0] == mediaid
        else:
            if self.suppress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete_local_media_by_condition(
        self,
        timestamp: int = Utility.get_current_time(),
        size_gt: int = 0,
        keep_profiles: bool = True,
        server_name: str = None
    ) -> Contents:
        """Delete local media with condition

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#delete-local-media-by-date-or-size

        Args:
            timestamp (int, optional): delete media sent before this timestamp. Defaults to Utility.get_current_time() (current time). # noqa: E501
            size_gt (int, optional): delete media in which their size are greater than this size in bytes. Defaults to None.
            keep_profiles (bool, optional): whether to keep profiles media or not. Defaults to True.
            server_name (str, optional): the source of the media. Defaults to your local server name (None).

        Returns:
            Contents: a list of deleted media
        """
        if server_name is None:
            server_name = self.server_addr

        optional_str = ""
        if keep_profiles:
            optional_str += "&keep_profiles=true"

        if size_gt < 0:
            raise ValueError("Argument 'size_gt' must be a positive integer")
        if not isinstance(timestamp, int):
            raise TypeError("Argument 'timestamp' must be an integer")

        resp = self.connection.request(
            "POST",
            self.admin_patterns(
                f"/media/{server_name}/delete?before_ts="
                f"{timestamp}&size_gt={size_gt}{optional_str}", 1
            ),
            json={},
        )
        data = resp.json()
        return Contents(data["deleted_media"], data["total"])

    def delete_media_by_user(
        self,
        userid: str,
        limit: int = 100,
        _from: int = 0,
        order_by: int = None,
        _dir: str = "f"
    ) -> Contents:
        """Delete local media uploaded by a specific user

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/user_admin_api.md#delete-media-uploaded-by-a-user
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/user_admin_api.md#list-media-uploaded-by-a-user

        Args:
            userid (str): the user you want to delete their uploaded media
            limit (int, optional): equivalent to "limit". Defaults to 100.
            _from (int, optional): equivalent to "from". Defaults to 0.
            order_by (int, optional): equivalent to "order_by". Defaults to None. # noqa: E501
            _dir (str, optional): equivalent to "dir". Defaults to "f".

        Returns:
            Contents: list of media deleted
        """
        userid = self.validate_username(userid)
        optional_str = ""
        if order_by is not None:
            optional_str += f"&order_by={order_by}"
        resp = self.connection.request(
            "DELETE",
            self.admin_patterns(
                f"/users/{userid}/media?"
                f"limit={limit}&from={_from}"
                f"&dir={_dir}{optional_str}", 1)
        )
        data = resp.json()
        if resp.status_code == 200:
            return Contents(data["deleted_media"], data["total"])
        else:
            if self.suppress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def purge_remote_media(
        self,
        timestamp: int = Utility.get_current_time()
    ) -> int:
        """Purge remote homeserver media

        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/media_admin_api.md#purge-remote-media-api

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
