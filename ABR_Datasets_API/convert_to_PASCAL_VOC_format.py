# Object detection PASCAL VOC annotations format:
# https://towardsdatascience.com/coco-data-format-for-object-detection-a4c5eaf518c5

import os
import json
import xml.etree.ElementTree as ET

folder = '/home/pll1tv/PycharmProjects/ActivePerception/create_synthetic_dataset/$AMIRA_DATASETS/WorkstationScenarios-Train-Camera/Annotations/OpenCV'
json_filename = '/home/pll1tv/PycharmProjects/ActivePerception/create_synthetic_dataset/$AMIRA_DATASETS/WorkstationScenarios-Train-Camera/Annotations/OpenCV/camera_0000_location_0000.json'
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
# item1 = ET.SubElement(items, 'itemA')
# item2 = ET.SubElement(items, 'itemB')
# item1.set('name', 'item11')
# item2.set('name', 'item21')
# item1.text = 'item1abc'
# item2.text = 'item2abc'
#
# mydata = ET.tostring(data_xml)
# myfile = open(xml_filename, "w")
# myfile.write(mydata)

# xml.etree.ElementTree.SubElement(parent, tag, attrib={}, **extra)

# create a new XML file with the results
mydata = ET.ElementTree(root)
indent(root)
mydata.write(xml_filename)

### ADD LINK TO PASCAL ANNOTATION FORMAT ###
''' PASCAL ANNOTATION EXAMPLE
<annotation>
	<folder>frames_priority_decimation</folder>
	<filename>frame001003_vid0002.png</filename>
	<path>E:\Downloads\Work\Bosch\frames_priority_decimation\frame001003_vid0002.png</path>
	<source>
		<database>Unknown</database>
	</source>
	<size>
		<width>640</width>
		<height>360</height>
		<depth>3</depth>
	</size>
	<segmented>0</segmented>
	<object>
		<name>scissors</name>
		<pose>Unspecified</pose>
		<truncated>0</truncated>
		<difficult>0</difficult>
		<bndbox>
			<xmin>313</xmin>
			<ymin>35</ymin>
			<xmax>438</xmax>
			<ymax>316</ymax>
		</bndbox>
	</object>
	<object>
		<name>oring</name>
		<pose>Unspecified</pose>
		<truncated>0</truncated>
		<difficult>0</difficult>
		<bndbox>
			<xmin>340</xmin>
			<ymin>158</ymin>
			<xmax>404</xmax>
			<ymax>251</ymax>
		</bndbox>
	</object>
	<object>
		<name>ruler</name>
		<pose>Unspecified</pose>
		<truncated>1</truncated>
		<difficult>0</difficult>
		<bndbox>
			<xmin>229</xmin>
			<ymin>15</ymin>
			<xmax>319</xmax>
			<ymax>360</ymax>
		</bndbox>
	</object>
</annotation>
'''
