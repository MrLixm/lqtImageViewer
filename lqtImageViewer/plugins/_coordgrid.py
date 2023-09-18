import logging
import time
from typing import Optional

import qtpy
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from ._base import BaseScreenSpacePlugin


LOGGER = logging.getLogger(__name__)


def _generate_point_grid(
    surface: QtCore.QRectF,
    tiles_number: int,
) -> list[tuple[float, float]]:
    """
    Args:
        surface: surface used to paint and to extract coordinates from
        tiles_number: size of the grid in number of seperation
    """
    block_width = surface.width() / tiles_number
    block_height = surface.height() / tiles_number

    h_coordinates = [
        surface.left() + int(block_width * index + 0.5)
        for index in range(tiles_number + 1)
    ]
    v_coordinates = [
        surface.top() + int(block_height * index + 0.5)
        for index in range(tiles_number + 1)
    ]
    grid_coordinates = [
        (h_coordinate, v_coordinate)
        for h_coordinate in h_coordinates
        for v_coordinate in v_coordinates
    ]
    return grid_coordinates


def _draw_coordinates_grid(
    painter: QtGui.QPainter,
    source_grid: list[QtCore.QPointF],
    source_surface: QtCore.QRectF,
    screenspace_grid: list[QtCore.QPointF],
    screenspace_surface: QtCore.QRectF,
):
    """
    Use the given QPainter to draw the given grid of points.

    Args:
        painter: QPainter to draw on
        source_grid: original coordinates used for text drawing only
        source_surface: not used
        screenspace_grid: coordinates to draw point son the painter
        screenspace_surface: QRect corresponding to the surface covered by the screenspace grid
    """
    block_width: QtCore.QLineF = QtCore.QLineF(screenspace_grid[0], screenspace_grid[1])
    block_width: float = block_width.dy()

    text_rect = painter.fontMetrics().boundingRect("9")
    # hack to take in account font bearing
    text_rect = painter.fontMetrics().boundingRect(text_rect, 0, "9")
    # we have a line break, so it need ot be 2 time taller
    text_height = text_rect.height() * 2
    text_rect = QtCore.QRectF(0, 0, block_width, text_height)

    for index, screenspace_point in enumerate(screenspace_grid):
        x = screenspace_point.x()
        y = screenspace_point.y()

        AlignFlag = QtCore.Qt.AlignmentFlag

        alignment = AlignFlag.AlignHCenter | AlignFlag.AlignTop
        text_rect.moveCenter(screenspace_point)
        # negative offset is the margin between the point and the text
        text_rect.moveBottom(y - 5)

        if x == screenspace_surface.left():
            alignment = alignment ^ AlignFlag.AlignHCenter | AlignFlag.AlignLeft
            text_rect.moveLeft(x)
        elif x >= screenspace_surface.width() + screenspace_surface.left():
            alignment = alignment ^ AlignFlag.AlignHCenter | AlignFlag.AlignRight
            text_rect.moveRight(x)
        if y == screenspace_surface.top():
            alignment = alignment ^ AlignFlag.AlignTop | AlignFlag.AlignBottom
            text_rect.moveTop(y)
        # useless but there by default
        elif y >= screenspace_surface.height() + screenspace_surface.top():
            alignment = alignment ^ AlignFlag.AlignTop | AlignFlag.AlignTop
            text_rect.moveBottom(y)

        painter.save()
        painter.drawPoint(screenspace_point)
        x = int(source_grid[index].x())
        y = int(source_grid[index].y())
        painter.drawText(text_rect, alignment, f"x{x}\ny{y}")
        painter.restore()


class CoordinatesGridPlugin(BaseScreenSpacePlugin):
    """
    A screensapce plugin that display a grid of image pixel coordinates.

    The gris is made of "tiles" which amount can be controlled using a shortcut.
    The intersection of each tile is a point that will draw its coordinates.

    The plugin is only visible when a certain combination of key is pressed.
    """

    def __init__(self) -> None:
        super().__init__()
        self._rect = QtCore.QRectF(0, 0, 64, 64)
        self._tiles_number = 6
        self.hide()

    def set_visibility_from_scene_event(self, event: QtCore.QEvent):
        modifier_matching_any = (
            self.shortcuts.view_coordinates2.modifier_matching.contains_any
        )

        if (
            event.type() == event.Type.ShortcutOverride
            or event.type() == event.Type.KeyPress
        ) and (
            self.shortcuts.view_coordinates1.match_event(event)
            or self.shortcuts.view_coordinates2.match_event(event)
        ):
            self.show()

        elif event.type() == event.Type.KeyRelease and (
            self.shortcuts.view_coordinates1.match_event(event, modifier_matching_any)
            or self.shortcuts.view_coordinates2.match_event(
                event, modifier_matching_any
            )
        ):
            self.hide()

    def reload(self):
        image = self.image_item
        if image:
            self._rect = self.image_item.sceneBoundingRect()
        super().reload()

    def wheelEvent(self, event: QtWidgets.QGraphicsSceneWheelEvent):
        # can only be called when visible, which is when shortcut is active,
        # so no need to double-check modifiers
        if event.delta() > 0:
            self._tiles_number += 1
        else:
            self._tiles_number -= 1

        # TODO give a visual feedback for the current tile number
        self.update()

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(self.map_to_screenspace(self._rect))

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 150), 3))
        font = QtGui.QFont("Monospace")
        font.setStyleHint(QtGui.QFont.StyleHint.TypeWriter)
        font.setPointSize(8)
        if qtpy.QT6:
            font.setWeight(font.Weight.Medium)
        else:
            font.setWeight(500)
        painter.setFont(font)

        grid = _generate_point_grid(self._rect, self._tiles_number)
        grid = [QtCore.QPointF(x, y) for x, y in grid]
        screenspace_rect = self.boundingRect()
        screenspace_grid = [self.map_to_screenspace(point) for point in grid]

        _draw_coordinates_grid(
            painter,
            source_grid=grid,
            source_surface=self._rect,
            screenspace_grid=screenspace_grid,
            screenspace_surface=screenspace_rect,
        )
