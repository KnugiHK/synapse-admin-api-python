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

    def __init__(self):
        super().__init__()
        self.devices = _Device()

    def lists(self):
        self.connection.request(
            "GET", self.admin_patterns("/users", 2),
            headers=self.header
        )
        resp = self.connection.get_response()
        data = json.loads(resp.read().decode())
        if resp.status == 200:
            return data["users"], data["total"]
        else:
            if self.supress_exception:
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def creates(self, user, *args, **kwargs):
        user = self.validate_username(user)
        self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{user}", 2),
            body=json.dumps(kwargs),
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

    def modify(self, user, *args, **kwargs):
        return self.creates(user, *args, **kwargs)

    def query(self, user):
        user = self.validate_username(user)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{user}", 2),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())

    def active_sessions(self, user):
        user = self.validate_username(user)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/whois/{user}", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        resp = json.loads(resp.read())["devices"][""]
        resp = resp["sessions"][0]["connections"]
        return resp

    def deactivate(self, user, erase=True):
        user = self.validate_username(user)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/deactivate/{user}", 1),
            body=json.dumps({"erase": erase}),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())["id_server_unbind_result"] == "success"

    def reactivate(self, user, password):
        if not isinstance(password, str):
            raise TypeError(
                "Argument 'password' should be a "
                f"string but not {type(password)}"
            )
        user = self.validate_username(user)
        return self.modify(user, password=password, deactivated=False)

    def reset_password(self, user, password, logout=True):
        user = self.validate_username(user)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/reset_password/{user}", 1),
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
                return False, data["errcode"], data["error"]
            else:
                raise SynapseException(data["errcode"], data["error"])

    def is_admin(self, user):
        user = self.validate_username(user)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{user}/admin", 1),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())["admin"]

    def set_admin(self, user, activate):
        user = self.validate_username(user)
        if not isinstance(activate, bool):
            raise TypeError(
                "Argument 'activate' only accept "
                f"boolean but not {type(activate)}."
            )
        self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{user}/admin", 1),
            body=json.dumps({"admin": activate}),
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

    def joined_room(self, user):
        user = self.validate_username(user)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{user}/joined_rooms", 1),
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
                return SynapseException(data["errcode"], data["error"])

    def join_room(self, user, room):
        user = self.validate_username(user)
        room = self.validate_room(room)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/join/{room}", 1),
            body=json.dumps({"user_id": user}),
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
                return SynapseException(data["errcode"], data["error"])

    # Not yet tested

    def validity(self, user, expiration=None, enable_renewal_emails=True):
        if expiration is not None and not isinstance(expiration, int):
            raise TypeError(
                "Argument 'expiration' only accept "
                f"int but not {type(expiration)}."
            )

        user = self.validate_username(user)
        data = {"user_id": user, "enable_renewal_emails": True}
        if expiration is not None:
            data["expiration_ts"] = expiration
        
        self.connection.request(
            "POST",
            self.admin_patterns("/account_validity/validity", 1),
            body=json.dumps(data),
            headers=self.header
        )
        resp = self.connection.get_response()
        return json.loads(resp.read())
    
    def register(self, username, password, displayname, shared_secret, admin=False):
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
            "mac": self._generate_mac(nonce, username, password, admin)
        }
        self.connection.request(
            "POST",
            self.admin_patterns("/register", 1),
            body=json.dumps(data),
            headers=self.header
        )

        resp = self.connection.get_response()
        return json.loads(resp.read())

    def _generate_mac(self, nonce, user, password, shared_secret, admin=False, user_type=None):
        """
        Adapted from:
        https://github.com/matrix-org/synapse/blob/develop/docs/admin_api/register_api.rst
        """
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
        

class _Device(Admin):
    def lists(self, user):
        user = self.validate_username(user)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{user}/devices", 2),
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

    def delete(self, user, device):
        if isinstance(device, list) and len(device) > 1:
            return self._deletes(user, device)
        elif isinstance(device, list) and len(device) == 1:
            device = device[0]

        user = self.validate_username(user)
        self.connection.request(
            "DELETE", self.admin_patterns(
                f"/users/{user}/devices/{device}", 2),
            headers=self.header)
        resp = self.connection.get_response()
        if resp.status == 200:
            return True
        else:
            return False

    def _deletes(self, user, devices):
        user = self.validate_username(user)
        self.connection.request(
            "POST",
            self.admin_patterns(f"/users/{user}/delete_devices", 2),
            body=json.dumps({"devices": devices}),
            headers=self.header
        )
        resp = self.connection.get_response()
        if resp.status == 200:
            return True
        else:
            return False

    def show(self, user, device):
        user = self.validate_username(user)
        self.connection.request(
            "GET",
            self.admin_patterns(f"/users/{user}/devices/{device}", 2),
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

    def update(self, user, device, display_name):
        user = self.validate_username(user)
        self.connection.request(
            "PUT",
            self.admin_patterns(f"/users/{user}/devices/{device}", 2),
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
