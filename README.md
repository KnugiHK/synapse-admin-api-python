# Synapse-admin-api-python
A Python wrapper for Matrix Synapse admin API

This library now supports up to Synapse 1.34.0, any Admin API introduced after 1.34.0 may not be included in this version. However, newer changes to Admin API are planned to be included in this library. For planned update, see [TODO.md](TODO.md). In the future, the version numbering convention will follow the version this library up to, for example, if this library supports up to 1.34.0, then the version number of this library will be 1.34.0. And the minor number will be reserved for bug fixes in this repo.

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
Enter the homeserver URL with port: example.com:443 # Only need to be entered in the first time
Enter the access token: <access token> # Only need to be entered in the first time
>>> details_of_users, number_of_users = user.lists()
>>> print(details_of_users)
[{'name': '@admin:example.com', 'user_type': None, 'is_guest': 0, 'admin': 1, 'deactivated': 0, 'shadow_banned': False, 'displayname': 'Admin', 'avatar_url': 'mxc://example.com/ABCDEFG'}]
>>> print(number_of_users)
1
```
More documentation are coming...

## Contribution
If you want to help me to improve the quality of this project, you can submit an issue.

If you want to collaborate with us, feel free to Fork this project and open a pull request.
### What can you do?
* For Issue
  * Report any Error.
  * Request new features based on the Synapse Admin API
  * Ask questions if you do not understand something.

* For Pull request
  * Add comments to source code.
  * Add new features based on the Synapse Admin API
  * Correct any Error.
