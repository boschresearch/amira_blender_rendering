"""The scenes module contains scene managers for various setups."""

# base classes
from .basescenemanager import BaseSceneManager
from .threepointlighting import ThreePointLighting
from .renderedobjectsbase import RenderedObjectsBase

# concrete scenes
from .simpletoolcap import SimpleToolCap
from .simpleletterb import SimpleLetterB
from .pandatable import PandaTable, ClutteredPandaTable, MultiObjectsClutteredPandaTable
from .workstationscenarios import WorkstationScenarios



