from collections import namedtuple
import operator
from numbers import Number
from typing import Union, Iterable, Callable, Any

import numpy as np

X = Union[Iterable, np.ndarray, Number, bool]
Key = Union[int, slice, np.ndarray]


def getitem(array_group, key: np.ndarray):
    if isinstance(array_group, np.ndarray):
        return array_group[key]
    return [getitem(a, key) for a in array_group]


def setitem(array_group: Union[list, np.ndarray],
            key: Key, x: X):
    if isinstance(array_group, np.ndarray):
        array_group[key] = x
    else:
        assert isinstance(x, Iterable)
        for _group, _x in zip(array_group, x):
            setitem(_group, key, _x)


def allocate(pre_shape: tuple, shapes: Union[tuple, Iterable]):
    try:
        return np.zeros(pre_shape + shapes)
    except TypeError:
        return [allocate(pre_shape, shape) for shape in shapes]


def get_shapes(x, subset=None):
    if isinstance(x, np.ndarray):
        shape = np.shape(x)  # type: tuple
        if subset is None:
            return shape
        return shape[subset]
    if np.isscalar(x):
        return tuple()
    return [get_shapes(_x, subset) for _x in x]


def xnor(check: Callable, *vals: X):
    return all(map(check, vals)) or not any(map(check, vals))


def zip_op(op: Callable[[X, X], list], x: X, y: X):
    assert xnor(np.isscalar, [x, y])
    assert xnor(lambda z: isinstance(z, np.ndarray), [x, y])
    if isinstance(x, np.ndarray) or np.isscalar(x):
        return op(x, y)
    assert len(x) == len(y)
    return [op(_x, _y) for _x, _y in zip(x, y)]


class ArrayGroup:
    @staticmethod
    def shape_like(x: X, pre_shape: tuple):
        return ArrayGroup(allocate(pre_shape=pre_shape,
                                   shapes=(get_shapes(x))))

    def __init__(self, values):
        self.arrays = values

    def __iter__(self):
        return iter(self.arrays)

    def __getitem__(self, key: Key):
        return ArrayGroup(getitem(self.arrays, key=key))

    def __setitem__(self, key: Key, value):
        setitem(self.arrays, key=key, x=value)

    def zip_op(self, op, other):
        assert callable(op)
        assert isinstance(other, ArrayGroup)
        return ArrayGroup(zip_op(op, self.arrays, other.arrays))

    def __or__(self, other):
        return self.zip_op(operator.or_, other)

    def __eq__(self, other):
        return self.zip_op(operator.eq, other)

    @property
    def shape(self):
        return get_shapes(self.arrays)