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

import httpx
import os
import re
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path
from typing import Tuple, Any


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


class Utility():
    port_re = re.compile(r":[0-9]{1,5}/?$")
    http_re = re.compile(r"^https?://")

    @staticmethod
    def get_bool(boolean: bool) -> str:
        if not isinstance(boolean, bool):
            raise TypeError("Argument 'boolean' must be a "
                            f"bool not a {type(boolean)}")
        if boolean:
            return "true"
        else:
            return "false"

    @staticmethod
    def get_current_time() -> int:
        return int(datetime.now().timestamp() * 1000)


class Admin():
    """Base class for storing common variable read configuration"""

    def __init__(
        self,
        server_addr: str = None,
        server_port: int = 443,
        access_token: str = None,
        server_protocol: str = None,
        suppress_exception: bool = False
    ):
        if server_addr is not None and access_token is not None:
            self.access_token = access_token
            self.server_addr = server_addr
            self.server_port = server_port
            if server_protocol is None:
                self.server_protocol = \
                    self._parse_protocol_by_port(server_port)
            else:
                if "://" not in server_protocol:
                    self.server_protocol = server_protocol + "://"
                else:
                    self.server_protocol = server_protocol
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
                self.read_config(self.config_path)
            else:
                # If configuration file not found, create one
                self.create_config()
        self.access_token_header = {
            "Authorization": f"Bearer {self.access_token}"
        }
        from .__init__ import __version__
        self.header = {
            **self.access_token_header,
            "User-Agent": f"matrix-synpase-admin-python/{__version__}"
        }
        self.connection = HTTPConnection(
            self.server_protocol,
            self.server_addr,
            self.server_port,
            self.header
        )
        self.supress_exception = suppress_exception

    def create_config(
        self,
        protocol: str = None,
        url: str = None,
        port: int = None,
        access_token: str = None
    ) -> bool:
        if (protocol is None or url is None or
                port is None or access_token is None):
            while True:
                url = input(
                    "Enter the homeserver URL with port"
                    "(e.g. https://example.com:443): "
                )
                try:
                    protocol, host, port = self._parse_homeserver_url(url)
                except ValueError as e:
                    print(e)
                    continue
                else:
                    break
            access_token = input("Enter the access token: ")
            save = input("Save to a config file?(Y/n)").lower()

            self.server_protocol = protocol
            self.server_addr = host
            self.server_port = int(port)
            self.access_token = access_token
            if save == "n":
                return True
            else:
                return self._save_config(protocol, host, port, access_token)

    def _parse_homeserver_url(self, url: str) -> Tuple[str, str, int]:
        port = Utility.port_re.search(url)
        protocol = Utility.http_re.search(url)
        if port is None:
            if protocol is None:
                raise ValueError(
                    "You must specify at least "
                    "a port or a HTTP protocol"
                )
            elif protocol[0] == "https://":
                port = 443
            elif protocol[0] == "http://":
                port = 80
        else:
            port = int(port[0][1:].replace("/", ""))
            if protocol is None:
                protocol = self._parse_protocol_by_port(port)
        if protocol is not None and isinstance(protocol, re.Match):
            protocol = protocol[0]

        host = url
        if protocol is not None:
            host = host.replace(protocol, "")
        if port is not None:
            host = host.replace(f":{port}", "")
        if host[-1] == "/":
            host = host[:-1]

        return protocol, host, port

    def _parse_protocol_by_port(self, port: int) -> str:
        if port == 80 or port == 8008:
            return "http://"
        elif port == 443 or port == 8443:
            return "https://"
        else:
            raise ValueError(
                "Cannot determine the protocol "
                f"automatically by the port {port}."
            )

    def _save_config(
        self,
        protocol: str,
        host: str,
        port: int,
        token: str
    ) -> bool:
        config = ConfigParser()
        config['DEFAULT'] = {
            'protocol': protocol,
            'homeserver': host,
            'port': port,
            'token': token
        }
        with open(self.config_path, 'w') as configfile:
            config.write(configfile)
        return True

    def modify_config(
        self,
        server_addr: str = None,
        access_token: str = None
    ) -> bool:
        raise NotImplementedError("This function is temporarily disabled.")
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
        return True

    def read_config(self, config_path: str) -> bool:
        config = ConfigParser()
        config.sections()
        config.read(config_path)
        self.server_protocol = config.get("DEFAULT", "protocol")
        self.server_addr = config.get("DEFAULT", "homeserver")
        self.access_token = config.get("DEFAULT", "token")
        self.server_port = int(config.get("DEFAULT", "port"))
        return True

    def validate_server(self, string: str) -> str:
        if f":{self.server_addr}" not in string:
            string = string + f":{self.server_addr}"
        return string

    def validate_username(self, user: str) -> str:
        user = self.validate_server(user)
        if user[0] != "@":
            user = "@" + user
        return user

    def validate_room(self, room: str) -> str:
        room = self.validate_server(room)
        if room[0] != "!":
            room = "!" + room
        return room

    def admin_patterns(self, path: str, version: int = 1) -> str:
        base = "/_synapse/admin/"
        if path[0] != "/":
            path = "/" + path
        return f"{base}v{version}{path}"


class Client(httpx.Client):
    def delete(self, url, json) -> httpx.Response:
        return self.request("DELETE", url, json=json)


class HTTPConnection():
    def __init__(
        self,
        protocol: str,
        host: str,
        port: int,
        headers: str
    ):
        self.headers = headers
        self.protocol = protocol
        self.host = host
        self.port = port
        self.conn = Client(headers=self.headers)
        self.method_map = {
            "GET": self.conn.get,
            "POST": self.conn.post,
            "PUT": self.conn.put,
            "DELETE": self.conn.delete,
        }
        self.base_url = f"{self.protocol}{self.host}:{self.port}"

    def request(
        self,
        method: str,
        path: str,
        json: Any = None
    ) -> httpx.Response:
        url = self.base_url + path
        request = self.method_map[method]
        if json is not None:
            return request(url, json=json)
        return request(url)
