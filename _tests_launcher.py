if __name__ == "__main__":
    from _tests.common import XMLTestResult
    import _tests.ptv_timetable_parser
    import unittest

    unittest.main(module=_tests.ptv_timetable_parser, testRunner=unittest.TextTestRunner(resultclass=XMLTestResult), verbosity=2, catchbreak=True, tb_locals=True)
