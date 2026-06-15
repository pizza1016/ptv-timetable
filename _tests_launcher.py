if __name__ == "__main__":
    from functools import partial
    import unittest

    from _tests.common import XMLTestResult
    import _tests.ptv_timetable_parser

    unittest.main(module=_tests.ptv_timetable_parser, testRunner=unittest.TextTestRunner(resultclass=partial(XMLTestResult, outpath="test_report.xml")), verbosity=2, catchbreak=True, tb_locals=True)
