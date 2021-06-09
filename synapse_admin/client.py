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

from synapse_admin.base import Admin, SynapseException, Utility
from synapse_admin import User
from typing import Union


class ClientAPI(Admin):
    """Matrix client APIs wrapper (Maybe I should use matrix-python-sdk)"""

    base_path = "/_matrix/client/r0"

    def client_create(
        self,
        public: bool = False,
        alias: str = None,
        name: str = None,
        invite: Union[str, list] = None,
        federation: bool = True
    ) -> str:
        """Create a room as a client

        Args:
            public (bool, optional): is the room public. Defaults to False.
            alias (str, optional): alias of the room. Defaults to None.
            name (str, optional): name of the room. Defaults to None.
            invite (Union[str, list], optional): list of members. Defaults to None. # noqa: E501
            federation (bool, optional): allow federation. Defaults to True.

        Returns:
            str: created room id
        """
        data = {}
        if public:
            data["visibility"] = "public"
        else:
            data["visibility"] = "private"
        if alias is not None:
            data["roo_alias_name"] = alias
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

        resp = self.connection.request(
            "POST",
            f"{ClientAPI.base_path}/createRoom",
            json=data
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["room_id"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def client_leave(self, roomid: str) -> bool:
        """leave a room as a client

        Args:
            roomid (str): the id of room which the client want to leave

        Returns:
            bool: succuess or not
        """
        roomid = self.validate_room(roomid)
        resp = self.connection.request(
            "POST",
            f"{ClientAPI.base_path}/rooms/{roomid}/leave",
            json={}
        )
        data = resp.json()
        if resp.status_code == 200:
            if len(data) == 0:
                return True
            else:
                return data
        else:
            if self.supress_exception:
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
        supress_exception: bool = False
    ) -> str:
        """Login and get an access token

        Args:
            protocol (str): "http://" or "https://". Defaults to None. # noqa: E501
            host (str): homeserver address. Defaults to None.
            port (int): homeserver listening port. Defaults to None.
            username (str, optional): just username. Defaults to None.
            password (str, optional): just password. Defaults to None.
            supress_exception (bool, optional): supress exception or not, if not return False and the error in dict. Defaults to False. # noqa: E501

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
            f"{base_url}{ClientAPI.base_path}/login",
            json=login_data
        )
        data = resp.json()
        if resp.status_code == 200:
            access_token = data["access_token"]
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
        if supress_exception:
            return False, data
        else:
            raise SynapseException(data["errcode"], data["error"])
