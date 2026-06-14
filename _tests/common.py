from traceback import format_exception
from types import TracebackType
from typing import Any, Final, Literal, override, Self
from unittest import TextTestResult
from xml.etree.ElementTree import Element, ElementTree

import types
import unittest


_TEST_SUITE_TAG: Final = "testsuite"
_TEST_CASE_TAG: Final = "testcase"
_FAILURE_TAG: Final = "failure"
_ERROR_TAG: Final = "error"
_SKIPPED_TAG: Final = "skipped"
_SYSTEM_OUT_TAG: Final = "system-out"
_SYSTEM_ERR_TAG: Final = "system-err"

REPORT_PATH: Final = "test_report.xml"


class XMLTestResult(TextTestResult):

    def __init__(self: Self, stream: unittest.runner._StreamT, descriptions: bool, verbosity: int, *, durations: int | None = None, **kwargs: Any) -> None:
        super().__init__(stream=stream, descriptions=descriptions, verbosity=verbosity, durations=durations, **kwargs)
        self.tree: Final[ElementTree[Element[str]]] = ElementTree(Element(_TEST_SUITE_TAG))
        self.last_elapsed: float | None = None
        return

    def _add_failure_entry(self: Self, test: unittest.TestCase, err: tuple[type[BaseException], BaseException, TracebackType] | tuple[None, None, None], tag: Literal["failure", "error"]) -> None:
        _id = test.id().rpartition(".")
        method = _id[-1]
        _id = _id[0].rpartition(".")
        case = Element(_TEST_CASE_TAG, {"classname": _id[-1], "name": method, "file": str.join("/", _id[0].split(".")) + ".py"})
        self.tree.getroot().append(case)
        if self.last_elapsed is not None:
            case.set("time", str(self.last_elapsed))
            self.last_elapsed = None
        failure = Element(tag)
        case.append(failure)
        failure.text = str.join("", format_exception(err[1]))
        return

    @override
    def addSuccess(self: Self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        _id = test.id().rpartition(".")
        method = _id[-1]
        _id = _id[0].rpartition(".")
        self.tree.getroot().append(Element(_TEST_CASE_TAG, {"classname": _id[-1], "name": method, "file": str.join("/", _id[0].split(".")) + ".py"}))
        if self.last_elapsed is not None:
            self.tree.getroot()[-1].set("time", str(self.last_elapsed))
            self.last_elapsed = None
        return

    @override
    def addFailure(self: Self, test: unittest.TestCase, err: tuple[type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None]) -> None:
        super().addFailure(test, err)
        self._add_failure_entry(test, err, _FAILURE_TAG)
        return

    @override
    def addError(self: Self, test: unittest.TestCase, err: tuple[type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None]) -> None:
        super().addError(test, err)
        self._add_failure_entry(test, err, _ERROR_TAG)
        return

    @override
    def addSkip(self: Self, test: unittest.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        _id = test.id().rpartition(".")
        method = _id[-1]
        _id = _id[0].rpartition(".")
        case = Element(_TEST_CASE_TAG, {"classname": _id[-1], "name": method, "file": str.join("/", _id[0].split(".")) + ".py"})
        self.tree.getroot().append(case)
        if self.last_elapsed is not None:
            case.set("time", str(self.last_elapsed))
            self.last_elapsed = None
        skipped = Element(_SKIPPED_TAG)
        case.append(skipped)
        skipped.text = reason
        return

    @override
    def addExpectedFailure(self: Self, test: unittest.TestCase, err: tuple[type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None]) -> None:
        super().addExpectedFailure(test, err)
        _id = test.id().rpartition(".")
        method = _id[-1]
        _id = _id[0].rpartition(".")
        self.tree.getroot().append(Element(_TEST_CASE_TAG, {"classname": _id[-1], "name": method, "file": str.join("/", _id[0].split(".")) + ".py"}))
        if self.last_elapsed is not None:
            self.tree.getroot()[-1].set("time", str(self.last_elapsed))
            self.last_elapsed = None
        return

    @override
    def addUnexpectedSuccess(self: Self, test: unittest.TestCase) -> None:
        super().addUnexpectedSuccess(test)
        _id = test.id().rpartition(".")
        method = _id[-1]
        _id = _id[0].rpartition(".")
        case = Element(_TEST_CASE_TAG, {"classname": _id[-1], "name": method, "file": str.join("/", _id[0].split(".")) + ".py"})
        self.tree.getroot().append(case)
        if self.last_elapsed is not None:
            case.set("time", str(self.last_elapsed))
            self.last_elapsed = None
        failure = Element(_FAILURE_TAG)
        case.append(failure)
        failure.text = "Test succeeded when it was not expected to"
        return

    @override
    def addSubTest(self: Self, test: unittest.TestCase, subtest: unittest.TestCase, outcome: tuple[type[BaseException], BaseException, types.TracebackType] | tuple[None, None, None] | None) -> None:
        super().addSubTest(test, subtest, outcome)
        if outcome is not None:
            if issubclass(outcome[0], test.failureException):
                self._add_failure_entry(subtest, outcome, _FAILURE_TAG)
            else:
                self._add_failure_entry(subtest, outcome, _ERROR_TAG)
        else:
            _id = subtest.id().rpartition(".")
            method = _id[-1]
            _id = _id[0].rpartition(".")
            self.tree.getroot().append(Element(_TEST_CASE_TAG, {"classname": _id[-1], "name": method, "file": str.join("/", _id[0].split(".")) + ".py"}))
            if self.last_elapsed is not None:
                self.tree.getroot()[-1].set("time", str(self.last_elapsed))
                self.last_elapsed = None
        return

    @override
    def addDuration(self: Self, test: unittest.TestCase, elapsed: float) -> None:
        super().addDuration(test, elapsed)
        self.last_elapsed = elapsed
        return

    @override
    def stopTestRun(self: Self) -> None:
        super().stopTestRun()
        with open(REPORT_PATH, mode="w", encoding="utf-8") as f:
            self.tree.write(f, encoding="unicode", xml_declaration=True, method="xml")
        return

