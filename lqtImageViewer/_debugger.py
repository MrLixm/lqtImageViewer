from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._viewport import LqtImageViewport


def stringify_qobject(qobject: QtCore.QObject) -> str:
    if isinstance(qobject, QtGui.QTransform):
        converted = [
            round(getattr(qobject, f"m{mid}")(), 3)
            for mid in [11, 12, 13, 21, 22, 23, 31, 32, 33]
        ]
        converted = f"QTransform{converted}"
        return converted

    converted = str(qobject)
    converted = converted.split("QtCore.")[-1]
    converted = converted.split("QtGui.")[-1]
    converted = converted.split("QtWidgets.")[-1]
    return converted


def modifier_to_str(modifiers: QtCore.Qt.KeyboardModifier) -> list[str]:
    modifiers_names = []

    if modifiers & QtCore.Qt.ShiftModifier:
        modifiers_names.append("Shift")
    if modifiers & QtCore.Qt.AltModifier:
        modifiers_names.append("Alt")
    if modifiers & QtCore.Qt.ControlModifier:
        modifiers_names.append("Ctrl")

    return modifiers_names


def mouse_button_to_str(mouse_button: QtCore.Qt.MouseButton):
    if mouse_button == QtCore.Qt.LeftButton:
        return "LMB"
    if mouse_button == QtCore.Qt.RightButton:
        return "RMB"
    if mouse_button == QtCore.Qt.MiddleButton:
        return "MMB"


class KeyMouseDisplayWidget(QtWidgets.QLabel):
    """
    QLabel that display key and mouse press from global application scope.
    """

    fade_out_timer = 800

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timer_update = QtCore.QTimer()
        self._timer_update.timeout.connect(self._on_timer_timeout)
        QtWidgets.QApplication.instance().installEventFilter(self)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        modifier_text = ""
        key_text = ""
        mouse_text = ""
        need_update = False

        if event.type() == QtCore.QEvent.KeyPress:
            event: QtGui.QKeyEvent
            modifier_text = modifier_to_str(event.modifiers())
            modifier_text = " + ".join(modifier_text)
            key_text = f"{event.text()}"
            need_update = True

        elif event.type() == QtCore.QEvent.MouseButtonPress:
            event: QtGui.QMouseEvent
            modifier_text = modifier_to_str(event.modifiers())
            modifier_text = " + ".join(modifier_text)
            mouse_text = mouse_button_to_str(event.button())
            need_update = True

        elif event.type() == QtCore.QEvent.Wheel:
            mouse_text = "Scroll"
            need_update = True

        if need_update:
            self._timer_update.stop()
            if modifier_text and key_text:
                modifier_text += " + "
            display_text = f"{modifier_text}{key_text} | {mouse_text}"
            self.setText(display_text)

        if event.type() in (
            QtCore.QEvent.KeyRelease,
            QtCore.QEvent.MouseButtonRelease,
            QtCore.QEvent.Wheel,
        ):
            self._timer_update.start(self.fade_out_timer)

        return super().eventFilter(watched, event)

    def _on_timer_timeout(self):
        self.setText("")


