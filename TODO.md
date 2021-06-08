# Todo
This document describes what need to be changed or added due to the changes made by [matrix-synapse](https://github.com/matrix-org/synapse/releases). Only major release of Synapse (x.y.0) will be included here.
## Synapse 1.36.0
1. Add new admin APIs for unprotecting local media from quarantine. Contributed by @dklimpel. ([#10040](https://github.com/matrix-org/synapse/issues/10040)) -> Test needed
2. Add new admin APIs to remove media by media ID from quarantine. Contributed by @dklimpel. ([#10044](https://github.com/matrix-org/synapse/issues/10044)) -> Test needed
3. Make reason and score parameters optional for reporting content. Implements MSC2414. Contributed by Callum Brown. ([#10077](https://github.com/matrix-org/synapse/issues/10077)) -> Test needed
