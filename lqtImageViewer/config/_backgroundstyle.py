import functools
from typing import Optional

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets


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

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"label={self.label},"
            f"background={self.primary},"
            f"foreground={self.secondary},"
            f"use_background_texture={self.use_background_texture},"
            f"texture_zoom_range={self.texture_zoom_range},"
            f")"
        )

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
    black_grid_dot = DottedBackgroundStyle(
        "Black Grid of Dots",
        QtGui.QColor(0, 0, 0),
        QtGui.QColor(30, 30, 30),
    )
    black = BaseBackgroundStyle(
        "Black",
        QtGui.QColor(0, 0, 0),
        QtGui.QColor(30, 30, 30),
    )
    dark_grid_dot = DottedBackgroundStyle(
        "Dark Grid of Dots",
        QtGui.QColor(25, 25, 25),
        QtGui.QColor(18, 18, 18),
    )
    customs: list[BaseBackgroundStyle] = []

    @classmethod
    def all(cls):
        all_styles = [
            cls.light,
            cls.light_grid_dot,
            cls.mid_grey,
            cls.black,
            cls.black_grid_dot,
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
