"""
A plugin system to add arbitary QGraphicItem over the viewport.
"""
__all__ = [
    "BasePluginType",
    "BaseScreenSpacePlugin",
    "ColorPickerPlugin",
    "CoordinatesGridPlugin",
]

from ._base import BasePluginType
from ._base import BaseScreenSpacePlugin
from ._colorpicker import ColorPickerPlugin
from ._coordgrid import CoordinatesGridPlugin
