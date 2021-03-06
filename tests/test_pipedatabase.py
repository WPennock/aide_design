import unittest
from aide_design.units import unit_registry as u
from aide_design import pipedatabase as pipe

class PipeTest(unittest.TestCase):
    def test_OD(self):
        checks = [[1.0 * u.inch, 1.315 * u.inch]]
        for i in checks:
            with self.subTest(i=i):
                self.assertEqual(pipe.OD(i[0]), i[1])

if __name__ == '__main__':
    unittest.main()
