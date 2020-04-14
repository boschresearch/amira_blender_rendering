"""The scenes module contains scene managers for various setups."""

# base classes
from .basescenemanager import BaseSceneManager
from .baseconfiguration import BaseConfiguration
from .threepointlighting import ThreePointLighting
from .renderedobjectsbase import RenderedObjectsBase

# composition classes, if inheritance should or cannot be used
from .rendermanager import RenderManager

# concrete scenes
from .simpletoolcap import SimpleToolCap
from .simpleletterb import SimpleLetterB
from .pandatable import PandaTable, ClutteredPandaTable, MultiObjectsClutteredPandaTable
from .workstationscenarios import WorkstationScenarios


