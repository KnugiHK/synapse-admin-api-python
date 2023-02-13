# Todo
This document describes what need to be changed or added due to the changes made by [matrix-synapse](https://github.com/matrix-org/synapse/releases). Only major release of Synapse (x.y.0) will be included here.

## Regular
1. More tests for CI

## Synapse
### 1.49.0
1. Add admin API to get some information about federation status with remote servers. ([#11407](https://github.com/matrix-org/synapse/issues/11407)) -> Test delayed

### 1.61.0
1. Allow updating a user's password using the admin API without logging out their devices. Contributed by @jcgruenhage. ([#12952](https://github.com/matrix-org/synapse/issues/12952))

### 1.64.0
1. Add a room_type field in the responses for the list room and room details admin APIs. Contributed by @andrewdoh. ([#13208](https://github.com/matrix-org/synapse/issues/13208))

### 1.66.0
1. Add forgotten status to Room Details Admin API. ([#13503](https://github.com/matrix-org/synapse/issues/13503))

### 1.68.0
1. Add an admin API endpoint to fetch messages within a particular window of time. ([#13672](https://github.com/matrix-org/synapse/issues/13672))
2. Add an admin API endpoint to find a user based on their external ID in an auth provider. ([#13810](https://github.com/matrix-org/synapse/issues/13810))

### 1.72.0
1. Add an Admin API endpoint for user lookup based on third-party ID (3PID). Contributed by @ashfame. ([#14405](https://github.com/matrix-org/synapse/issues/14405))