class GraphicViewSceneDebugger(QtWidgets.QWidget):
    def __init__(self, view: QtWidgets.QGraphicsView, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._view = view

        # 1. Create
        self.timer_refresh = QtCore.QTimer()
        self.layout_main = QtWidgets.QVBoxLayout()
        self.layout_grid = QtWidgets.QGridLayout()
        self.label_keys = KeyMouseDisplayWidget()
        self.label_mouse_pos_global = QtWidgets.QLabel()
        self.label_mouse_pos_view = QtWidgets.QLabel()
        self.label_mouse_pos_scene = QtWidgets.QLabel()
        self.label_scene_rect = QtWidgets.QLabel()
        self.label_view_transform = QtWidgets.QLabel()
        self.label_scene_selection_area = QtWidgets.QLabel()

        label_mapping = [
            (self.label_keys, "Keys Active"),
            (self.label_mouse_pos_global, "Mouse Global"),
            (self.label_mouse_pos_view, "Mouse View"),
            (self.label_mouse_pos_scene, "Mouse Scene"),
            (self.label_scene_rect, "Scene Rect"),
            (self.label_view_transform, "View Transform"),
            (self.label_scene_selection_area, "Scene Selection"),
        ]

        # 2. Add
        self.setLayout(self.layout_main)
        self.layout_main.addLayout(self.layout_grid)
        for row_index, widgets in enumerate(label_mapping):
            widget, label = widgets
            label = QtWidgets.QLabel(label, self)
            label.setDisabled(True)
            self.layout_grid.addWidget(label, row_index, 0)
            self.layout_grid.addWidget(widget, row_index, 1)

        # 3. Modify
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_grid.setContentsMargins(0, 0, 0, 0)
        self.timer_refresh.start(50)

        # 4. Connections
        self.timer_refresh.timeout.connect(self.update_ui)

    def update_ui(self):
        cursor = QtGui.QCursor.pos()
        self.label_mouse_pos_global.setText(stringify_qobject(cursor))
        cursor = self._view.mapFromGlobal(cursor)
        self.label_mouse_pos_view.setText(stringify_qobject(cursor))
        cursor = self._view.mapToScene(cursor)
        self.label_mouse_pos_scene.setText(stringify_qobject(cursor))

        self.label_scene_rect.setText(stringify_qobject(self._view.sceneRect()))
        self.label_view_transform.setText(stringify_qobject(self._view.transform()))
        self.label_scene_selection_area.setText(
            stringify_qobject(self._view.scene().selectionArea())
        )


class ImageViewportDebugger(QtWidgets.QWidget):
    def __init__(self, liv: LqtImageViewport, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self._liv = liv

        # 1. Create
        self.timer_refresh = QtCore.QTimer()
        self.layout_main = QtWidgets.QVBoxLayout()
        self.layout_grid = QtWidgets.QGridLayout()

        self.label_image = QtWidgets.QLabel()
        self.label_plugins = QtWidgets.QLabel()
        self.label_bg_style = QtWidgets.QLabel()
        self.label_rotation = QtWidgets.QLabel()
        self.label_array = QtWidgets.QLabel()
        self.label_time_pre = QtWidgets.QLabel()
        self.label_time_post = QtWidgets.QLabel()

        label_mapping = [
            (self.label_image, "QImage"),
            (self.label_plugins, "Plugins"),
            (self.label_bg_style, "Background Style"),
            (self.label_rotation, "Rotation Angle"),
            (self.label_array, "Ndarray"),
            (self.label_time_pre, "Image preprocess time"),
            (self.label_time_post, "Image graphics process time"),
        ]

        # 2. Add
        self.setLayout(self.layout_main)
        self.layout_main.addLayout(self.layout_grid)
        for row_index, widgets in enumerate(label_mapping):
            widget, label = widgets
            label = QtWidgets.QLabel(label, self)
            label.setDisabled(True)
            self.layout_grid.addWidget(label, row_index, 0)
            self.layout_grid.addWidget(widget, row_index, 1)

        # 3. Modify
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_grid.setContentsMargins(0, 0, 0, 0)
        self.timer_refresh.start(50)

        # 4. Connections
        self.timer_refresh.timeout.connect(self.update_ui)

    def update_ui(self):
        self.label_image.setText(stringify_qobject(self._liv._image_item._image))
        self.label_plugins.setText(f"{len(self._liv._plugins)}")
        self.label_bg_style.setText(f"{repr(self._liv.graphic_view._background_style)}")
        self.label_rotation.setText(f"{self._liv._rotation_angle}")
        if self._liv._image_array is None:
            self.label_array.setText("None")
        else:
            self.label_array.setText(
                f"<{self._liv._image_array.dtype} {self._liv._image_array.shape}>"
            )
        self.label_time_pre.setText(f"{self._liv._last_image_loading_time[0]}s")
        self.label_time_post.setText(f"{self._liv._last_image_loading_time[1]}s")
