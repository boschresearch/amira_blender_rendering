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
* Further clarify what levels of realism are required, and how to improve
  realism
  + Motion Blur might be required. Discussion with DLR showed that some
    reviewers complain when datasets are too perfect.
  + Make scenes more complex, with more textures, models, etc
  + Dynamics in the scene
    - moving objects (example conveyor belt)
    - moving sensors
  + Sensor realism
    - noise
    - resolution
    - distance between RGB and depth sensors
* Decide and discuss an interface between ABR and APS
* User Stories and Use Cases
  + What could users achieve with ABR?
  + What would be the incentive to use ABR?
  + What do we not support users to make, what won't we implement (because of
    time, engineering effort, etc.)
  + Use Case: Point Cloud Data


