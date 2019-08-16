#!/usr/bin/env python

#
# At the moment we simply import all node setups. This is not very nice, and
# could be automated (see the automatic import of datasets in
# amira_deep_vision/aps)
#

# compositor nodes
from .compositor_renderedobjects import CompositorNodesOutputRenderedObject

# material nodes
from . import material_metal_tool_cap
from . import material_3Dprinted_plastic
