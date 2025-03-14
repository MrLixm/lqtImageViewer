import dataclasses
import enum
from typing import Optional
from typing import Union

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets


class ShortcutModifierMatching(enum.Enum):
    """
    Amount of precision required to match an event modifiers against a known collection of modifiers.
    """

    exact = enum.auto()
    contains_all = enum.auto()
    contains_any = enum.auto()


@dataclasses.dataclass
class LIVKeyShortcut:
    """
    Store a unique combinations of key to verify it matches against Qt QEvent.
    """

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
        elif isinstance(event, (QtGui.QMouseEvent, QtWidgets.QGraphicsSceneMouseEvent)):
            key = event.button()
        else:
            return False

        modifiers = self.modifiers or tuple()
        exact_modifiers = QtCore.Qt.KeyboardModifier.NoModifier
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
    """
    Mapping of shortcuts with their intended usage across the image viewer.
    """

    reset_zoom: LIVKeyShortcut
    change_background: LIVKeyShortcut
    reset_pan: LIVKeyShortcut
    pan1: LIVKeyShortcut
    pan2: LIVKeyShortcut
    zoom2: LIVKeyShortcut
    pick: LIVKeyShortcut
    pick_area_start: LIVKeyShortcut
    pick_area_expand: LIVKeyShortcut
    unpick: LIVKeyShortcut
    view_coordinates1: LIVKeyShortcut
    view_coordinates2: LIVKeyShortcut
    set_coordinates_tiles: LIVKeyShortcut
    rotate_90_up: LIVKeyShortcut
    rotate_90_down: LIVKeyShortcut
    clear: LIVKeyShortcut

    @classmethod
    def get_default(cls):
        """
        Generate an instance with defaults key bindings.
        """
        Modifiers = QtCore.Qt.KeyboardModifier

        return cls(
            reset_zoom=LIVKeyShortcut(QtCore.Qt.Key.Key_Home, tuple()),
            reset_pan=LIVKeyShortcut(QtCore.Qt.Key.Key_F, tuple()),
            change_background=LIVKeyShortcut(QtCore.Qt.Key.Key_B, tuple()),
            pan1=LIVKeyShortcut(
                QtCore.Qt.MouseButton.LeftButton,
                (Modifiers.AltModifier,),
                ShortcutModifierMatching.contains_all,
            ),
            pan2=LIVKeyShortcut(
                QtCore.Qt.MouseButton.MiddleButton,
                (Modifiers.NoModifier,),
            ),
            zoom2=LIVKeyShortcut(
                QtCore.Qt.MouseButton.MiddleButton,
                (Modifiers.AltModifier,),
                ShortcutModifierMatching.contains_all,
            ),
            pick=LIVKeyShortcut(
                QtCore.Qt.MouseButton.LeftButton,
                (Modifiers.ControlModifier,),
            ),
            pick_area_start=LIVKeyShortcut(
                QtCore.Qt.MouseButton.LeftButton,
                (Modifiers.ControlModifier, Modifiers.ShiftModifier),
            ),
            pick_area_expand=LIVKeyShortcut(
                QtCore.Qt.MouseButton.NoButton,
                (Modifiers.ControlModifier, Modifiers.ShiftModifier),
            ),
            unpick=LIVKeyShortcut(
                QtCore.Qt.MouseButton.RightButton,
                (Modifiers.ControlModifier,),
            ),
            view_coordinates1=LIVKeyShortcut(
                QtCore.Qt.Key.Key_Alt,
                (Modifiers.ShiftModifier, Modifiers.AltModifier),
            ),
            view_coordinates2=LIVKeyShortcut(
                QtCore.Qt.Key.Key_Shift,
                (Modifiers.AltModifier, Modifiers.ShiftModifier),
            ),
            # not actually used
            set_coordinates_tiles=LIVKeyShortcut(
                QtCore.Qt.MouseButton.MiddleButton,
                (Modifiers.AltModifier, Modifiers.ShiftModifier),
            ),
            rotate_90_up=LIVKeyShortcut(
                QtCore.Qt.Key.Key_Q,
                tuple(),
            ),
            rotate_90_down=LIVKeyShortcut(
                QtCore.Qt.Key.Key_E,
                tuple(),
            ),
            clear=LIVKeyShortcut(
                QtCore.Qt.Key.Key_C,
                (Modifiers.AltModifier,),
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
