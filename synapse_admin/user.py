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
import hmac
import hashlib


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
        self.devices = _Device()

    def lists(
        self,
        offset=0,
        limit=100,
        userid=None,
        name=None,
        guests=True,
        deactivated=False,
        order_by=None
    ):
        optional_str = ""
        if userid is not None:
            userid = self.validate_username(userid)
            optional_str += f"&user_id={userid}"
        if name is not None:
            optional_str += f"&name={name}"
        if order_by is not None:
            optional_str += f"&order_by={order_by}"

        self.connection.request(
            "GET",
            self.admin_patterns(
                f"/users?from={offset}&limit={limit}&guests="
                f"{Admin.get_bool(guests)}&deactivated="
                f"{Admin.get_bool(deactivated)}{optional_str}",
                2
            ),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read().decode())
        if resp.status == 200:
            return data["users"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def creates(self, userid, *args, **kwargs):
        userid = self.validate_username(userid)
        self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{userid}", 2),
            body=json.dumps(kwargs),
            headers=self.header
        )
        resp = self.connection.get_response()
        if resp.status == 200:
            return True
        else:
            data = json.loads(resp.read())
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def modify(self, user, *args, **kwargs):
        return self.creates(user, *args, **kwargs)

    def query(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}", 2),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())

    def active_sessions(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/whois/{userid}", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        resp = json.loads(resp.read())["devices"][""]
        resp = resp["sessions"][0]["connections"]
        return resp

    def deactivate(self, userid, erase=True):
        userid = self.validate_username(userid)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/deactivate/{userid}", 1),
            body=json.dumps({"erase": erase}),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())["id_server_unbind_result"] == "success"

    def reactivate(self, userid, password):
        if not isinstance(password, str):
            raise TypeError(
                "Argument 'password' should be a "
                f"string but not {type(password)}"
            )
        userid = self.validate_username(userid)
        return self.modify(userid, password=password, deactivated=False)

    def reset_password(self, userid, password, logout=True):
        userid = self.validate_username(userid)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/reset_password/{userid}", 1),
            body=json.dumps(
                {"new_password": password, "logout_devices": logout}),
            headers=self.header
        )
        resp = self.connection.get_response()
        if resp.status == 200:
            return True
        else:
            data = json.loads(resp.read())
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def is_admin(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/admin", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())["admin"]

    def set_admin(self, userid, activate):
        userid = self.validate_username(userid)
        if not isinstance(activate, bool):
            raise TypeError(
                "Argument 'activate' only accept "
                f"boolean but not {type(activate)}."
            )
        self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{userid}/admin", 1),
            body=json.dumps({"admin": activate}),
            headers=self.header
        )
        resp = self.connection.get_response()
        if resp.status == 200:
            return True
        else:
            data = json.loads(resp.read())
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def joined_room(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/joined_rooms", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data["joined_rooms"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def join_room(self, userid, room):
        userid = self.validate_username(userid)
        room = self.validate_room(room)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/join/{room}", 1),
            body=json.dumps({"user_id": userid}),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            if "room_id" in data and data["room_id"] == room:
                return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def validity(self, userid, expiration=0, enable_renewal_emails=True):
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

        self.connection.request(
            "POST",
            self.admin_patterns("/account_validity/validity", 1),
            body=json.dumps(data),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def register(
        self,
        username,
        password,
        displayname,
        shared_secret,
        admin=False
    ):
        self.connection.request(
            "GET",
            self.admin_patterns("/register", 1)
        )
        resp = self.connection.get_response()
        nonce = json.loads(resp.read())["nonce"]
        data = {
            "nonce": nonce,
            "username": username,
            "display_name": displayname,
            "password": password,
            "admin": admin,
            "mac": self._generate_mac(nonce, username, password, shared_secret)
        }
        self.connection.request(
            "POST",
            self.admin_patterns("/register", 1),
            body=json.dumps(data),
            headers=self.header
        )

        resp = self.connection.get_response()
        return json.loads(resp.read())

    def _generate_mac(
        self,
        nonce,
        user,
        password,
        shared_secret,
        admin=False,
        user_type=None
    ):
        """
        Adapted from:
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/register_api.rst
        """
        mac = hmac.new(
            key=shared_secret.encode(),
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

    def list_media(self, userid, limit=100, _from=0, order_by=None, _dir="f"):
        userid = self.validate_username(userid)
        optional_str = ""
        if order_by is not None:
            optional_str += f"&order_by={order_by}"
        self.connection.request(
            "GET",
            self.admin_patterns(
                f"/users/{userid}/media?"
                f"limit={limit}&from={_from}"
                f"&dir={_dir}{optional_str}", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
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

    def login(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/users/{userid}/login", 1),
            body="{}",
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data["access_token"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def get_ratelimit(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "GET",
            self.admin_patterns(
                f"/users/{userid}/"
                "override_ratelimit",
                1
            ),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if data == {}:
            return data
        if resp.status == 200:
            return data["messages_per_second"], data["burst_count"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def set_ratelimit(self, userid, mps, bc):
        userid = self.validate_username(userid)
        data = {"messages_per_second": mps, "burst_count": bc}
        self.connection.request(
            "POST",
            self.admin_patterns(
                f"/users/{userid}/"
                "override_ratelimit",
                1
            ),
            body=json.dumps(data),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data["messages_per_second"], data["burst_count"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def disable_ratelimit(self, userid):
        return self.set_ratelimit(userid, 0, 0)

    def delete_ratelimit(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "DELETE",
            self.admin_patterns(
                f"/users/{userid}/"
                "override_ratelimit",
                1
            ),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if data == {}:
            return True
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def pushers(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/pushers", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())

        if resp.status == 200:
            return data["pushers"], data["total"]
        else:
            if self.supress_exception:
                return False, data
            else:
                raise SynapseException(data["errcode"], data["error"])

    def shadow_ban(self, userid):
        print("WARNING! This action may Undermine the TRUST of YOUR USERS.")
        userid = self.validate_username(userid)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/users/{userid}/shadow_ban", 1),
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


class _Device(Admin):
    def lists(self, userid):
        userid = self.validate_username(userid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/devices", 2),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read())
        if resp.status == 200:
            return data["devices"]
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def delete(self, userid, device):
        if isinstance(device, list) and len(device) > 1:
            return self._deletes(userid, device)
        elif isinstance(device, list) and len(device) == 1:
            device = device[0]

        userid = self.validate_username(userid)
        self.connection.request(
            "DELETE", self.admin_patterns(
                f"/users/{userid}/devices/{device}", 2),
            headers=self.header)
        resp = self.connection.get_response()
        if resp.status == 200:
            return True
        else:
            return False

    def _deletes(self, userid, devices):
        userid = self.validate_username(userid)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/users/{userid}/delete_devices", 2),
            body=json.dumps({"devices": devices}),
            headers=self.header
        )
        resp = self.connection.get_response()
        if resp.status == 200:
            return True
        else:
            return False

    def show(self, userid, device):
        userid = self.validate_username(userid)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{userid}/devices/{device}", 2),
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

    def update(self, userid, device, display_name):
        userid = self.validate_username(userid)
        self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{userid}/devices/{device}", 2),
            body=json.dumps({"display_name": display_name}),
            headers=self.header
        )
        resp = self.connection.get_response()
        if resp.status == 200:
            return True
        else:
            data = json.loads(resp.read())
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])
