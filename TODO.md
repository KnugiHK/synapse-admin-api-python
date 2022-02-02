# Todo
This document describes what need to be changed or added due to the changes made by [matrix-synapse](https://github.com/matrix-org/synapse/releases). Only major release of Synapse (x.y.0) will be included here.

## Regular
1. More tests for CI

## Synapse
### 1.49.0
1. Add admin API to get some information about federation status with remote servers. ([#11407](https://github.com/matrix-org/synapse/issues/11407)) -> Test delayed

### 1.52.0
1. Add an admin API to reset connection timeouts for remote server. ([#11639](https://github.com/matrix-org/synapse/issues/11639))
2. Add an admin API to get a list of rooms that federate with a given remote homeserver. ([#11658](https://github.com/matrix-org/synapse/issues/11658))
