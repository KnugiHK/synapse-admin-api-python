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
from getpass import getpass
from pathlib import Path
from typing import Tuple, Any


class SynapseException(Exception):
    """Error returned from the Admin API"""

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
    """Some utilities"""

    port_re = re.compile(r":[0-9]{1,5}/?$")
    http_re = re.compile(r"^https?://")

    @staticmethod
    def get_bool(boolean: bool) -> str:
        """Covert Python bool to str

        Returns:
            str: string "true" or "false"
        """
        if not isinstance(boolean, bool):
            raise TypeError("Argument 'boolean' must be a "
                            f"bool not a {type(boolean)}")
        if boolean:
            return "true"
        else:
            return "false"

    @staticmethod
    def get_current_time() -> int:
        """Get the current timestamp in millisecond

        Returns:
            int: current timestamp in millisecond
        """
        return int(datetime.now().timestamp() * 1000)

    @staticmethod
    def get_password(
        prompt: str = "Enter a password: ",
        validate: bool = True
    ) -> str:
        """Get a password interactively

        Args:
            prompt (str, optional): String to ask for input. Defaults to "Enter a password: ". # noqa: E501

        Returns:
            str: the password user entered
        """
        password = getpass(prompt)
        if validate:
            again = getpass("Enter the password again: ")
            if password == again:
                return password
            else:
                print("The passwords you entered are not the same, try again.")
                return Utility.get_password(prompt)
        else:
            return password


