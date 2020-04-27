"""The scenes module contains scene managers for various setups."""

# base classes
from .basescenemanager import BaseSceneManager
from .baseconfiguration import BaseConfiguration
from .threepointlighting import ThreePointLighting

# composition classes, if inheritance should or cannot be used
from .rendermanager import RenderManager

# concrete scenes
from .simpletoolcap import SimpleToolCap
from .workstationscenarios import WorkstationScenarios


