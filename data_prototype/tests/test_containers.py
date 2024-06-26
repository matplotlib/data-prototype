import numpy as np

from matplotlib.transforms import IdentityTransform

import pytest


from .. import containers


@pytest.fixture
def ac():
    return containers.ArrayContainer(
        a=np.arange(5), b=np.arange(42, dtype=float).reshape(6, 7)
    )


def _verify_describe(container):
    data, cache_key = container.query(IdentityTransform(), [100, 100])
    desc = container.describe()

    assert set(data) == set(desc)
    for k, v in data.items():
        assert v.shape == desc[k].shape


def test_array_describe(ac):
    _verify_describe(ac)


def test_array_ignore_query(ac):
    data, cache_key = ac.query(IdentityTransform(), [100, 100])
    data2, cache_key_2 = ac.query(IdentityTransform(), [10, 10])
    assert cache_key == cache_key_2

    for k in set(data) | set(data2):
        assert np.all(data[k] == data2[k])


def test_array_cache_stable(ac):
    data, cache_key = ac.query(IdentityTransform(), [100, 100])
    data2, cache_key_2 = ac.query(IdentityTransform(), [100, 100])
    assert cache_key == cache_key_2

    for k in set(data) | set(data2):
        assert np.all(data[k] == data2[k])


def test_array_cache_update(ac):
    data, cache_key = ac.query(IdentityTransform(), [100, 100])
    ac.update(**{k: v * 2 for k, v in data.items()})
    data2, cache_key_2 = ac.query(IdentityTransform(), [100, 100])

    assert cache_key != cache_key_2
    for k in set(data) | set(data2):
        assert np.all(2 * data[k] == data2[k])


def test_array_no_new_keys(ac):
    with pytest.raises(containers.NoNewKeys):
        ac.update(d=[1, 2])


@pytest.fixture
def rc():
    return containers.RandomContainer(a=(5,), b=(6, 7))


def test_random_describe(rc):
    _verify_describe(rc)


def test_random_ustable_cache(rc):
    _, cache_key = rc.query(IdentityTransform(), [100, 100])
    _, cache_key2 = rc.query(IdentityTransform(), [100, 100])
    assert cache_key != cache_key2
