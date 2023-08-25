# lqtImageViewer

A simple image viewer for PyQt that take numpy array as input.

# usage

## developer

Most basic example :

```python
import numpy
import sys

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from lqtImageViewer import LqtImageViewer

app = QtWidgets.QApplication()

array = numpy.full((256,256,4), (3000, 63535, 5535, 65535), numpy.uint16)

viewer = LqtImageViewer()
viewer.set_image_from_array(array)
viewer.resize(1300, 800)
viewer.show()

sys.exit(app.exec_())
```

Note that the viewer expect R-G-B-A uint16 encoded array.


## user

### key binding

keyboard :

- `home` reset the zoom to 1:1
- `B` switch between background styles
- `F` reset the viewport position to origin

mouse:

- `MMB + drag`: pan the viewport
- `Alt + LMB + drag`: pan the viewport
- `Scroll Wheel`: zoom the viewport
- `Alt + MMB + drag`: zoom the viewport