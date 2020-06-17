#!/usr/bin/env python

# Copyright (c) 2020 - for information on the respective copyright owner
# see the NOTICE file and/or the repository
# <https://github.com/boschresearch/amira-blender-rendering>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import xml.etree.ElementTree as ET


def to_PASCAL_VOC(fpath_json):
    """
    Converts data annotations from json to xml according to PASCAL VOC format
    https://towardsdatascience.com/coco-data-format-for-object-detection-a4c5eaf518c5

    Args: fpath_json - path to json annotation file to convert

    """
    # manage directories
    json_folder = os.path.split(fpath_json)[0]
    filename = os.path.split(fpath_json)[1][:-5]

    xml_folder = os.path.join(os.path.split(json_folder)[0], 'xml')
    os.makedirs(xml_folder, exist_ok=True)
    fpath_xml = os.path.join(xml_folder, filename + '.xml')

    space = '  '
    # read json file
    with open(fpath_json) as json_file:
        data_json = json.load(json_file)

    # create the file structure
    root = ET.Element('annotation')
    root.text = '\n' + space

    folder = ET.SubElement(root, 'folder')
    folder.text = os.path.split(os.path.split(fpath_xml)[0])[1]
    folder.tail = '\n' + space

    filename = ET.SubElement(root, 'filename')
    filename.text = os.path.split(fpath_xml)[1][:-4]
    filename.tail = '\n' + space

    path = ET.SubElement(root, 'path')
    path.text = os.path.split(fpath_xml)[0]
    path.tail = '\n' + space

    source = ET.SubElement(root, 'source')
    source.text = '\n' + 2 * space
    database = ET.SubElement(source, 'database')
    database.text = 'blender_industrial_dataset_2020_06'
    database.tail = '\n' + space
    source.tail = '\n' + space

    size = ET.SubElement(root, 'size')
    size.text = '\n' + 2 * space
    width = ET.SubElement(size, 'width')
    width.text = str(data_json[0]['dimensions'][1])
    width.tail = '\n' + 2 * space
    height = ET.SubElement(size, 'height')
    height.text = str(data_json[0]['dimensions'][0])
    height.tail = '\n' + 2 * space
    depth = ET.SubElement(size, 'depth')
    depth.text = str(data_json[0]['dimensions'][2])
    depth.tail = '\n' + space
    size.tail = '\n' + space

    segmented = ET.SubElement(root, 'segmented')
    segmented.text = str(0)
    segmented.tail = '\n' + space

    for obj_idx, obj in enumerate(data_json):
        current_obj = ET.SubElement(root, 'object')
        current_obj.text = '\n' + 2 * space
        name = ET.SubElement(current_obj, 'name')
        name.text = obj['object_class_name']
        name.tail = '\n' + 2 * space
        pose = ET.SubElement(current_obj, 'pose')
        pose.text = 'Unspecified'
        pose.tail = '\n' + 2 * space
        truncated = ET.SubElement(current_obj, 'truncated')
        truncated.text = str(0)
        truncated.tail = '\n' + 2 * space
        difficult = ET.SubElement(current_obj, 'difficult')
        difficult.text = str(0)
        difficult.tail = '\n' + 2 * space
        bndbox = ET.SubElement(current_obj, 'bndbox')
        bndbox.text = '\n' + 3 * space
        xmin = ET.SubElement(bndbox, 'xmin')
        xmin.text = str(obj['bbox']['corners2d'][0][0])
        xmin.tail = '\n' + 3 * space
        ymin = ET.SubElement(bndbox, 'ymin')
        ymin.text = str(obj['bbox']['corners2d'][0][1])
        ymin.tail = '\n' + 3 * space
        xmax = ET.SubElement(bndbox, 'xmax')
        xmax.text = str(obj['bbox']['corners2d'][1][0])
        xmax.tail = '\n' + 3 * space
        ymax = ET.SubElement(bndbox, 'ymax')
        ymax.text = str(obj['bbox']['corners2d'][1][1])
        ymax.tail = '\n' + 2 * space
        bndbox.tail = '\n' + space
        if obj_idx == len(data_json) - 1:  # if last object
            current_obj.tail = '\n'
        else:
            current_obj.tail = '\n' + space

    # create a new XML file and write annotations to it
    data = ET.ElementTree(root)
    # indent(root)
    data.write(fpath_xml)
