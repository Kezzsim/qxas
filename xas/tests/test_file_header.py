import unittest
from types import SimpleNamespace

from xas.file_io import create_file_header, create_file_header_tiled


class TestFileHeader(unittest.TestCase):
    def make_run(self, value):
        start = dict.fromkeys(
            ('Facility', 'beamline_id', 'PI', 'PROPOSAL', 'SAF', 'comment',
             'year', 'cycle', 'scan_id', 'uid'),
            'test',
        )
        start['time'] = 1000
        for key, length in {
            'foil_element': 1,
            'keithley_gainsB': 4,
            'keithley_gainsC': 3,
            'ionchamber_ratesB': 5,
            'ionchamber_ratesC': 5,
            'incident_beampathB': 1,
            'incident_beampathC': 1,
            'incident_slits': 4,
            'incident_slits_c': 4,
            'sample_stageB': 4,
            'cm_horizontal': 2,
            'linkam_temperature': 2,
            'hutchC_table': 5,
            'drifts_stageC': 2,
        }.items():
            start[key] = [value] * length
        return SimpleNamespace(start=start, stop={'time': 1060})

    def headers(self, run):
        class Header(dict):
            start = run.start

        yield create_file_header({'test': Header(start=run.start, stop=run.stop)}, 'test')
        yield create_file_header_tiled(run)

    def test_none_metadata_renders_as_unavailable(self):
        for header in self.headers(self.make_run(None)):
            self.assertIn('I0: N/A sccm He + N/A sccm N2', header)
            self.assertIn('Horizontal: N/A mm Vertical: N/A mm', header)
            self.assertIn('Temperature : N/A C and Ramp Rate: N/A C/min.', header)
            self.assertIn('Up: N/A mm Down: N/A mm', header)
            self.assertNotIn('None', header)

    def test_numeric_precision_and_zero_are_preserved(self):
        for value, expected in [(1.234, '1.23'), (0, '0.00')]:
            for header in self.headers(self.make_run(value)):
                self.assertIn(f'I0: {expected} sccm He', header)
                self.assertIn(f'Up: {expected} mm Down: {expected} mm', header)
                self.assertNotIn('N/A', header)


if __name__ == '__main__':
    unittest.main()
