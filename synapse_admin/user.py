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

import hashlib
import hmac
from synapse_admin.base import Admin, SynapseException, Utility
from typing import Union, Tuple


class User(Admin):
    """
    Wapper class for admin API for user management

    Reference:
    https://github.com/matrix-org/synapse/blob/master/docs/admin_api/user_admin_api.rst
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/account_validity.rst
    https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/room_membership.md
    """

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
        self.devices = _Device(self.server_addr, self.connection)
        self._create_alias()

    def _create_alias(self) -> None:
        self.creates = self.create  # For compatibility
        self.details = self.query
        self.modify = self.create

    def lists(
        self,
        offset: int = 0,
        limit: int = 100,
        userid: str = None,
        name: str = None,
        guests: bool = True,
        deactivated: bool = False,
        order_by: str = None
    ) -> Tuple[str, int]:
        optional_str = ""
        if userid is not None:
            userid = self.validate_username(userid)
            optional_str += f"&user_id={userid}"
        if name is not None:
            optional_str += f"&name={name}"
        if order_by is not None:
            optional_str += f"&order_by={order_by}"

        resp = self.connection.request(
            "GET",
            self.admin_patterns(
                f"/users?from={offset}&limit={limit}&guests="
                f"{Utility.get_bool(guests)}&deactivated="
                f"{Utility.get_bool(deactivated)}{optional_str}",
                2
            )
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["users"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def create(self, userid: str, **kwargs) -> bool:
        """Create or modify a user

        Args:
            userid (str): The user id of the user

        Extra Args (use by specifying the argument name):
            password (str)
            displayname (str)
            threepids (list)
            avatar_url (str)
            admin (str)
            deactivated (str)

        Returns:
            bool: The creation of user is successful or not
        """
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{userid}", 2),
            json=kwargs
        )
        if resp.status_code == 200 or resp.status_code == 201:
            return True
        else:
            data = resp.json()
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def query(self, userid: str) -> Union[list, dict]:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}", 2)
        )
        return resp.json()

    def active_sessions(self, userid: str) -> list:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/whois/{userid}", 1)
        )
        data = resp.json()["devices"][""]
        return data["sessions"][0]["connections"]

    def deactivate(self, userid: str, erase: bool = True) -> bool:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/deactivate/{userid}", 1),
            json={"erase": erase}
        )
        return resp.json()["id_server_unbind_result"] == "success"

    def reactivate(self, userid: str, password: str = None) -> bool:
        if password is None:
            password = Utility.get_password()
        if not isinstance(password, str):
            raise TypeError(
                "Argument 'password' should be a "
                f"string but not {type(password)}"
            )
        return self.modify(userid, password=password, deactivated=False)

    def reset_password(
        self,
        userid: str,
        password: str = None,
        logout: bool = True
    ) -> bool:
        userid = self.validate_username(userid)
        if password is None:
            password = Utility.get_password()
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/reset_password/{userid}", 1),
            json={"new_password": password, "logout_devices": logout}
        )
        if resp.status_code == 200:
            return True
        else:
            data = resp.json()
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def is_admin(self, userid: str) -> bool:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/admin", 1)
        )
        return resp.json()["admin"]

    def set_admin(self, userid: str, activate: bool = None) -> bool:
        if activate is None:
            activate = not self.is_admin(userid)
        elif not isinstance(activate, bool):
            raise TypeError(
                "Argument 'activate' only accept "
                f"boolean but not {type(activate)}."
            )
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{userid}/admin", 1),
            json={"admin": activate}
        )
        if resp.status_code == 200:
            return True
        else:
            data = resp.json()
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def joined_room(self, userid: str) -> Tuple[list, int]:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/joined_rooms", 1)
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["joined_rooms"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def join_room(self, userid: str, room: str) -> bool:
        userid = self.validate_username(userid)
        room = self.validate_room(room)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/join/{room}", 1),
            json={"user_id": userid}
        )
        data = resp.json()
        if resp.status_code == 200:
            if "room_id" in data and data["room_id"] == room:
                return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def validity(
        self,
        userid: str,
        expiration: int = 0,
        enable_renewal_emails: bool = True
    ) -> dict:
        if expiration is not None and not isinstance(expiration, int):
            raise TypeError(
                "Argument 'expiration' only accept "
                f"int but not {type(expiration)}."
            )

        userid = self.validate_username(userid)
        data = {
            "user_id": userid,
            "enable_renewal_emails": enable_renewal_emails,
            "expiration_ts": expiration
        }

        resp = self.connection.request(
            "POST",
            self.admin_patterns("/account_validity/validity", 1),
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

    def register(
        self,
        username: str,
        shared_secret: Union[str, bytes],
        *,
        displayname: str,
        password: str = None,
        admin: bool = False
    ) -> dict:
        nonce = self._get_register_nonce()
        if password is None:
            password = Utility.get_password()
        data = {
            "nonce": nonce,
            "username": username,
            "display_name": displayname,
            "password": password,
            "admin": admin,
            "mac": self._generate_mac(nonce, username, password, shared_secret)
        }
        resp = self.connection.request(
            "POST",
            self.admin_patterns("/register", 1),
            json=data
        )

        return resp.json()

    def _get_register_nonce(self) -> str:
        resp = self.connection.request(
            "GET",
            self.admin_patterns("/register", 1)
        )
        return resp.json()["nonce"]

    def _generate_mac(
        self,
        nonce,
        user,
        password,
        shared_secret,
        admin=False,
        user_type=None
    ) -> str:
        """
        Adapted from:
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/register_api.rst
        """
        if isinstance(shared_secret, str):
            shared_secret = shared_secret.encode()
        elif not isinstance(shared_secret, bytes):
            raise TypeError("Argument shared_secret must be str or bytes")

        mac = hmac.new(
            key=shared_secret,
            digestmod=hashlib.sha1,
        )

        mac.update(nonce.encode('utf8'))
        mac.update(b"\x00")
        mac.update(user.encode('utf8'))
        mac.update(b"\x00")
        mac.update(password.encode('utf8'))
        mac.update(b"\x00")
        mac.update(b"admin" if admin else b"notadmin")
        if user_type:
            mac.update(b"\x00")
            mac.update(user_type.encode('utf8'))

        return mac.hexdigest()

    def list_media(
        self,
        userid: str,
        limit: int = 100,
        _from: int = 0,
        order_by: int = None,
        _dir: str = "f"
    ) -> Tuple[list, int, int]:
        userid = self.validate_username(userid)
        optional_str = ""
        if order_by is not None:
            optional_str += f"&order_by={order_by}"
        resp = self.connection.request(
            "GET",
            self.admin_patterns(
                f"/users/{userid}/media?"
                f"limit={limit}&from={_from}"
                f"&dir={_dir}{optional_str}", 1)
        )
        data = resp.json()
        if resp.status_code == 200:
            if "next_token" not in data:
                next_token = 0
            else:
                next_token = data["next_token"]
            return data["media"], next_token, data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def login(self, userid: str, valid_until_ms: int = None) -> str:
        if isinstance(valid_until_ms, int):
            data = {"valid_until_ms": valid_until_ms}
        elif valid_until_ms is None:
            data = {}
        else:
            raise TypeError(
                "Argument valid_until_ms must be int "
                f"but not {type(valid_until_ms)}."
            )

        userid = self.validate_username(userid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/users/{userid}/login", 1),
            json=data
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["access_token"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def get_ratelimit(self, userid: str) -> Tuple[int, int]:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(
                f"/users/{userid}/"
                "override_ratelimit",
                1
            )
        )
        data = resp.json()
        if data == {}:
            return data
        if resp.status_code == 200:
            return data["messages_per_second"], data["burst_count"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def set_ratelimit(self, userid: str, mps: int, bc: int) -> Tuple[int, int]:
        userid = self.validate_username(userid)
        data = {"messages_per_second": mps, "burst_count": bc}
        resp = self.connection.request(
            "POST",
            self.admin_patterns(
                f"/users/{userid}/"
                "override_ratelimit",
                1
            ),
            json=data
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["messages_per_second"], data["burst_count"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def disable_ratelimit(self, userid: str) -> Tuple[int, int]:
        return self.set_ratelimit(userid, 0, 0)

    def delete_ratelimit(self, userid: str) -> bool:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "DELETE",
            self.admin_patterns(
                f"/users/{userid}/"
                "override_ratelimit",
                1
            )
        )
        data = resp.json()
        if data == {}:
            return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def pushers(self, userid: str) -> Tuple[list, int]:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/pushers", 1)
        )
        data = resp.json()

        if resp.status_code == 200:
            return data["pushers"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def shadow_ban(self, userid: str) -> bool:
        print("WARNING! This action may Undermine the TRUST of YOUR USERS.")
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/users/{userid}/shadow_ban", 1)
        )
        data = resp.json()
        if len(data) == 0:
            return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])


class _Device(Admin):
    def __init__(self, server_addr, conn):
        self.server_addr = server_addr
        self.connection = conn

    def lists(self, userid: str) -> list:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/devices", 2)
        )
        data = resp.json()
        if resp.status_code == 200:
            return data["devices"]
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete(self, userid: str, device: Union[str, list]) -> bool:
        if isinstance(device, list) and len(device) > 1:
            return self._delete_multiple(userid, device)
        elif isinstance(device, list) and len(device) == 1:
            device = device[0]

        userid = self.validate_username(userid)
        resp = self.connection.request(
            "DELETE",
            self.admin_patterns(f"/users/{userid}/devices/{device}", 2)
        )
        if resp.status_code == 200:
            return True
        else:
            return False

    def _delete_multiple(self, userid: str, devices: list) -> bool:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "POST",
            self.admin_patterns(f"/users/{userid}/delete_devices", 2),
            json={"devices": devices}
        )
        if resp.status_code == 200:
            return True
        else:
            return False

    def show(self, userid: str, device: str) -> dict:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/devices/{device}", 2)
        )
        data = resp.json()
        if resp.status_code == 200:
            return data
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def update(self, userid: str, device: str, display_name: str) -> bool:
        userid = self.validate_username(userid)
        resp = self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{userid}/devices/{device}", 2),
            json={"display_name": display_name}
        )
        if resp.status_code == 200:
            return True
        else:
            data = resp.json()
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])
