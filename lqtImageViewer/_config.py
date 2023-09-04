import dataclasses
import enum
from typing import Optional
from typing import Union

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets


class ShortcutModifierMatching(enum.Enum):
    exact = enum.auto()
    contains_all = enum.auto()
    contains_any = enum.auto()


@dataclasses.dataclass
class LIVKeyShortcut:
    key: Union[QtCore.Qt.Key, QtCore.Qt.MouseButton]
    """
    Main input to match the event against
    """

    modifiers: Optional[tuple[QtCore.Qt.KeyboardModifier, ...]]
    """
    Modifiers keys that must be active along the main key to be matched.
    
    - None means to ignore modifiers.
    - To specify that you don't want modifier pass an empty tuple.
    """

    modifier_matching: ShortcutModifierMatching = ShortcutModifierMatching.exact
    """
    Determine how strict the modifier must be matched against the event 
    """

    def match_event(
        self,
        event: QtCore.QEvent,
        modifier_matching: Optional[ShortcutModifierMatching] = None,
    ):
        """
        Return True if the given event match this shortcut.
        """
        modifier_matching = (
            self.modifier_matching if modifier_matching is None else modifier_matching
        )

        if isinstance(event, QtGui.QKeyEvent):
            key = event.key()
        elif isinstance(event, QtGui.QMouseEvent):
            key = event.button()
        else:
            return False

        modifiers = self.modifiers or tuple()
        exact_modifiers = QtCore.Qt.NoModifier
        for _modifier in modifiers:
            exact_modifiers = exact_modifiers | _modifier

        if (
            self.modifiers is not None
            and modifier_matching == ShortcutModifierMatching.exact
            and event.modifiers() != exact_modifiers
        ):
            return False
        elif (
            self.modifiers is not None
            and modifier_matching == ShortcutModifierMatching.contains_all
            and not all([event.modifiers() & modifier for modifier in self.modifiers])
        ):
            return False
        elif (
            self.modifiers is not None
            and modifier_matching == ShortcutModifierMatching.contains_any
            and not any([event.modifiers() & modifier for modifier in self.modifiers])
        ):
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
    view_coordinates1: LIVKeyShortcut
    view_coordinates2: LIVKeyShortcut
    set_coordinates_tiles: LIVKeyShortcut

    @classmethod
    def get_default(cls):
        return cls(
            reset_zoom=LIVKeyShortcut(QtCore.Qt.Key_Home, tuple()),
            reset_pan=LIVKeyShortcut(QtCore.Qt.Key_F, tuple()),
            change_background=LIVKeyShortcut(QtCore.Qt.Key_B, tuple()),
            pan1=LIVKeyShortcut(
                QtCore.Qt.LeftButton,
                (QtCore.Qt.AltModifier,),
                ShortcutModifierMatching.contains_all,
            ),
            pan2=LIVKeyShortcut(QtCore.Qt.MiddleButton, (QtCore.Qt.NoModifier,)),
            zoom2=LIVKeyShortcut(
                QtCore.Qt.MiddleButton,
                (QtCore.Qt.AltModifier,),
                ShortcutModifierMatching.contains_all,
            ),
            pick=LIVKeyShortcut(QtCore.Qt.LeftButton, (QtCore.Qt.ShiftModifier,)),
            unpick=LIVKeyShortcut(QtCore.Qt.LeftButton, (QtCore.Qt.ControlModifier,)),
            view_coordinates1=LIVKeyShortcut(
                QtCore.Qt.Key_Alt,
                (QtCore.Qt.ShiftModifier, QtCore.Qt.AltModifier),
            ),
            view_coordinates2=LIVKeyShortcut(
                QtCore.Qt.Key_Shift,
                (QtCore.Qt.AltModifier, QtCore.Qt.ShiftModifier),
            ),
            # not actually used
            set_coordinates_tiles=LIVKeyShortcut(
                QtCore.Qt.MiddleButton,
                (QtCore.Qt.AltModifier, QtCore.Qt.ShiftModifier),
            ),
        )

    def get_event_matching_shortcut(
        self, event: QtCore.QEvent
    ) -> Optional[LIVKeyShortcut]:
        """
        Get the shortcut that match the given event or None if not found.
        """
        for field in dataclasses.fields(self):
            field_value: LIVKeyShortcut = getattr(self, field.name)
            if field_value.match_event(event):
                return field_value
        return None


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
