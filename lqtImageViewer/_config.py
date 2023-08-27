import dataclasses
from typing import Optional
from typing import Union

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets


@dataclasses.dataclass
class LIVKeyShortcut:
    key: Union[QtCore.Qt.Key, QtCore.Qt.MouseButton]
    modifier: Optional[QtCore.Qt.KeyboardModifier]

    def match_event(self, event: Union[QtGui.QKeyEvent, QtGui.QMouseEvent]):
        if isinstance(event, QtGui.QKeyEvent):
            key = event.key()
        else:
            key = event.button()

        if self.modifier is not None and event.modifiers() != self.modifier:
            return False

        if self.key != key:
            return False

        return True


@dataclasses.dataclass
class LIVKeyShortcuts:
    reset_zoom: LIVKeyShortcut
    change_background: LIVKeyShortcut
    reset_pan: LIVKeyShortcut
    pan1: LIVKeyShortcut
    pan2: LIVKeyShortcut
    zoom2: LIVKeyShortcut
    pick: LIVKeyShortcut
    unpick: LIVKeyShortcut

    @classmethod
    def get_default(cls):
        return cls(
            reset_zoom=LIVKeyShortcut(QtCore.Qt.Key_Home, None),
            change_background=LIVKeyShortcut(QtCore.Qt.Key_B, None),
            reset_pan=LIVKeyShortcut(QtCore.Qt.Key_F, None),
            pan1=LIVKeyShortcut(QtCore.Qt.LeftButton, QtCore.Qt.AltModifier),
            pan2=LIVKeyShortcut(QtCore.Qt.MiddleButton, QtCore.Qt.NoModifier),
            zoom2=LIVKeyShortcut(QtCore.Qt.MiddleButton, QtCore.Qt.AltModifier),
            pick=LIVKeyShortcut(QtCore.Qt.LeftButton, QtCore.Qt.ShiftModifier),
            unpick=LIVKeyShortcut(QtCore.Qt.LeftButton, QtCore.Qt.ControlModifier),
        )
