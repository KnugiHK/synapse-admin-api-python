# Synapse-admin-api-python
[![Pypi](https://img.shields.io/pypi/v/matrix-synapse-admin?label=Pypi)](https://pypi.org/project/matrix-synapse-admin/)
[![License MIT](https://img.shields.io/pypi/l/matrix-synapse-admin)](https://github.com/KnugiHK/synapse-admin-api-python/blob/main/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/matrix-synapse-admin)](https://pypi.org/project/matrix-synapse-admin/)
[![Synapse](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FKnugiHK%2Fsynapse-admin-api-python%2Fmain%2Fsupported_synapse.json)](https://github.com/KnugiHK/synapse-admin-api-python/blob/main/TODO.md)
[![Tests](https://github.com/KnugiHK/synapse-admin-api-python/actions/workflows/tests.yml/badge.svg)](https://github.com/KnugiHK/synapse-admin-api-python/actions/workflows/tests.yml)

A Python wrapper for [Matrix Synapse admin API](https://github.com/matrix-org/synapse).

### Versioning
This library now supports up to Synapse 1.60.0, any Admin API introduced after 1.60.0 may not be included in this version. However, newer changes to Admin API are planned to be included in this library. For planned update, see [TODO.md](TODO.md). In the future, the version numbering convention will follow the version this library up to, for example, if this library supports up to 1.60.0, then the version number of this library will be 1.60.0. And the minor number will be reserved for bug fixes in this repo.

**Releases older than 0.1.5 only work with HTTP/2**

## Get Started
Install from PyPi
```sh
pip install matrix-synapse-admin
```
Provide the connection information and access token in the first time of execution. You can either enter the information interactively or as arguments:  
### Interactively
```python
>>> from synapse_admin import User
>>> user = User()
# The config creator is smart enough to determine the protocol and port by providing either one.
Enter the homeserver URL with port(e.g. https://example.com:443): https://example.com # Only need to be entered in the first time
Enter the access token (leave blank to get the access token by logging in): <access token or leave blank> # Only need to be entered in the first time
# If access token is left blank
Enter a username: admin
Enter a password:
Token retrieved successfully
Save to a config file? (Y/n)
>>> details_of_users = user.lists()
>>> print(details_of_users)
[{'name': '@admin:example.com', 'user_type': None, 'is_guest': 0, 'admin': 1, 'deactivated': 0, 'shadow_banned': False, 'displayname': 'Admin', 'avatar_url': 'mxc://example.com/ABCDEFG'}]
>>> print(details_of_users.total)
1
```
### As arguments
```python
>>> from synapse_admin import User
>>> user = User("example.com", 443, "<access token>", "https://")
>>> details_of_users = user.lists()
>>> print(details_of_users)
[{'name': '@admin:example.com', 'user_type': None, 'is_guest': 0, 'admin': 1, 'deactivated': 0, 'shadow_banned': False, 'displayname': 'Admin', 'avatar_url': 'mxc://example.com/ABCDEFG'}]
>>> print(details_of_users.total)
1
```
### Unit Testing
Simply run the testing script
```shell
chmod +x testing_env.sh
./testing_env.sh
```
## Documentation
Docstrings are present now in most methods and classes. If you see /equivalent to ".*"/, it's mean that you may want to refer back to the Synapse Admin API documentation.

More documentation are coming...

## Additional features
In addition to the wrapper that wraps the official admin APIs, this wrapper also provides serval unofficial helper methods or admin APIs, they include:
* Reactivate an deactivated account (User.reactivate)
* Create a room (Room.create)
* Send an announcement to everyone (Management.announce_all)
* Delete media by id or by condition (Media.delete_media)

## Contribution
If you want to help me to improve the quality of this project, you can submit an issue.

If you want to collaborate with us, feel free to Fork this project and open a pull request.
### What can you do?
* For Issue
  * Report any Error.
  * Request new features based on the Synapse Admin API
  * Ask questions if you do not understand something.
  * More.

* For Pull request
  * Add comments to source code.
  * Add new features based on the Synapse Admin API
  * Correct any Error.
  * More.
