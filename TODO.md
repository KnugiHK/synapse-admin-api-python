# Todo
This document describes what need to be changed or added due to the changes made by [matrix-synapse](https://github.com/matrix-org/synapse/releases). Only major release of Synapse (x.y.0) will be included here.

## Regular
1. More tests for CI

## Synapse
1. Admin API to delete several media for a specific user. Contributed by @dklimpel. ([#10558](https://github.com/matrix-org/synapse/issues/10558), [#10628](https://github.com/matrix-org/synapse/issues/10628)) -> Test needed
2. Add an admin API (GET /_synapse/admin/username_available) to check if a username is available (regardless of registration settings). ([#10578](https://github.com/matrix-org/synapse/issues/10578)) -> Test needed
3. Allow editing a user's external_ids via the "Edit User" admin API. Contributed by @dklimpel. ([#10598](https://github.com/matrix-org/synapse/issues/10598)) -> Test needed
