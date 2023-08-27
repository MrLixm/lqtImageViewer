import dataclasses
import enum
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


@dataclasses.dataclass(frozen=True)
class _BackgroundStyle:
    label: str
    primary: QtGui.QColor
    secondary: QtGui.QColor
    draw_grid: bool


class BackgroundStyle(enum.Enum):
    """
    Collection of style the background of the viewport can be set to.
    """

    light = _BackgroundStyle(
        "Light",
        QtGui.QColor(240, 240, 238),
        QtGui.QColor(200, 200, 200),
        False,
    )
    light_grid_dot = _BackgroundStyle(
        "Light Grid of Dots",
        QtGui.QColor(240, 240, 238),
        QtGui.QColor(200, 200, 200),
        True,
    )
    mid_grey = _BackgroundStyle(
        "Mid Grey",
        QtGui.QColor(125, 125, 125),
        QtGui.QColor(100, 100, 100),
        False,
    )
    dark_grid_dot = _BackgroundStyle(
        "Dark Grid of Dots",
        QtGui.QColor(0, 0, 0),
        QtGui.QColor(30, 30, 30),
        True,
    )
    dark = _BackgroundStyle(
        "Dark",
        QtGui.QColor(0, 0, 0),
        QtGui.QColor(30, 30, 30),
        False,
    )

    @classmethod
    def all(cls):
        return [
            cls.light,
            cls.light_grid_dot,
            cls.mid_grey,
            cls.dark,
            cls.dark_grid_dot,
        ]

    @classmethod
    def next(cls, style: "BackgroundStyle"):
        all_styles = cls.all()
        index = all_styles.index(style)
        try:
            return all_styles[index + 1]
        except IndexError:
            return all_styles[0]
