"""
This script is used to determine blender behavior.

For instance, blender segfaults after running a python script. It is currently
unclear what the reason for the segfault is.
"""
import bpy

def main():
    # gracefully close blender
    bpy.ops.wm.quit_blender()

if __name__ == "__main__":
    main()
