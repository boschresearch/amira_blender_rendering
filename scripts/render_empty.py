"""
This script is only used to determine blender behavior.

For instance, blender might segfault after running a python script. It is
currently unclear what the reason for the segfault is, but this script can help
to identify and trace issues.
"""
import bpy

def main():
    # gracefully close blender
    bpy.ops.wm.quit_blender()

if __name__ == "__main__":
    main()
