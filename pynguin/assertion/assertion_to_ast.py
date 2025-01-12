#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2021 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
"""Provides an assertion visitor to transform assertions to AST."""
import ast
from typing import Any, List, Set

import pynguin.assertion.assertionvisitor as av
import pynguin.assertion.noneassertion as na
import pynguin.assertion.primitiveassertion as pa
import pynguin.configuration as config
import pynguin.testcase.variable.variablereference as vr
import pynguin.utils.ast_util as au
from pynguin.utils.namingscope import NamingScope


class AssertionToAstVisitor(av.AssertionVisitor):
    """An assertion visitor that transforms assertions into AST nodes."""

    def __init__(self, common_modules: Set[str], variable_names: NamingScope):
        """Create a new assertion visitor.

        Args:
            variable_names: the naming scope that is used to resolve the names
                            of the variables used in the assertions.
            common_modules: the set of common modules that are used. Modules may be
                            added when transforming the assertions.
        """
        self._common_modules = common_modules
        self._variable_names = variable_names
        self._nodes: List[ast.stmt] = []

    @property
    def nodes(self) -> List[ast.stmt]:
        """Provides the ast nodes generated by this visitor.

        Returns:
            the ast nodes generated by this visitor.
        """
        return self._nodes

    def visit_primitive_assertion(self, assertion: pa.PrimitiveAssertion) -> None:
        """
        Creates an assertion of form "assert var0 == value" or assert var0 is False,
        if the value is a bool.

        Args:
            assertion: the assertion that is visited.

        """
        if isinstance(assertion.value, bool):
            self._nodes.append(
                self._create_constant_assert(
                    assertion.source, ast.Is(), assertion.value
                )
            )
        elif isinstance(assertion.value, float):
            self._nodes.append(
                self._create_float_delta_assert(assertion.source, assertion.value)
            )
        else:
            self._nodes.append(
                self._create_constant_assert(
                    assertion.source, ast.Eq(), assertion.value
                )
            )

    def visit_none_assertion(self, assertion: na.NoneAssertion) -> None:
        """
        Creates an assertion of form "assert var0 is None" or "assert var0 is not None".

        Args:
            assertion: the assertion that is visited.
        """
        self._nodes.append(
            self._create_constant_assert(
                assertion.source, ast.Is() if assertion.value else ast.IsNot(), None
            )
        )

    def _create_constant_assert(
        self, var: vr.VariableReference, operator: ast.cmpop, value: Any
    ) -> ast.Assert:
        return ast.Assert(
            test=ast.Compare(
                left=au.create_var_name(self._variable_names, var, load=True),
                ops=[operator],
                comparators=[ast.Constant(value=value, kind=None)],
            ),
            msg=None,
        )

    def _create_float_delta_assert(
        self, var: vr.VariableReference, value: Any
    ) -> ast.Assert:
        self._common_modules.add("pytest")
        float_precision = config.configuration.test_case_output.float_precision

        return ast.Assert(
            test=ast.Compare(
                left=au.create_var_name(self._variable_names, var, load=True),
                ops=[ast.Eq()],
                comparators=[
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="pytest", ctx=ast.Load()),
                            attr="approx",
                            ctx=ast.Load(),
                        ),
                        args=[
                            ast.Constant(value=value, kind=None),
                        ],
                        keywords=[
                            ast.keyword(
                                arg="abs",
                                value=ast.Constant(
                                    value=float_precision,
                                    kind=None,
                                ),
                            ),
                            ast.keyword(
                                arg="rel",
                                value=ast.Constant(
                                    value=float_precision,
                                    kind=None,
                                ),
                            ),
                        ],
                    ),
                ],
            ),
            msg=None,
        )
