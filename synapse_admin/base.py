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

from pathlib import Path
import os
from configparser import ConfigParser
from hyper import HTTPConnection
from datetime import datetime


class SynapseException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f"SynapseException: [{self.code}] {self.msg}"


class SynapseAPIError(Exception):
    def __init__(self):
        super().__init__("The API is not ready.")


class Admin():
    """Base class for storing common variable read configuration"""

    def __init__(
        self,
        server_addr=None,
        server_port=443,
        access_token=None,
        suppress_exception=False
    ):
        if server_addr is not None and access_token is not None:
            self.access_token = access_token
            self.server_addr = server_addr
            self.server_port = server_port
        else:
            # If homeserver address or/and access token are
            # not provided, read from configration file
            if os.name == "nt":
                path = os.path.join(
                    f"{os.environ['APPDATA']}\\Synapse-Admin-API\\")
                if not os.path.isdir(path):
                    os.makedirs(path)
            else:
                path = str(Path.home())

            self.config_path = os.path.join(path, "api.cfg")
            if os.path.isfile(self.config_path):
                self.read()
            else:
                # If configuration file not found, create one
                self.create()
        self.access_token_header = {
            "Authorization": f"Bearer {self.access_token}"}
        self.header = {**self.access_token_header}
        self.connection = HTTPConnection(self.server_addr, self.server_port)
        self.supress_exception = suppress_exception

    def create(self, url=None, port=None, access_token=None):
        if url is None or port is None or access_token is None:
            while True:
                try:
                    url, port = input(
                        "Enter the homeserver URL with port: ").split(":")
                except ValueError:
                    continue
                else:
                    break
            access_token = input("Enter the access token: ")
        return self._create(url, port, access_token)

    def _create(self, url, port, token):
        config = ConfigParser()
        self.server_addr = url
        self.server_port = int(port)
        self.access_token = token
        config['DEFAULT'] = {'homeserver': url, 'port': port, 'token': token}
        with open(self.config_path, 'w') as configfile:
            config.write(configfile)

    def modify(self, server_addr=None, access_token=None):
        if server_addr is None and access_token is None:
            return

        if server_addr is not None:
            self.server_addr = server_addr
        if access_token is not None:
            self.access_token = access_token
        config = ConfigParser()
        config['DEFAULT'] = {
            'homeserver': self.server_addr, 'token': self.access_token}
        with open(self.config_path, 'w') as configfile:
            config.write(configfile)

    def read(self):
        config = ConfigParser()
        config.sections()
        config.read(self.config_path)
        self.server_addr = config.get("DEFAULT", "homeserver")
        self.access_token = config.get("DEFAULT", "token")
        self.server_port = int(config.get("DEFAULT", "port"))

    def validate_server(self, string):
        if f":{self.server_addr}" not in string:
            string = string + f":{self.server_addr}"
        return string

    def validate_username(self, user):
        user = self.validate_server(user)
        if user[0] != "@":
            user = "@" + user
        return user

    def validate_room(self, room):
        room = self.validate_server(room)
        if room[0] != "!":
            room = "!" + room
        return room

    def admin_patterns(self, path, version=1):
        base = "/_synapse/admin/"
        if path[0] != "/":
            path = "/" + path
        return f"{base}v{version}{path}"

    @staticmethod
    def get_bool(boolean):
        if not isinstance(boolean, bool):
            raise TypeError("Argument 'boolean' must be a "
                            f"bool not a {type(boolean)}")
        if boolean:
            return "true"
        else:
            return "false"

    @staticmethod
    def get_current_time():
        return int(datetime.now().timestamp() * 1000)
