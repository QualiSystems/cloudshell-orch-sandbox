import unittest
from mock import patch, Mock


class MyTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something2(self):
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
