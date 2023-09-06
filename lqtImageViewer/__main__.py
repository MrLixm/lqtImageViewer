import logging
import sys
from pathlib import Path
from warnings import warn

from Qt import QtGui
from Qt import QtWidgets
from Qt import QtCore

try:
    import imageio.v3 as imageio
except ImportError:
    warn("imageio dependency not installed, some feature will be missing")

    class imageio:
        def __getattr__(self, item):
            raise RuntimeError("imageio dependency not installed")


from lqtImageViewer import LqtImageViewport
from lqtImageViewer._debugger import GraphicViewSceneDebugger


LOGGER = logging.getLogger(__name__)


class DockedDebugger(QtWidgets.QDockWidget):
    def __init__(self, image_viewer: LqtImageViewport):
        super().__init__("GraphicsView Debugger")
        self.debugger = GraphicViewSceneDebugger(image_viewer.graphic_view)
        self.debugger.layout_main.addStretch(-1)
        self.debugger.setFixedWidth(420)
        self.setWidget(self.debugger)


class InteractiveImageViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_viewer = LqtImageViewport()
        self.dock_debugger = DockedDebugger(self.image_viewer)

        LOGGER.debug("registering shortcut Ctrl+O")
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self, self.open_image_browser)

        self.setCentralWidget(self.image_viewer)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_debugger)

        self.setWindowTitle("LqtImageViewer")
        self.statusBar().showMessage("Use Ctrl+O to open an image.")

        self.image_viewer.picked_color_changed_signal.connect(
            self.on_color_picked_changed
        )

    def open_image_browser(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Image")
        if not file_path:
            return

        file_path = Path(file_path)

        LOGGER.info(f"reading {file_path} ...")
        try:
            array = imageio.imread(file_path)
        except Exception as error:
            raise IOError(
                f"Cannot read image {file_path}, it might not be a supported format: {error}"
            )

        LOGGER.info(f"loading image array <{array.dtype} {array.shape}> ...")
        self.image_viewer.set_image_from_array(array)

    @QtCore.Slot()
    def on_color_picked_changed(self):
        area = self.image_viewer.get_color_picked_area()
        if area:
            area = f"x:{area.x()} y:{area.y()} - {area.width()}x{area.height()}"
        self.statusBar().showMessage(str(area))


def main():
    app = QtWidgets.QApplication()

    LOGGER.info("Starting InteractiveImageViewer ...")

    window = InteractiveImageViewer()
    window.resize(1600, 850)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )

    main()
