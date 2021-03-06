# Synapse-admin-api-python
[![Latest in Pypi](https://img.shields.io/pypi/v/matrix-synapse-admin?label=Latest%20in%20Pypi)](https://pypi.org/project/matrix-synapse-admin/)
![License MIT](https://img.shields.io/pypi/l/matrix-synapse-admin)

A Python wrapper for Matrix Synapse admin API

This library now supports up to Synapse 1.35.0, any Admin API introduced after 1.35.0 may not be included in this version. However, newer changes to Admin API are planned to be included in this library. For planned update, see [TODO.md](TODO.md). In the future, the version numbering convention will follow the version this library up to, for example, if this library supports up to 1.35.0, then the version number of this library will be 1.35.0. And the minor number will be reserved for bug fixes in this repo.

**Releases older than 0.1.5 only work with HTTP/2**

## Get Started
Install from PyPi
```sh
pip install matrix-synapse-admin
```
Provide the connection information and access token in the first time of execution:
```python
>>> from synapse_admin import User
>>> user = User()
# The config creator is smart enough to determine the protocol and port by providing either one.
Enter the homeserver URL with port(e.g. https://example.com:443): https://example.com # Only need to be entered in the first time
Enter the access token: <access token> # Only need to be entered in the first time
>>> details_of_users, number_of_users = user.lists()
>>> print(details_of_users)
[{'name': '@admin:example.com', 'user_type': None, 'is_guest': 0, 'admin': 1, 'deactivated': 0, 'shadow_banned': False, 'displayname': 'Admin', 'avatar_url': 'mxc://example.com/ABCDEFG'}]
>>> print(number_of_users)
1
```
More documentation are coming...