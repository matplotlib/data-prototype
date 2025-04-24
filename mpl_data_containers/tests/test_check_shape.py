import pytest

from mpl_data_containers.description import Desc


@pytest.mark.parametrize(
    "spec,actual",
    [
        ([()], [()]),
        ([(3,)], [(3,)]),
        ([("N",)], [(3,)]),
        ([("N",)], [("X",)]),
        ([("N+1",)], [(3,)]),
        ([("N", "N+1")], [(3, 4)]),
        ([("N", "N-1")], [(3, 2)]),
        ([("N", "N+10")], [(3, 13)]),
        ([("N", "N+1")], [("X", "X+1")]),
        ([("N", "N+9")], [("X", "X+9")]),
        ([("N",), ("N",)], [("X",), ("X",)]),
        ([("N",), ("N",)], [(3,), (3,)]),
        ([("N",), ("N+1",)], [(3,), (4,)]),
        ([("N", "M")], [(3, 4)]),
        ([("N", "M")], [("X", "Y")]),
        ([("N", "M")], [("X", "X")]),
        ([("N", "M", 3)], [(3, 4, 3)]),
        ([("N",), ("M",), ("N", "M")], [(3,), (4,), (3, 4)]),
        ([("N",), ("M",), ("N", "M")], [("X",), ("Y",), ("X", "Y")]),
    ],
)
def test_passing_no_broadcast(
    spec: list[tuple[int | str, ...]], actual: list[tuple[int | str, ...]]
):
    spec = {var: shape for var, shape in zip("abcdefg", spec)}
    actual = {var: shape for var, shape in zip("abcdefg", actual)}
    Desc.validate_shapes(spec, actual)


@pytest.mark.parametrize(
    "spec,actual",
    [
        ([(2,)], [()]),
        ([(3,)], [(4,)]),
        ([(3,)], [(1,)]),
        ([("N",)], [(3, 4)]),
        ([("N", "N+1")], [(4, 4)]),
        ([("N", "N-1")], [(4, 4)]),
        ([("N", "N+1")], [("X", "Y")]),
        ([("N", "N+1")], [("X", 3)]),
        ([("N",), ("N",)], [(3,), (4,)]),
        ([("N", "N")], [("X", "Y")]),
        ([("N", "M", 3)], [(3, 4, 4)]),
        ([("N",), ("M",), ("N", "M")], [(3,), (4,), (3, 5)]),
    ],
)
def test_failing_no_broadcast(
    spec: list[tuple[int | str, ...]], actual: list[tuple[int | str, ...]]
):
    spec = {var: shape for var, shape in zip("abcdefg", spec)}
    actual = {var: shape for var, shape in zip("abcdefg", actual)}
    with pytest.raises(ValueError):
        Desc.validate_shapes(spec, actual)


@pytest.mark.parametrize(
    "spec,actual",
    [
        ([()], [()]),
        ([(2,)], [()]),
        ([(3,)], [(3,)]),
        ([(3,)], [(1,)]),
        ([("N",)], [(3,)]),
        ([("N",)], [("X",)]),
        ([("N", 4)], [(3, 1)]),
        ([("N+1",)], [(3,)]),
        ([("N", "N+1")], [(3, 4)]),
        ([("N", "N+1")], [("X", "X+1")]),
        ([("N", "N+1")], [("X", 1)]),
        ([("N",), ("N",)], [("X",), ("X",)]),
        ([("N",), ("N+1",)], [("X",), (1,)]),
        ([("N",), ("N+1",)], [(3,), (4,)]),
        ([("N",), ("N+1",)], [(1,), (4,)]),
        ([("N", "M")], [(3, 4)]),
        ([("N", "M")], [("X", "Y")]),
        ([("N", "M")], [("X", "X")]),
        ([("N", "M", 3)], [(3, 4, 3)]),
        ([("N",), ("M",), ("N", "M")], [(3,), (4,), (3, 4)]),
        ([("N",), ("M",), ("N", "M")], [(3,), (4,), (3, 1)]),
        ([("N",), ("M",), ("N", "M")], [("X",), ("Y",), ("X", "Y")]),
    ],
)
def test_passing_broadcast(
    spec: list[tuple[int | str, ...]], actual: list[tuple[int | str, ...]]
):
    spec = {var: shape for var, shape in zip("abcdefg", spec)}
    actual = {var: shape for var, shape in zip("abcdefg", actual)}
    Desc.validate_shapes(spec, actual, broadcast=True)


@pytest.mark.parametrize(
    "spec,actual",
    [
        ([(1,)], [(3,)]),
        ([(3,)], [(4,)]),
        ([("N",)], [(3, 4)]),
        ([("N", "N+1")], [(4, 4)]),
        ([("N", "N+1")], [("X", "Y")]),
        ([("N", "N+1")], [("X", 3)]),
        ([("N",), ("N",)], [(3,), (4,)]),
        ([("N", "N")], [("X", "Y")]),
        ([("N", "M", 3)], [(3, 4, 4)]),
        ([("N",), ("M",), ("N", "M")], [(3,), (4,), (3, 5)]),
    ],
)
def test_failing_broadcast(
    spec: list[tuple[int | str, ...]], actual: list[tuple[int | str, ...]]
):
    spec = {var: shape for var, shape in zip("abcdefg", spec)}
    actual = {var: shape for var, shape in zip("abcdefg", actual)}
    with pytest.raises(ValueError):
        Desc.validate_shapes(spec, actual, broadcast=True)


def test_desc_object():
    spec = {"a": Desc(("N",), float), "b": Desc(("N+1",), float)}
    actual = {"a": Desc((3,), float), "b": Desc((4,), float)}
    Desc.validate_shapes(spec, actual)


def test_missing_key():
    spec = {"a": Desc(("N",), float), "b": Desc(("N+1",), float)}
    actual = {"a": Desc((3,), float)}
    with pytest.raises(KeyError):
        Desc.validate_shapes(spec, actual)
