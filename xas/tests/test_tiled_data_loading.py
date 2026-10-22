import unittest
from types import SimpleNamespace

import numpy as np

from xas.db_io import load_apb_dataset_from_tiled, load_apb_trig_dataset_from_tiled


class Array:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data


class Stream(dict):
    def read(self):
        raise ValueError(
            'Cannot specify dim0 when the arrays have different left-most dimensions.'
        )


def make_run(start, **arrays):
    return SimpleNamespace(
        start=start,
        v2={name: Stream(data={name: Array(data)}) for name, data in arrays.items()},
    )


class TestTiledDataLoading(unittest.TestCase):
    def test_apb_and_encoder_arrays_are_read_independently(self):
        apb = np.array(
            [(1, 2000), (2, 3000)], dtype=[('timestamp', 'f8'), ('i0', 'f8')]
        )
        encoder = np.array(
            [(1, 0, -10), (2, 0, -20), (3, 0, -30)],
            dtype=[('ts_s', 'f8'), ('ts_ns', 'f8'), ('encoder', 'i4')],
        )
        for hutch, stream_name in [('b', 'apb_stream'), ('c', 'apb_stream_c')]:
            with self.subTest(hutch=hutch):
                run = make_run(
                    {'hutch': hutch, 'angle_offset': 1.5, 'ch1_offset': 1},
                    **{stream_name: apb, 'pb1_enc1': encoder},
                )
                data, energy, offset = load_apb_dataset_from_tiled(run)
                np.testing.assert_allclose(data['timestamp'], [1, 2])
                np.testing.assert_allclose(data['i0'], [0.001, 0.002])
                np.testing.assert_array_equal(energy['encoder'], [-10, -20, -30])
                self.assertEqual(offset, -1.5)

    def test_trigger_array_is_read_without_stream_alignment(self):
        triggers = np.array(
            [(1, 1), (2, 0), (3, 1), (4, 0)],
            dtype=[('timestamp', 'f8'), ('transition', 'i4')],
        )
        run = make_run({}, apb_trigger=triggers)
        np.testing.assert_allclose(
            load_apb_trig_dataset_from_tiled(run), [1.5, 3.5]
        )


if __name__ == '__main__':
    unittest.main()
