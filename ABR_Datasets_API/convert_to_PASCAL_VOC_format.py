# Object detection PASCAL VOC annotations format:
# https://towardsdatascience.com/coco-data-format-for-object-detection-a4c5eaf518c5

import os
import json
import xml.etree.ElementTree as ET

folder = '/home/pll1tv/PycharmProjects/amira_blender_rendering/src/amira_blender_rendering/$AMIRA_DATASETS/WorkstationScenarios-Train-Camera/Annotations/OpenCV'
json_filename = os.path.join(folder, 'camera_0000_location_0000.json')
xml_filename = json_filename[:-5] + '.xml'


#
def indent(elem, level=0):
    '''
    Creates a new line after subelement
    similar to tree.write(filename, pretty_print=True) option in lxml library

    Code from: https://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    '''
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# read json file
with open(json_filename) as json_file:
    data_json = json.load(json_file)

# create the file structure
root = ET.Element('annotation')

folder = ET.SubElement(root, 'folder')
folder.text = os.path.split(os.path.split(xml_filename)[0])[1]

filename = ET.SubElement(root, 'filename')
filename.text = os.path.split(xml_filename)[1][:-4]

path = ET.SubElement(root, 'path')
path.text = os.path.split(xml_filename)[0]

source = ET.SubElement(root, 'source')
database = ET.SubElement(source, 'database')
database.text = 'blender_industrial_dataset_2020_06'

size = ET.SubElement(root, 'size')
width = ET.SubElement(size, 'width')
width.text = str(data_json[0]['dimensions'][1])
height = ET.SubElement(size, 'height')
height.text = str(data_json[0]['dimensions'][0])
depth = ET.SubElement(size, 'depth')
depth.text = str(data_json[0]['dimensions'][2])

segmented = ET.SubElement(root, 'segmented')
segmented.text = str(0)

for obj in data_json:
    current_obj = ET.SubElement(root, 'object')
    name = ET.SubElement(current_obj, 'name')
    name.text = obj['object_class_name']
    pose = ET.SubElement(current_obj, 'pose')
    pose.text = 'Unspecified'
    truncated = ET.SubElement(current_obj, 'truncated')
    truncated.text = str(0)
    difficult = ET.SubElement(current_obj, 'difficult')
    difficult.text = str(0)
    bndbox = ET.SubElement(current_obj, 'bndbox')
    xmin = ET.SubElement(bndbox, 'xmin')
    xmin.text = str(obj['bbox']['corners2d'][0][0])
    ymin = ET.SubElement(bndbox, 'ymin')
    ymin.text = str(obj['bbox']['corners2d'][0][1])
    xmax = ET.SubElement(bndbox, 'xmax')
    xmax.text = str(obj['bbox']['corners2d'][1][0])
    ymax = ET.SubElement(bndbox, 'ymax')
    ymax.text = str(obj['bbox']['corners2d'][1][1])

# create a new XML file and write annotations to it
data = ET.ElementTree(root)
indent(root)
data.write(xml_filename)
