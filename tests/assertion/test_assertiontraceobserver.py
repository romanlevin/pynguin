#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2021 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
from typing import Optional
from unittest import mock
from unittest.mock import MagicMock

import pynguin.assertion.assertiontraceobserver as ato
from pynguin.testcase.execution.executioncontext import ExecutionContext
from pynguin.testcase.statements import statement as stmt


class FooObserver(ato.AssertionTraceObserver):
    def before_statement_execution(
        self, statement: stmt.Statement, exec_ctx: ExecutionContext
    ):
        pass  # pragma: no cover

    def after_statement_execution(
        self,
        statement: stmt.Statement,
        exec_ctx: ExecutionContext,
        exception: Optional[Exception] = None,
    ) -> None:
        pass  # pragma: no cover


def test_clear():
    observer = FooObserver()
    with mock.patch.object(observer, "_trace") as trace_mock:
        observer.clear()
        trace_mock.clear.assert_called_once()


def test_clone():
    observer = FooObserver()
    with mock.patch.object(observer, "_trace") as trace_mock:
        clone = object()
        trace_mock.clone.return_value = clone
        cloned = observer.get_trace()
        trace_mock.clone.assert_called_once()
        assert cloned == clone


def test_before_test_case_execution():
    observer = FooObserver()
    with mock.patch.object(observer, "clear") as clear_mock:
        observer.before_test_case_execution(MagicMock())
        clear_mock.assert_called_once()


def test_after_test_case_execution():
    observer = FooObserver()
    result = MagicMock()
    with mock.patch.object(observer, "_trace") as trace_mock:
        clone = object()
        trace_mock.clone.return_value = clone
        observer.after_test_case_execution(MagicMock(), result)
        result.add_output_trace.assert_called_with(type(observer), clone)
