# Todo
This document describes what need to be changed or added due to the changes made by [matrix-synapse](https://github.com/matrix-org/synapse/releases). Only major release of Synapse (x.y.0) will be included here.

## Regular
1. More tests for CI

## Synapse
### 1.46.0
1. Users admin API can now also modify user type in addition to allowing it to be set on user creation. ([#11174](https://github.com/matrix-org/synapse/issues/11174))

### 1.47.0
1. Add search by room ID and room alias to the List Room admin API. ([#11099](https://github.com/matrix-org/synapse/issues/11099))
2. Add admin APIs to pause, start and check the status of background updates. ([#11263](https://github.com/matrix-org/synapse/issues/11263))
