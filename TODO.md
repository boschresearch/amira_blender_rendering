# TODO

This file contains a list of items that need to be addressed in the future.
The content of this file can be used to synthesize fine-grained JIRA items.

IMPORTANT high level tasks:

* derive 3 month plan
  + user stories, user concepts
  + what's our realistic goal?
  + what's the benefit of our tool? (use typical Bosch-speak to convince people
    why it's important to work on it)

Below contains more detailed items

* Document all ABR users
  - APA
  - DLR
  - RTC China
  - ARM Project
* Make a nice landing page for ABR for new users?
* Mockup for a Blender Plugin to allow estimation of development effort
  + Examine the workflow with external users -> Alona; generally APA
* Evaluate blender version compatibility
* Store all models with the same scaling
* Store all models with geometrical center at zero (0)
* Additional outputs
  + Depth Map as PNG (in addition to Z Buffer/range map in EXR)
    - Document issues with PNG and color spaces (sRGB is non-linear but
      typically used when writing PNG files. This is a remarkably bad format to
      store linear data, and the reason why people use EXR and HDF5)
  + Disparity maps
  + Visibility ratio
* Further clarify what levels of realism are required, and how to improve
  realism
  + Motion Blur might be required. Discussion with DLR showed that some
    reviewers complain when datasets are too perfect.
  + Make scenes more complex, with more textures, models, clutter, etc
  + (Continuous) Dynamics in the scene (both camera and objects)
    - moving objects (example conveyor belt)
    - moving sensors
  + Sensor realism
    - noise
    - resolution: rgb and depth maps sometimes come with different resolutions
        - e.g., RealSense camera, rgb: 960x540 depth: 640x480
    - distance between RGB and depth sensors (are they treated as one camera or as two separate ones?)
* Decide and discuss an interface between ABR and APS
* User Stories and Use Cases
  + What could users achieve with ABR?
  + What would be the incentive to use ABR?
  + What do we not support users to make, what won't we implement (because of
    time, engineering effort, etc.)
  + Use Case: Point Cloud Data


**User Stories**

1. As a Blender user I want to be able to automatically trigger data generation

*Assumption(s)*: Typical blender users with Blender modeling and rendering knowledge

*Problem*: Currently, in Blender is possible to render single images or video sequences.
Users must trigger rendering manually via Blender's GUI. It is possible to render single
images and video sequences but neither to automatically generate multiple randomization of the same
scene nor to automatically trigger rendering from multiple cameras

*Why(s)*: As a user I want to be able to model my desired scene but also render quickly multiple views and/or
multiple variations of the scene

*DoD(s)*: ABR Blender Plug-in available


2. As a Blender user and big-data practitioner, I want to be able to automatically generate large amount of data

*Assumption(s)*: Entry-level and/or typical blender users with Blender modeling and rendering knowledge 
working with big-data

*Problem*: Currently, in Blender is possible to render single images or video sequences.
Automatically render a predefined number of images is not possible.

*Why(s)*: As a user I can model my desired scene. In addition as a big-data practitioner I want to commence
rendering of large amount of data

*DoD(s)*: ABR Blender Plug-in available


3. As a Compute Vision practitioner, I want to be able to automatically generate large amount of data

*Assumption(s)*: 
  1. CV practitioner in e.g., an industrial context. Blender knowledge: Yes/some
  2. CV practitioner in e.g., an industrial context. Blender knowledge: No

*Problem*: Currently, in Blender is possible to render single images or video sequences.
Automatically render a predefined number of images is not possible.

*Why(s)*:
 - As a CV practioner and blender user I want to model my scene by also generate large amount of data
 to test/train my technology
 - As a CV practitioner w/o blender knowledge, I want to quickly generate large amount of data to test/train
 my technology but w/o blender modeling knowledge I can rely on small variations of predefined scenes

*DoD(s)*:
- ABR Blender Plug-in available [if Ass. 1]
- ABR as a python library/OSS project available [if Ass. 2]


4. As a Compute Vision researcher, I want to be able to automatically generate large amount of data

*Assumption(s)*:
  1. CV researcher. Blender knowledge: Yes/some
  2. CV researcher. Blender knowledge: No

*Problem*: Currently, in Blender is possible to render single images or video sequences.
Automatically render a predefined number of images is not possible.

*Why(s)*:
 - As a CV practioner and blender user I want to play around with large amount of data to develop and test
 my new technology.
 - As a CV practitioner w/o blender knowledge, I want to quickly generate large amount of data to 
 develop my knew technology reling on small variations of predefined scenes
 
*DoD(s)*:
- ABR Blender Plug-in available [if Ass. 1]
- ABR as a python library/OSS project available [if Ass. 2]

5. As a developer/researcher with SW developer skills I don't want to develop my own custom
rendering tool but I would gladly contribute to the development of existing ones

*Assumption(s)*: Researcher/developer w some SW developer skills. 
Blender knowledge: Yes/some (mainly in Blender's Python API)

*Problem*: Integrate solutions for large amount of photorealistic physics-based rendering not availabel 
(to the best of my knowledge)

*Why(s)*: As a developer I want to rely on existing tools but I am happy to contribute
 
*DoD(s)*: 
- ABR Blender Plug-in available [if extensive Blender knowledge]
- ABR as a python library/OSS project available [if limited Blender knowldege]
