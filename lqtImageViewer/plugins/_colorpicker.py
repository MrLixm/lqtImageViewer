import enum
import logging
from typing import Optional

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from ._base import BaseScreenSpacePlugin


LOGGER = logging.getLogger(__name__)


def _pointf_to_point(pointf: QtCore.QPointF) -> QtCore.QPoint:
    """
    As toPoint() round 0.5 to 1.0, this is the alternative to round to lowest.
    """
    return QtCore.QPoint(int(pointf.x()), int(pointf.y()))


class ColorPickerControlState(enum.IntEnum):
    none = enum.auto()
    expand = enum.auto()
    center = enum.auto()
    border = enum.auto()


class ColorPickerPlugin(BaseScreenSpacePlugin):
    states = ColorPickerControlState

    class _Signals(QtCore.QObject):
        picked_color_changed = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self._control_state: ColorPickerControlState = ColorPickerControlState.none
        # in image pixel scene coordinates
        self._scene_rect = QtCore.QRect(0, 0, 10, 10)
        self._primary_color = QtGui.QColor(250, 10, 10)
        self.signals = self._Signals()
        self._update_position()
        self.hide()

    def _is_point_inside_image(self, point: QtCore.QPointF) -> bool:
        """
        Args:
            point: scene coordinates
        """
        return self.image_scene_rect.contains(self.map_to_screenspace(point))

    def _surface_rect(self, center: Optional[QtCore.QPointF] = None) -> QtCore.QRectF:
        surface = QtCore.QRectF(self._scene_rect)
        surface.moveCenter(center or QtCore.QPointF(0.0, 0.0))
        return self.map_to_screenspace(surface)

    def _center_rect(self) -> QtCore.QRectF:
        center_rect = QtCore.QRectF(0, 0, 12, 12)
        center_rect.moveCenter(self._surface_rect().center())
        return center_rect

    def _update_position(self):
        target = QtCore.QRectF(self._scene_rect).center()
        # setPos expect scene coordinates
        self.setPos(target)

    def _update_center_from(self, event_pos: QtCore.QPointF):
        """
        Args:
            event_pos: in world scene coordinates
        """
        pixel_coord = event_pos
        pixel_coord = _pointf_to_point(pixel_coord)
        self._scene_rect.moveCenter(pixel_coord)
        self._update_position()

    def get_picked_area(self) -> QtCore.QRect:
        """
        Return the area that is currently being picked, in image scene coordinates.
        """
        return QtCore.QRect(self._scene_rect).normalized()

    # Overrides

    def on_image_changed(self):
        self.hide()
        self.signals.picked_color_changed.emit()

    def set_visibility_from_scene_event(self, event: QtCore.QEvent):
        if not isinstance(event, QtWidgets.QGraphicsSceneMouseEvent):
            return

        event_pos = event.scenePos()

        if (
            (event.type() == event.Type.GraphicsSceneMousePress)
            and (
                self.shortcuts.pick.match_event(event)
                or self.shortcuts.pick_area_start.match_event(event)
            )
            and self._is_point_inside_image(event_pos)
        ):
            self.show()
            event_pos = _pointf_to_point(event_pos)
            self._scene_rect.setTopLeft(event_pos)
            self._scene_rect.setSize(QtCore.QSize(1, 1))
            self._update_position()
            self.signals.picked_color_changed.emit()

        elif (
            (event.type() == event.Type.GraphicsSceneMouseMove)
            and self.shortcuts.pick_area_expand.match_event(event)
            and self._is_point_inside_image(event_pos)
        ):
            event_pos = _pointf_to_point(event_pos)
            self._scene_rect.setBottomRight(event_pos)
            self._update_position()
            self.signals.picked_color_changed.emit()
            self._control_state = self.states.expand

        elif (event.type() == event.Type.GraphicsSceneMousePress) and (
            self.shortcuts.unpick.match_event(event)
        ):
            self.hide()
            self.signals.picked_color_changed.emit()

    def boundingRect(self) -> QtCore.QRectF:
        bounds = self._surface_rect().normalized()
        padding = 4
        # add 2 pixel of padding
        return bounds.adjusted(-padding, -padding, padding, padding)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        paint_rect = self._surface_rect().normalized()
        painter.setPen(QtGui.QPen(self._primary_color, 1))
        painter.drawRect(paint_rect)

        if self._scene_rect.size() != QtCore.QSize(1, 1):
            pen = painter.pen()
            pen.setWidth(5)
            painter.setPen(pen)
            painter.drawPoint(paint_rect.center())
            center_color = QtGui.QColor(self._primary_color)
            center_color.setAlpha(50)
            painter.setPen(QtGui.QPen(center_color, 1))
            painter.drawRect(self._center_rect())

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        # local widget coordinates
        center_rect = self._center_rect()

        if self._scene_rect.size() == QtCore.QSize(1, 1) or center_rect.contains(
            event.pos()
        ):
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
            self.signals.picked_color_changed.emit()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        self._control_state = self.states.none
