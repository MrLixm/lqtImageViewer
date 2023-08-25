from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets


def generate_points_grid(
    surface: QtCore.QRectF,
    size: float,
) -> list[QtCore.QPointF]:
    """
    Generate a grid of the given size on the given surface, made of points.

    Args:
        surface: surface that must be covered in points
        size: size of the grid in pixels
    """
    block_width = surface.width() / size + 0.5
    block_height = surface.height() / size + 0.5

    left = surface.left() - (surface.left() % size)
    top = surface.top() - (surface.top() % size)

    h_coordinates = [left + size * index for index in range(int(block_width) + 2)]
    v_coordinates = [top + size * index for index in range(int(block_height) + 2)]
    grid_coordinates = [
        QtCore.QPointF(h_coordinate, v_coordinate)
        for h_coordinate in h_coordinates
        for v_coordinate in v_coordinates
    ]
    return grid_coordinates


def generate_coordinates_grid(
    painter: QtGui.QPainter,
    surface: QtCore.QRectF,
    separation: int,
    font_size: int = 5,
):
    """
    Use the given QPainter to draw a grid of coordinates corresponding to the given surface.

    Args:
        painter:
        surface: surface used to paint and to extract coordinates from
        separation: size of the grid in number of seperation
        font_size: size of the coordinates text font
    """
    block_width = surface.width() / separation
    block_height = surface.height() / separation

    h_coordinates = [
        surface.left() + block_width * index for index in range(separation + 1)
    ]
    v_coordinates = [
        surface.top() + block_height * index for index in range(separation + 1)
    ]
    grid_coordinates = [
        [h_coordinate, v_coordinate]
        for h_coordinate in h_coordinates
        for v_coordinate in v_coordinates
    ]

    text_height = painter.fontMetrics().boundingRectChar("5").height()
    text_height = min(text_height + 10, block_height)
    text_rect = QtCore.QRectF(0, 0, block_width, text_height)

    for x, y in grid_coordinates:
        alignment = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop
        if x == surface.left():
            alignment = alignment ^ QtCore.Qt.AlignHCenter | QtCore.Qt.AlignRight
        elif x >= surface.width() + surface.left():
            alignment = alignment ^ QtCore.Qt.AlignHCenter | QtCore.Qt.AlignLeft
        if y == surface.top():
            alignment = alignment ^ QtCore.Qt.AlignTop | QtCore.Qt.AlignBottom
        # useless but there by default
        elif y >= surface.height() + surface.top():
            alignment = alignment ^ QtCore.Qt.AlignTop | QtCore.Qt.AlignTop

        point = QtCore.QPointF(x, y)
        text_rect.moveCenter(point)
        painter.save()
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 150), 3))
        painter.drawPoint(point)
        painter.setFont(QtGui.QFont("Courier New", font_size, 500))
        painter.drawText(text_rect, alignment, f"{x:0.2f}, {y:0.2f}")
        painter.restore()
