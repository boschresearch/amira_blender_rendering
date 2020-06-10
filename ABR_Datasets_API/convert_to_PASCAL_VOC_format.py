import os
import json
import xml.etree.ElementTree as ET

json_filename = '/home/pll1tv/PycharmProjects/ActivePerception/create_synthetic_dataset/$AMIRA_DATASETS/WorkstationScenarios-Train-Camera/Annotations/OpenCV/camera_0000_location_0000.json'
xml_filename = json_filename[:-5] + '.xml'
# read json file
with open(json_filename) as json_file:
    data = json.load(json_file)


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