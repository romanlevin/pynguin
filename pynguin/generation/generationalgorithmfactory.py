#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2020 Pynguin Contributors
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
"""Provides factories for the generation algorithm."""
import logging
from abc import ABCMeta, abstractmethod
from typing import Callable, Dict, Generic, TypeVar

import pynguin.configuration as config
import pynguin.ga.chromosome as chrom
import pynguin.ga.chromosomefactory as cf
import pynguin.ga.testcasechromosomefactory as tccf
import pynguin.ga.testcasefactory as tcf
import pynguin.ga.testsuitechromosome as tsc
import pynguin.ga.testsuitechromosomefactory as tscf
import pynguin.testcase.testfactory as tf
from pynguin.ga.operators.crossover.crossover import CrossOverFunction
from pynguin.ga.operators.crossover.singlepointrelativecrossover import (
    SinglePointRelativeCrossOver,
)
from pynguin.ga.operators.selection.rankselection import RankSelection
from pynguin.ga.operators.selection.selection import SelectionFunction
from pynguin.generation.algorithms.randomsearch.randomsearchstrategy import (
    RandomSearchStrategy,
)
from pynguin.generation.algorithms.randoopy.randomteststrategy import RandomTestStrategy
from pynguin.generation.algorithms.testgenerationstrategy import TestGenerationStrategy
from pynguin.generation.algorithms.wspy.wholesuiteteststrategy import (
    WholeSuiteTestStrategy,
)
from pynguin.generation.stoppingconditions.maxiterationsstoppingcondition import (
    MaxIterationsStoppingCondition,
)
from pynguin.generation.stoppingconditions.maxtestsstoppingcondition import (
    MaxTestsStoppingCondition,
)
from pynguin.generation.stoppingconditions.maxtimestoppingcondition import (
    MaxTimeStoppingCondition,
)
from pynguin.generation.stoppingconditions.stoppingcondition import StoppingCondition
from pynguin.setup.testcluster import TestCluster
from pynguin.testcase.execution.testcaseexecutor import TestCaseExecutor
from pynguin.utils.exceptions import ConfigurationException

C = TypeVar("C", bound=chrom.Chromosome)  # pylint: disable=invalid-name


class GenerationAlgorithmFactory(Generic[C], metaclass=ABCMeta):
    """A generic generation algorithm factory."""

    _logger = logging.getLogger(__name__)

    def get_stopping_condition(self) -> StoppingCondition:
        """Instantiates the stopping condition depending on the configuration settings.

        Returns:
            A stopping condition
        """
        stopping_condition = config.INSTANCE.stopping_condition
        self._logger.info("Setting stopping condition: %s", stopping_condition)
        if stopping_condition == config.StoppingCondition.MAX_ITERATIONS:
            return MaxIterationsStoppingCondition()
        if stopping_condition == config.StoppingCondition.MAX_TESTS:
            return MaxTestsStoppingCondition()
        if stopping_condition == config.StoppingCondition.MAX_TIME:
            return MaxTimeStoppingCondition()
        self._logger.warning("Unknown stopping condition: %s", stopping_condition)
        return MaxIterationsStoppingCondition()

    @abstractmethod
    def get_search_algorithm(self) -> TestGenerationStrategy:
        """Initialises and sets up the test-generation strategy to use.

        Returns:
            A fully configured test-generation strategy  # noqa: DAR202
        """


# pylint: disable=unsubscriptable-object, too-few-public-methods
class TestSuiteGenerationAlgorithmFactory(
    GenerationAlgorithmFactory[tsc.TestSuiteChromosome]
):
    """A factory for a search algorithm generating test-suites."""

    _strategies: Dict[config.Algorithm, Callable[[], TestGenerationStrategy]] = {
        config.Algorithm.RANDOOPY: RandomTestStrategy,
        config.Algorithm.RANDOMSEARCH: RandomSearchStrategy,
        config.Algorithm.WSPY: WholeSuiteTestStrategy,
    }

    def __init__(self, executor: TestCaseExecutor, test_cluster: TestCluster):
        self._executor = executor
        self._test_cluster = test_cluster
        self._test_factory = tf.TestFactory(self._test_cluster)

    def _get_chromosome_factory(self) -> cf.ChromosomeFactory:
        """Provides a chromosome factory.

        Returns:
            A chromosome factory
        """
        # TODO add conditional returns/other factories here
        test_case_factory = tcf.RandomLengthTestCaseFactory(self._test_factory)
        test_case_chromosome_factory = tccf.TestCaseChromosomeFactory(
            self._test_factory, test_case_factory
        )
        return tscf.TestSuiteChromosomeFactory(test_case_chromosome_factory)

    def get_search_algorithm(self) -> TestGenerationStrategy:
        """Initialises and sets up the test-generation strategy to use.

        Returns:
            A fully configured test-generation strategy
        """
        chromosome_factory = self._get_chromosome_factory()
        strategy = self._get_generation_strategy()

        strategy.chromosome_factory = chromosome_factory
        strategy.executor = self._executor
        strategy.test_cluster = self._test_cluster
        strategy.test_factory = self._test_factory

        selection_function = self._get_selection_function()
        selection_function.maximize = False
        strategy.selection_function = selection_function

        stopping_condition = self.get_stopping_condition()
        strategy.stopping_condition = stopping_condition
        strategy.reset_stopping_conditions()

        crossover_function = self._get_crossover_function()
        strategy.crossover_function = crossover_function

        return strategy

    @classmethod
    def _get_generation_strategy(cls) -> TestGenerationStrategy:
        """Provides a generation strategy.

        Returns:
            A generation strategy

        Raises:
            ConfigurationException: if an unknown algorithm was requested
        """
        if config.INSTANCE.algorithm in cls._strategies:
            strategy = cls._strategies.get(config.INSTANCE.algorithm)
            assert strategy, "Strategy cannot be defined as None"
            return strategy()
        raise ConfigurationException("No suitable generation strategy found.")

    def _get_selection_function(self) -> SelectionFunction[tsc.TestSuiteChromosome]:
        """Provides a selection function for the selected algorithm.

        Returns:
            A selection function
        """
        self._logger.info("Chosen selection function: RankSelection")
        return RankSelection()

    def _get_crossover_function(self) -> CrossOverFunction[tsc.TestSuiteChromosome]:
        """Provides a crossover function for the selected algorithm.

        Returns:
            A crossover function
        """
        self._logger.info("Chosen crossover function: SinglePointRelativeCrossOver()")
        return SinglePointRelativeCrossOver()
