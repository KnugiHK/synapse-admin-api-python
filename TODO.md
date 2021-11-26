# Todo
This document describes what need to be changed or added due to the changes made by [matrix-synapse](https://github.com/matrix-org/synapse/releases). Only major release of Synapse (x.y.0) will be included here.

## Regular
1. More tests for CI

## Synapse
1. Operation about [Registration Tokens](https://github.com/matrix-org/synapse/blob/develop/docs/usage/administration/admin_api/registration_tokens.md#registration-tokens) -> Test needed

### 1.48.0
1. Add a new version of delete room admin API DELETE /_synapse/admin/v2/rooms/<room_id> to run it in the background. Contributed by @dklimpel. ([#11223](https://github.com/matrix-org/synapse/issues/11223))
2. Allow the admin Delete Room API to block a room without the need to join it. ([#11228](https://github.com/matrix-org/synapse/issues/11228))
3. Add an admin API to un-shadow-ban a user. ([#11347](https://github.com/matrix-org/synapse/issues/11347))
4. Add an admin API to run background database schema updates. ([#11352](https://github.com/matrix-org/synapse/issues/11352))
5. Add an admin API for blocking a room. ([#11324](https://github.com/matrix-org/synapse/issues/11324))
