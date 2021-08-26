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

import mimetypes
import time
from synapse_admin.base import Admin, SynapseException, Utility
from synapse_admin import User
from typing import Tuple, Union


class ClientAPI(Admin):
    """Matrix client APIs wrapper (Maybe I should use matrix-python-sdk)

    References:
        https://github.com/matrix-org/matrix-python-sdk/blob/master/matrix_client/api.py#L192
        https://github.com/matrix-org/matrix-python-sdk/blob/master/matrix_client/api.py#L527
    """

    BASE_PATH = "/_matrix/client/r0"

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
        self._create_alias()

    def _create_alias(self) -> None:
        """Create alias for some methods"""
        self.client_create = self.client_create_room
        self.client_leave = self.client_leave_room

    def client_create_room(
        self,
        public: bool = False,
        alias: str = None,
        name: str = None,
        invite: Union[str, list] = None,
        federation: bool = True,
        encrypted: bool = True
    ) -> str:
        """Create a room as a client

        Args:
            public (bool, optional): is the room public. Defaults to False.
            alias (str, optional): alias of the room. Defaults to None.
            name (str, optional): name of the room. Defaults to None.
            invite (Union[str, list], optional): list of members. Defaults to None. # noqa: E501
            federation (bool, optional): allow federation. Defaults to True.
            encrypted (bool, optional): create encrypted room or not. Defaults to True

        Returns:
            str: created room id
        """
        data = {}
        if public:
            data["visibility"] = "public"
        else:
            data["visibility"] = "private"
        if alias is not None:
            data["room_alias_name"] = alias
        if name is not None:
            data["name"] = name
        if invite is not None:
            if isinstance(invite, str):
                validated_invite = [self.validate_username(invite)]
            elif isinstance(invite, list):
                validated_invite = []
                for user in invite:
                    validated_invite.append(self.validate_username(user))
            else:
                raise TypeError("Argument invite must be str or list.")
            data["invite"] = validated_invite
        data["creation_content"] = {"m.federate": federation}
        if encrypted:
            data["initial_state"] = [{
                "type": "m.room.encryption",
                "state_key": "",
                "content": {"algorithm": "m.megolm.v1.aes-sha2"}
            }]

        while True:
            resp = self.connection.request(
                "POST",
                f"{ClientAPI.BASE_PATH}/createRoom",
                json=data
            )
            data = resp.json()
            if "errcode" in data and data["errcode"] == "M_LIMIT_EXCEEDED":
                time.sleep(data["retry_after_ms"] / 1000)
                continue
            if resp.status_code == 200:
                return data["room_id"]
            else:
                if self.suppress_exception:
                    return False, data
                else:
                    raise SynapseException(data["errcode"], data["error"])

    def client_leave_room(self, roomid: str) -> bool:
        """leave a room as a client

        Args:
            roomid (str): the id of room which the client want to leave

        Returns:
            bool: success or not
        """
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "POST",
            f"{ClientAPI.BASE_PATH}/rooms/{roomid}/leave",
            json={}
        )
        data = resp.json()
        if resp.status_code == 200:
            if len(data) == 0:
                return True
            else:
                return data
        else:
            if self.suppress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def client_upload_attachment(
        self,
        attachment: Union[str, bytes]
    ) -> Tuple[str, str]:
        """Upload media as a client

        Args:
            attachment (Union[str, bytes]): path to the attachment or the attachment in bytes  # noqa: E501

        Returns:
            Tuple[str, str]: media mxc url, mime type
        """
        content_type = "application/octet-stream"
        if isinstance(attachment, str):
            guess, _ = mimetypes.guess_type(attachment)
            if guess:
                content_type = guess
            with open(attachment, "rb",) as f:
                attachment = f.read()
        elif isinstance(attachment, bytes):
            guess = Utility.guess_type(attachment)
            if guess:
                content_type = guess
        else:
            raise TypeError("Argument attachment must be str or bytes")

        resp = self.connection.request(
            "POST",
            "/_matrix/media/r0/upload",
            content=attachment,
            headers={"Content-Type": content_type}
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["content_uri"], content_type
        else:
            if self.suppress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    @staticmethod
    def admin_login(
        protocol: str,
        host: str,
        port: str,
        username: str = None,
        password: str = None,
        suppress_exception: bool = False,
        no_admin: bool = False
    ) -> str:
        """Login and get an access token

        Args:
            protocol (str): "http://" or "https://". Defaults to None. # noqa: E501
            host (str): homeserver address. Defaults to None.
            port (int): homeserver listening port. Defaults to None.
            username (str, optional): just username. Defaults to None.
            password (str, optional): just password. Defaults to None.
            suppress_exception (bool, optional): suppress exception or not, if not return False and the error in dict. Defaults to False. # noqa: E501

        Returns:
            str: access token
        """
        if username is None:
            username = input("Enter a username: ")
        if password is None:
            password = Utility.get_password(validate=False)
        from httpx import Client
        login_data = {
            "identifier": {
                "type": "m.id.user",
                "user": username
            },
            "type": "m.login.password",
            "password": password,
            "initial_device_display_name": "matrix-synapse-admin"
        }
        http = Client()
        base_url = f"{protocol}{host}:{port}"
        resp = http.post(
            f"{base_url}{ClientAPI.BASE_PATH}/login",
            json=login_data
        )
        data = resp.json()
        if resp.status_code == 200:
            access_token = data["access_token"]
            if not no_admin:
                resp = User(
                    host,
                    port,
                    access_token,
                    protocol
                ).query(username)
                if "errcode" not in resp:
                    return data["access_token"]
                else:
                    data = resp
            else:
                return access_token
        if suppress_exception:
            return False, data
        else:
            raise SynapseException(data["errcode"], data["error"])
