import dataclasses
import enum
import functools
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


# note: not using a dataclass because unhashable QColor
class BaseBackgroundStyle:
    """

    Args:
        label: a pretty name for this style
        background:
        foreground:
        use_background_texture:
            False indicate we don't care abotu the background texture
        texture_zoom_range:
            allow to hide the background texture depending on the view zoom level.
            zoom range is [0-1+] where 1 == no zoom
    """

    def __init__(
        self,
        label: str,
        background: QtGui.QColor,
        foreground: QtGui.QColor,
        use_background_texture: bool = True,
        texture_zoom_range: tuple[Optional[float], Optional[float]] = (0.3, None),
    ):
        self.label = label
        self.primary = background
        self.secondary = foreground
        self.use_background_texture = use_background_texture
        self.texture_zoom_range = texture_zoom_range

    def should_use_background_texture(self, zoom: Optional[float] = None) -> bool:
        """
        Return True if the instance config imply that the backgroudn texture must be used.
        """
        draw_texture = False
        zoom_min = self.texture_zoom_range[0]
        zoom_max = self.texture_zoom_range[1]

        if self.use_background_texture:
            draw_texture = True
        if zoom_min is not None and zoom is not None and zoom < zoom_min:
            draw_texture = False
        if zoom_max is not None and zoom is not None and zoom > zoom_max:
            draw_texture = False

        return draw_texture

    @functools.cache
    def generate_background_brush(self, draw_texture: bool) -> QtGui.QBrush:
        """
        Return the QBrush to use for drawing backgrounds.
        """
        brush = QtGui.QBrush(self.primary)
        texture = self.generate_background_texture()

        if texture and draw_texture:
            brush.setTexture(texture)
            # hack to avoid pixelated image when zooming
            transform = QtGui.QTransform()
            transform.scale(0.05, 0.05)
            brush.setTransform(transform)

        return brush

    def generate_background_texture(self) -> Optional[QtGui.QPixmap]:
        """
        Generate a QPixmap to tile in a QBrush.

        It is recommended to create a large pattern as this one will be scale down
        in the view, so zooming will not produce pixelised preview.
        """
        return None


class DottedBackgroundStyle(BaseBackgroundStyle):
    def generate_background_texture(self) -> Optional[QtGui.QPixmap]:
        resolution = 1024
        dot_size = 50
        center = QtCore.QPointF(resolution // 2, resolution // 2)

        pixmap = QtGui.QPixmap(QtCore.QSize(resolution, resolution))
        pixmap.fill(self.primary)

        gradient = QtGui.QRadialGradient(center, 50)
        gradient.setColorAt(1, QtCore.Qt.transparent)
        gradient.setColorAt(0, self.secondary)
        gradient.setFocalRadius(44)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(painter.Antialiasing)

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(gradient))
        painter.drawEllipse(center, dot_size, dot_size)
        painter.end()
        return pixmap


class BackgroundStyleLibrary:
    """
    Collection of style the background of the viewport can be set to.
    """

    light = BaseBackgroundStyle(
        "Light",
        QtGui.QColor(240, 240, 238),
        QtGui.QColor(200, 200, 200),
    )
    light_grid_dot = DottedBackgroundStyle(
        "Light Grid of Dots",
        QtGui.QColor(240, 240, 238),
        QtGui.QColor(200, 200, 200),
    )
    mid_grey = BaseBackgroundStyle(
        "Mid Grey",
        QtGui.QColor(125, 125, 125),
        QtGui.QColor(100, 100, 100),
    )
    dark_grid_dot = DottedBackgroundStyle(
        "Dark Grid of Dots",
        QtGui.QColor(0, 0, 0),
        QtGui.QColor(30, 30, 30),
    )
    dark = BaseBackgroundStyle(
        "Dark",
        QtGui.QColor(0, 0, 0),
        QtGui.QColor(30, 30, 30),
    )
    customs: list[BaseBackgroundStyle] = []

    @classmethod
    def all(cls):
        all_styles = [
            cls.light,
            cls.light_grid_dot,
            cls.mid_grey,
            cls.dark,
            cls.dark_grid_dot,
        ]
        all_styles.extend(cls.customs)
        return all_styles

    @classmethod
    def next(cls, style: BaseBackgroundStyle) -> BaseBackgroundStyle:
        all_styles = cls.all()
        index = all_styles.index(style)
        try:
            return all_styles[index + 1]
        except IndexError:
            return all_styles[0]

    @classmethod
    def add_custom_style(cls, new_style: BaseBackgroundStyle):
        if new_style in cls.customs:
            return
        cls.customs.append(new_style)
