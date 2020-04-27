* Configuration Files
  As discussed, we have 6 scenes and 5 objects.

  + 1 scene used for the 5 objects singularly (1 instance) --> 5 scenarios
  + 1 scene used for multiple instances of single objects --> +5 scenarios
  + 1 scene used for 2 combinations of 2 objects (multi instances) --> +2 scenarios
  + 1 scene used for 3 combinations of 3 objects (multi instances) --> +3 scenarios
  + 1 scene used for all the objects (multi instances) --> +1 scenario
  + 1 scene used for objects from T-LESS --> +1 scenario

  Total of 17 scenarios --> 85k/17k train/test images

* Write documentation.
  New folder "docs" -> sphinx/reStructuredText. Move also the description of all
  configurations there

  + Describe BaseConfiguration
  + Describe Configuration for each scenario, and introduce there
  + Move all documentation elements from the README to corresponding files in docs

* Adapt other (old) scenarios to RenderManager backend

* Remove old / deprecated code

* Fix setup.py to make this a real installable package

  + change abr discovery in scripts/render_dataset.py to check if it is
    available as module.

* Update LICENSE with the license we select for open sourcing

* add VERSION to ini-files
