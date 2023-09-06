# lqtImageViewer

A simple but flexible image viewer for PyQt that take numpy array as input.

# usage

## developer

Most basic example :

```python
import numpy
import sys

from Qt import QtWidgets

from lqtImageViewer import LqtImageViewport

app = QtWidgets.QApplication()

array = numpy.full((256,256,4), (3000, 63535, 5535, 65535), numpy.uint16)

viewer = LqtImageViewport()
viewer.set_image_from_array(array)
viewer.resize(1300, 800)
viewer.show()

sys.exit(app.exec_())
```

Note that the viewer expect R-G-B-A uint16 encoded array.
But you can still give it other encodings (channels, bitdepth) and it will handle the conversion.

### color-picking

LIV include a color-picker plugin that allow you to select a area of pixel on the image.

Note the color picker doesn't actually perform any "color" picking. It only
allow to pick an area on the image. It is up to the developer to convert that
area into a color or anything else.

```python
# this is demo code, not directly executable
import numpy
from lqtImageViewer import LqtImageViewport

array = numpy.full((256,256,4), (0.23, 0.69, 0.1, 65535), numpy.float32)

viewer = LqtImageViewport()
viewer.set_image_from_array(array)
# retrieve a QRect
picked_area = viewer.get_color_picked_area()
# exactly the same as above
picked_area = viewer.color_picker.get_picked_area()


# there is a signal for when the picked area change
# note the signal doesn't pass any value

def print_picked():
    area = viewer.get_color_picked_area()
    sliced = array[
        area.y() : area.y() + area.height(),
        area.x() : area.x() + area.width(),
        ...,
    ]
    average = numpy.mean(sliced, axis=(0, 1))
    print(numpy.array2string(average, precision=3, separator=","))
    

viewer.picked_color_changed_signal.connect(print_picked)
```



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
- `Alt + Shift` : display a pixel coordinates grid as long as the keys are hold
- `Alt + Shift + Wheel` change the density of the coordinates grid
- `Ctrl + LMB` : show the color-picker at the current cursor position
- `Ctrl + Shift + LMB + drag`: create a color-picked area
- `Ctrl + RMB`: hide/disable the color-picker