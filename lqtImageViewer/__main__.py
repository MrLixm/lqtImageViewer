import logging
import sys
from pathlib import Path
from typing import Literal
from warnings import warn

import numpy
import numpy.typing
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

try:
    import imageio.v3 as imageio
except ImportError:
    warn("imageio dependency not installed, some feature will be missing")

    class imageio:
        def __getattr__(self, item):
            raise RuntimeError("imageio dependency not installed")


from lqtImageViewer import LqtImageViewer


LOGGER = logging.getLogger(__name__)


def convert_bit_depth(
    array: numpy.ndarray,
    bit_depth: numpy.typing.DTypeLike = numpy.core.float32,
) -> numpy.ndarray:
    """
    Convert given array to given bit-depth, the current bit-depth of the array
    is used to determine the appropriate conversion path.

    References:
        - [1] https://github.com/colour-science/colour/blob/develop/colour/io/image.py
    """
    uint8 = numpy.core.uint8
    uint16 = numpy.core.uint16
    float16 = numpy.core.float16
    float32 = numpy.core.float32
    float64 = numpy.core.float64

    source_dtype = array.dtype
    target_dtype = numpy.dtype(bit_depth)

    if source_dtype == uint8:
        if bit_depth == uint16:
            array = (array * 257).astype(target_dtype)
        elif bit_depth in (float16, float32, float64):
            array = (array / 255).astype(target_dtype)
    elif source_dtype == uint16:
        if bit_depth == uint8:
            array = (array / 257).astype(target_dtype)
        elif bit_depth in (float16, float32, float64):
            array = (array / 65535).astype(target_dtype)
    elif source_dtype in (float16, float32, float64):
        if bit_depth == uint8:
            array = numpy.around(array * 255).astype(target_dtype)
        elif bit_depth == uint16:
            array = numpy.around(array * 65535).astype(target_dtype)
        elif bit_depth in (float16, float32, float64):
            array = array.astype(target_dtype)
    else:
        raise TypeError(f"unsported source dtype {source_dtype}")

    return array


class InteractiveImageViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_viewer = LqtImageViewer()
        self.setCentralWidget(self.image_viewer)
        self.setWindowTitle("LqtImageViewer")

        LOGGER.debug("registering shortcut Ctrl+O")
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self, self.open_image_browser)

        self.statusBar().showMessage("Use Ctrl+O to open an image.")

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

        LOGGER.info(f"pre-processing array <{array.dtype} {array.shape}> ...")
        array = convert_bit_depth(array, numpy.core.uint16)

        # remove alpha if existing
        if array.shape[2] > 3:
            array = array[:, :, :3]

        # we need an alpha channel at max value
        alpha = numpy.full(
            (array.shape[0], array.shape[1], 1),
            numpy.iinfo(numpy.core.uint16).max,
            dtype=numpy.core.uint16,
        )
        array = numpy.concatenate((array, alpha), axis=-1)

        LOGGER.info(f"loading image array <{array.dtype} {array.shape}> ...")
        self.image_viewer.set_image_from_array(array)


def main():
    app = QtWidgets.QApplication()

    LOGGER.info("Starting InteractiveImageViewer ...")

    window = InteractiveImageViewer()
    window.resize(1300, 800)
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
