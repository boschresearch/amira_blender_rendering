#!/usr/bin/env python

#
# At the moment we simply import all node setups. This is not very nice, and
# could be automated (see the automatic import of datasets in
# amira_deep_vision/aps)
#

# compositor nodes
from .compositor_renderedobjects import setup_compositor_nodes_rendered_objects

# material nodes
from .material_metal_tool_cap import setup_material_nodes_metal_tool_cap