class Admin():
    """Base class for storing common variable read configuration"""

    def __init__(
        self,
        server_addr: str = None,
        server_port: int = 443,
        access_token: str = None,
        server_protocol: str = None,
        suppress_exception: bool = False
    ) -> None:
        """
        Args:
            server_addr (str, optional): homeserver address. Defaults to None.
            server_port (int, optional): homeserver listening port. Defaults to 443.
            access_token (str, optional): access token that has admin power. Defaults to None.
            server_protocol (str, optional): "http://" or "https://". Defaults to None.
            suppress_exception (bool, optional): supress exception or not, if not return False and the error in dict. Defaults to False. # noqa: E501
        """
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
        self._create_conn()
        self.supress_exception = suppress_exception

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

    def _create_conn(self) -> bool:
        """Create connection to the homeserver"""
        self.connection = HTTPConnection(
            self.server_protocol,
            self.server_addr,
            self.server_port,
            self.header
        )
        return True

    def create_config(
        self,
        protocol: str = None,
        host: str = None,
        port: int = None,
        access_token: str = None,
        save_to_file: int = False
    ) -> bool:
        """Create configuration (interactively)

        Args:
            protocol (str, optional): "http://" or "https://". Defaults to None. # noqa: E501
            host (str, optional): homeserver address. Defaults to None.
            port (int, optional): homeserver listening port. Defaults to None.
            access_token (str, optional): access token that has admin privilege. Defaults to None. # noqa: E501
            save_to_file (int, optional): whether or not save the configration to a file. Defaults to False. # noqa: E501

        Returns:
            bool: configration saved
        """
        if (protocol is None or host is None or
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
            while True:
                access_token = input(
                    "Enter the access token (leave blank "
                    "to get the access token by logging in): "
                )
                if access_token == "":
                    from synapse_admin.client import ClientAPI
                    access_token = ClientAPI.admin_login(
                        protocol,
                        host,
                        port,
                        supress_exception=True
                    )
                    if not access_token:
                        print(
                            "The account you logged in is not a server admin "
                            "or you entered an invalid username/password."
                        )
                        continue
                    else:
                        print("Token retrieved successfully")
                break
            save_to_file = input("Save to a config file? (Y/n) ").lower()

        self.server_protocol = protocol
        self.server_addr = host
        self.server_port = int(port)
        self.access_token = access_token
        if save_to_file == "n" or not save_to_file:
            return True
        return self._save_config(protocol, host, port, access_token)

    def _parse_homeserver_url(self, url: str) -> Tuple[str, str, int]:
        """Parse a given URL to three parts.

        Args:
            url (str): URL that is needed to be parsed

        Raises:
            ValueError: Raised if neither port or protocol is specified

        Returns:
            Tuple[str, str, int]: protocol, host, port
        """
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
        """Parse the given port to protocol automatically

        Args:
            port (int): port that is needed to be parsed

        Raises:
            ValueError: raised if the port is not 80 or 8008 or 443 or 8443

        Returns:
            str: either "http://" or "https://"
        """
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
        """Write the configration to a file

        Args:
            protocol (str): "http://" or "https://". Defaults to None.
            host (str): homeserver address. Defaults to None.
            port (int): homeserver listening port. Defaults to None.
            token (str): access token that has admin privilege. Defaults to None. # noqa: E501

        Returns:
            bool: Success or not
        """
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
        server_port: int = None,
        access_token: str = None,
        server_protocol: str = None,
        save_to_file: bool = True
    ) -> bool:
        """Modifying the current configuration

        Args:
            server_addr (str, optional): homeserver address. Defaults to None.
            server_port (int, optional): homeserver listening port. Defaults to None. # noqa: E501
            access_token (str, optional): access token that has admin privilege. Defaults to None. # noqa: E501
            server_protocol (str, optional): "http://" or "https://". Defaults to None. # noqa: E501
            save_to_file (bool, optional): whether or not save the configration to a file. Defaults to True. # noqa: E501

        Returns:
            bool: success or not
        """
        if (server_addr is None and server_port is None and
                access_token is None and server_protocol is None):
            self.create_config()
            return self._create_conn()

        if server_addr is not None:
            self.server_addr = server_addr
        if access_token is not None:
            self.access_token = access_token
        if server_port is not None:
            self.server_port = server_port
        if server_protocol is not None:
            self.server_protocol = server_protocol

        self._create_conn()

        if save_to_file:
            return self._save_config(
                self.server_protocol,
                self.server_addr,
                self.server_port,
                self.access_token
            )
        return True

    def read_config(self, config_path: str) -> bool:
        """Read configuration from given path

        Args:
            config_path (str): Path to configuration file

        Returns:
            bool: success or not
        """
        config = ConfigParser()
        config.sections()
        config.read(config_path)
        self.server_protocol = config.get("DEFAULT", "protocol")
        self.server_addr = config.get("DEFAULT", "homeserver")
        self.access_token = config.get("DEFAULT", "token")
        self.server_port = int(config.get("DEFAULT", "port"))
        return True

    def validate_server(self, string: str) -> str:
        """Validate the homeserver part of a given ID. If necessary add the homeserver address. # noqa: E501

        Args:
            string (str): User/Room/Media/Group ID

        Returns:
            str: ID with validated homeserver address part
        """
        if f":{self.server_addr}" not in string:
            string = string + f":{self.server_addr}"
        return string

    def validate_username(self, user: str) -> str:
        """Validate a user ID. If necessary add the user id identifier (@).

        Args:
            user (str): User ID (without @ and homeserver address part are also accepted) # noqa: E501

        Returns:
            str: validated user ID
        """
        user = self.validate_server(user)
        if user[0] != "@":
            user = "@" + user
        return user

    def validate_room(self, roomid: str) -> str:
        """Validate a room ID. If necessary add the room id identifier (!).

        Args:
            roomid (str): room ID (without ! and homeserver address part are also accepted) # noqa: E501

        Returns:
            str: validated room ID
        """
        roomid = self.validate_server(roomid)
        if roomid[0] != "!":
            roomid = "!" + roomid
        return roomid

    def validate_group(self, group: str) -> str:
        """Validate a group ID. If necessary add the group id identifier (+).

        Args:
            group (str): group ID (without + and homeserver address part are also accepted) # noqa: E501

        Returns:
            str: validated group ID
        """
        group = self.validate_server(group)
        if group[0] != "+":
            group = "+" + group
        return group

    def admin_patterns(self, path: str, version: int = 1) -> str:
        """Constructing an admin API endpoint url

        Args:
            path (str): the path after r'/_synapse/admin/v[1-2]/?'. The first slash in path is optional. # noqa: E501
            version (int, optional): the version of the API endpoint. Defaults to 1.

        Returns:
            str: admin API endpoint url
        """
        base = "/_synapse/admin/"
        if path[0] != "/":
            path = "/" + path
        return f"{base}v{version}{path}"


class Client(httpx.Client):
    """Some custom behavior based on httpx.Client"""

    def delete(self, url: str, json: dict = None) -> httpx.Response:
        """Allow a DELETE request to include a JSON body

        Args:
            url (str): URL of the API endpoint.
            json (dict, optional): the JSON body in dict. Defaults to None.

        Returns:
            httpx.Response
        """
        if json is not None:
            return self.request("DELETE", url, json=json)
        else:
            return self.request("DELETE", url)


class HTTPConnection():
    """A helper class for the compatibility of old version of synapse_admin"""

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
        """Determine the correct HTTP method to be used and fire the request

        Args:
            method (str): the HTTP method: (GET|POST|PUT|DELETE)
            path (str): the path of the API endpoint (without the protocol and host part) # noqa: E501
            json (Any, optional): a JSON body if any. Defaults to None.

        Returns:
            httpx.Response
        """
        url = self.base_url + path
        request = self.method_map[method]
        if json is not None:
            return request(url, json=json)
        return request(url)
