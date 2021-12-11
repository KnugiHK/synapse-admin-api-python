# Todo
This document describes what need to be changed or added due to the changes made by [matrix-synapse](https://github.com/matrix-org/synapse/releases). Only major release of Synapse (x.y.0) will be included here.

## Regular
1. More tests for CI

## Synapse
1. Operation about [Registration Tokens](https://github.com/matrix-org/synapse/blob/develop/docs/usage/administration/admin_api/registration_tokens.md#registration-tokens) -> Test needed

### 1.49.0
1. Add admin API to get some information about federation status with remote servers. ([#11407](https://github.com/matrix-org/synapse/issues/11407))
2. Extend the "delete room" admin api to work correctly on rooms which have previously been partially deleted. ([#11523](https://github.com/matrix-org/synapse/issues/11523))
