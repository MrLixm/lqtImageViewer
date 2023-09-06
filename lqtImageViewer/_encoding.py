import logging

import numpy
import numpy.typing
from numpy.core import uint8
from numpy.core import uint16
from numpy.core import float16
from numpy.core import float32
from numpy.core import float64


logger = logging.getLogger(__name__)


def convert_bit_depth(
    array: numpy.ndarray,
    bit_depth: numpy.typing.DTypeLike = float32,
) -> numpy.ndarray:
    """
    Convert given array to given bit-depth, the current bit-depth of the array
    is used to determine the appropriate conversion path.

    References:
        - [1] https://github.com/colour-science/colour/blob/develop/colour/io/image.py
    """
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
            array = numpy.clip(array, 0, 1)
            array = numpy.around(array * 255).astype(target_dtype)
        elif bit_depth == uint16:
            array = numpy.clip(array, 0, 1)
            array = numpy.around(array * 65535).astype(target_dtype)
        elif bit_depth in (float16, float32, float64):
            array = array.astype(target_dtype)
    else:
        raise TypeError(f"unsported source dtype {source_dtype}")

    return array


def ensure_rgba_array(array: numpy.ndarray) -> numpy.ndarray:
    """
    Ensure the given array has an alpha channel, if not create one with maximum value.

    Args:
        array: any arbitrary image array

    Returns:
        new RGBA array instance
    """
    # single channel with no third axis
    if len(array.shape) == 2:
        array = numpy.repeat(array[..., numpy.newaxis], 3, axis=-1)

    # remove images with more than 4 channels
    # TODO should we actually only keep 3 channel as the 4th is probably not an alpha ?
    elif array.shape[2] > 4:
        array = array[:, :, :4]

    # single channel
    elif array.shape[2] == 1:
        array = numpy.repeat(array, 3, axis=-1)

    # ensure an alpha channel at max value if not found
    if array.shape[2] == 3:
        alpha = numpy.full(
            (array.shape[0], array.shape[1], 1),
            numpy.iinfo(numpy.core.uint16).max,
            dtype=numpy.core.uint16,
        )
        array = numpy.concatenate((array, alpha), axis=-1)

    # TODO make a copy
    return array
