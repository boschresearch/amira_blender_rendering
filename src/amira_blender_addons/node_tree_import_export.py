#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

bl_info = {
    "name"        : "Node Tree Import/Export",
    "author"      : "",
    "version"     : (0, 1),
    "blender"     : (2, 8, 0),
    "location"    : "Node Editor > View",
    "description" : "Import and export a node tree",
    "warning"     : "",
    "wiki_url"    : "",
    "category"    : "Node",
}

import bpy
import bpy.types
import bpy.utils
from mathutils import Vector


def export_node_tree(node_tree):
    """ Serialize the writable attributes, enables saving with json

    Parameters
    ----------
    node_tree : bpy node_tree
        Typically an attribute of a material object

    Returns
    -------
    record : dict
    """
    record = dict(nodes=list(), links=list())

    for node in node_tree.nodes:
        node_dict = dict(type=node.bl_idname)
        for attr in dir(node):
            try:
                if node.is_property_readonly(attr):
                    continue
                val = getattr(node, attr)
                if val is None:
                    node_dict[attr] = val
                elif isinstance(val, (bool, str, int, float, tuple, list, dict)):
                    node_dict[attr] = val
                elif isinstance(val, Vector):
                    node_dict[attr] = val.to_tuple()
            except Exception:
                pass
        record["nodes"].append(node_dict)

    for link in node_tree.links:
        from_node = link.from_node.name
        from_index = int(link.from_socket.path_from_id().split("[")[-1].split("]")[0])
        to_node = link.to_node.name
        to_index = int(link.to_socket.path_from_id().split("[")[-1].split("]")[0])
        link_dict = dict(
            from_node=from_node,
            from_index=from_index,
            to_node=to_node,
            to_index=to_index,
        )
        record["links"].append(link_dict)

    return record


def clear_node_tree(material):
    nodes = material.node_tree.nodes
    for node in nodes:
        nodes.remove(node)


def import_node_tree(node_tree_dict, dst_material, clear=False):
    """ Configure the node_tree of a bpy material object

    Parameters
    ----------
    node_tree_dict : dict
        includes the bpy node type, and values for all the writable attributes
    """
    if clear:
        clear_node_tree(dst_material)

    dst_tree = dst_material.node_tree
    for src_node in node_tree_dict["nodes"]:
        dst_tree.nodes.new(type=src_node.pop("type"))
        dst_node = dst_material.node_tree.nodes[-1]
        for attr in src_node:
            setattr(dst_node, attr, src_node[attr])
    for src_link in node_tree_dict["links"]:
        from_node = src_link["from_node"]
        from_index = src_link["from_index"]
        to_node = src_link["to_node"]
        to_index = src_link["to_index"]
        dst_tree.links.new(
            dst_tree.nodes[to_node].inputs[to_index],
            dst_tree.nodes[from_node].outputs[from_index],
        )
    return


class NODE_MT_node_tree_import(bpy.types.Operator):
    bl_idname = 'addon.node_tree_import'
    bl_label = 'Import Node Tree'

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print("Import called, but not yet implemented")
        return {'FINISHED'}


class NODE_MT_node_tree_export(bpy.types.Operator):
    bl_idname = 'addon.node_tree_export'
    bl_label = 'Export Node Tree'

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print("Export called, but not yet implemented")
        return {'FINISHED'}


def _menu_func(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(NODE_MT_node_tree_import.bl_idname)
    layout.operator(NODE_MT_node_tree_export.bl_idname)


classes = (NODE_MT_node_tree_import,
           NODE_MT_node_tree_export)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_view.append(_menu_func)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.NODE_MT_view.remove(_menu_func)


if __name__ == "__main__":
    register()
