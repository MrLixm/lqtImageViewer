import enum
import logging
from typing import Optional

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._base import BaseScreenSpacePlugin


LOGGER = logging.getLogger(__name__)


class ColorPickerControlState(enum.IntEnum):
    none = enum.auto()
    center = enum.auto()
    border = enum.auto()


class ColorPickerPlugin(BaseScreenSpacePlugin):
    states = ColorPickerControlState

    def __init__(self) -> None:
        super().__init__()
        self._control_state: ColorPickerControlState = ColorPickerControlState.none
        # in image pixel scene coordinates
        self._scene_rect = QtCore.QRect(0, 0, 10, 10)
        self._update_position()

    def _surface_rect(self, center: Optional[QtCore.QPointF] = None) -> QtCore.QRectF:
        surface = QtCore.QRectF(self._scene_rect)
        surface.moveCenter(center or QtCore.QPointF(0.0, 0.0))
        return self.map_to_screenspace(surface)

    def _update_position(self):
        target = self._scene_rect.center()
        # setPos expect scene coordinates
        self.setPos(QtCore.QPointF(target))

    def _update_center_from(self, event_pos: QtCore.QPointF):
        """
        Args:
            event_pos: in world scene coordinates
        """
        pixel_coord = event_pos
        pixel_coord = pixel_coord.toPoint()
        self._scene_rect.moveCenter(pixel_coord)
        self._update_position()

    def set_center(self, center: QtCore.QPoint):
        """

        Args:
            center: in world scene coordinates
        """
        self._scene_rect.moveCenter(center)

    # Overrides

    def boundingRect(self) -> QtCore.QRectF:
        bounds = self._surface_rect()
        padding = 4
        # add 2 pixel of padding
        return bounds.adjusted(-padding, -padding, padding, padding)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        paint_rect = self._surface_rect()
        painter.setPen(QtGui.QPen(QtGui.QColor("red"), 2))
        painter.drawRect(paint_rect)

        if self._scene_rect.size() != QtCore.QSize(1, 1):
            pen = painter.pen()
            pen.setWidth(4)
            painter.setPen(pen)
            painter.drawPoint(paint_rect.center())

        painter.setPen(QtGui.QPen(QtGui.QColor("blue"), 2))

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if event.button() != QtCore.Qt.LeftButton:
            return

        image_rect = self.image_scene_rect
        pos = self.map_to_screenspace(event.scenePos())
        # TODO delete cause this should never happen
        if not image_rect.contains(pos):
            return

        # local widget coordinates
        center_rect = QtCore.QRectF(0, 0, 8, 8)
        center_rect.moveCenter(self._surface_rect().center())
        if center_rect.contains(event.pos()):
            self._control_state = self.states.center
        else:
            self._control_state = self.states.border

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if self._control_state == self.states.none:
            return

        if self._control_state == self.states.center:
            pos = event.scenePos()
            future_rect = self._surface_rect()
            future_rect.moveCenter(
                QtCore.QPointF(self.map_to_screenspace(pos).toPoint())
            )
            if self.image_scene_rect.united(future_rect) != self.image_scene_rect:
                return

            self._update_center_from(pos)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        self._control_state = self.states.none
