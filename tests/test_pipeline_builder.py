#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Test pipeline builder used for building pipeline configuration."""

from typing import Union
from typing import Dict

import flexmock
import pytest

from thoth.adviser.pipeline_builder import PipelineBuilder
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.unit import Unit
from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import DecisionType

import tests.units as units

from .base import AdviserTestCase
from .helpers import use_test_units


@pytest.fixture
def builder_context() -> PipelineBuilderContext:
    """Fixture for a builder context."""
    builder_context = PipelineBuilderContext(
        graph=None,
        project=None,
        library_usage=None,
        decision_type=DecisionType.RANDOM,
        recommendation_type=None,
    )
    builder_context.add_unit(units.boots.Boot1())
    builder_context.add_unit(units.sieves.Sieve1())
    builder_context.add_unit(units.steps.Step1())
    builder_context.add_unit(units.strides.Stride1())
    builder_context.add_unit(units.wraps.Wrap1())
    return builder_context


class TestPipelineBuilderContext(AdviserTestCase):
    """Test context carried within pipeline builder."""

    def test_is_included(self, builder_context: PipelineBuilderContext) -> None:
        """Test check if the given pipeline unit is included."""
        assert builder_context.is_included(units.boots.Boot1)
        assert not builder_context.is_included(units.boots.Boot2)
        assert builder_context.is_included(units.sieves.Sieve1)
        assert not builder_context.is_included(units.sieves.Sieve2)
        assert builder_context.is_included(units.steps.Step1)
        assert not builder_context.is_included(units.steps.Step2)
        assert builder_context.is_included(units.strides.Stride1)
        assert not builder_context.is_included(units.strides.Stride2)
        assert builder_context.is_included(units.wraps.Wrap1)
        assert not builder_context.is_included(units.wraps.Wrap2)

    def test_is_adviser_pipeline(self) -> None:
        """Test check for an adviser build context."""
        builder_context = PipelineBuilderContext(
            graph=None,
            project=None,
            library_usage=None,
            decision_type=None,
            recommendation_type=RecommendationType.LATEST,
        )
        assert builder_context.is_adviser_pipeline()
        assert not builder_context.is_dependency_monkey_pipeline()

    def test_is_dependency_monkey_pipeline(self) -> None:
        """Test check for a dependency monkey build context."""
        builder_context = PipelineBuilderContext(
            graph=None,
            project=None,
            library_usage=None,
            decision_type=DecisionType.RANDOM,
            recommendation_type=None,
        )
        assert builder_context.is_dependency_monkey_pipeline()
        assert not builder_context.is_adviser_pipeline()

    def test_invalid_pipeline_builder_context(self) -> None:
        """Test check an invalid build context."""
        # Exactly one from decision type/recommendation type has to be specified.
        with pytest.raises(ValueError):
            PipelineBuilderContext(
                graph=None,
                project=None,
                library_usage=None,
                decision_type=None,
                recommendation_type=None,
            )

        with pytest.raises(ValueError):
            PipelineBuilderContext(
                graph=None,
                project=None,
                library_usage=None,
                decision_type=DecisionType.ALL,
                recommendation_type=RecommendationType.LATEST,
            )

    @pytest.mark.parametrize(
        "unit_class,builder_context_attr",
        [
            (units.boots.Boot2, "boots"),
            (units.sieves.Sieve2, "sieves"),
            (units.steps.Step2, "steps"),
            (units.strides.Stride2, "strides"),
            (units.wraps.Wrap2, "wraps"),
        ],
    )
    def test_add_unit(
        self,
        builder_context: PipelineBuilderContext,
        unit_class: Unit,
        builder_context_attr: str,
    ) -> None:
        """Test addition of a unit."""
        assert not builder_context.is_included(unit_class)
        unit = unit_class()
        builder_context.add_unit(unit)
        assert builder_context.is_included(unit_class)
        assert getattr(builder_context, builder_context_attr)[-1] is unit


class TestPipelineBuilder(AdviserTestCase):
    """Tests related to pipeline builder."""

    @use_test_units
    @pytest.mark.parametrize(
        "pipeline_config_method,kwargs",
        [
            (
                "get_adviser_pipeline_config",
                {"recommendation_type": RecommendationType.LATEST},
            ),
            (
                "get_dependency_monkey_pipeline_config",
                {"decision_type": DecisionType.RANDOM},
            ),
        ],
    )
    def test_build_configuration(self, pipeline_config_method: str, kwargs: Dict[str, Union[RecommendationType, DecisionType]]) -> None:
        """Test building configuration."""
        # All test units do not register themselves - let's cherry-pick ones that should be present.
        # There are done 3 iterations in total during pipeline configuration creation.
        flexmock(units.boots.Boot1).should_receive("should_include").and_return(
            {"some_parameter": 1.0}
        ).and_return(None).and_return(None).times(3)
        flexmock(units.sieves.Sieve2).should_receive("should_include").and_return(
            {"foo": "bar"}
        ).and_return(None).and_return(None).times(3)
        flexmock(units.steps.Step1).should_receive("should_include").and_return(
            {}
        ).and_return(None).and_return(None).times(3)
        flexmock(units.strides.Stride2).should_receive("should_include").and_return(
            {}
        ).and_return(None).and_return(None).times(3)
        flexmock(units.strides.Stride1).should_receive("should_include").and_return(
            None
        ).and_return({"linus": "torvalds"}).and_return(None).times(3)
        flexmock(units.wraps.Wrap2).should_receive("should_include").and_return(
            {}
        ).and_return(None).and_return(None).times(3)

        # It is not relevant if adviser/dependency monkey is called in this case.
        pipeline = getattr(PipelineBuilder, pipeline_config_method)(
            graph=None, project=None, library_usage=None, **kwargs
        )

        assert pipeline.to_dict() == {
            "boots": [{"name": "Boot1", "configuration": {"some_parameter": 1.0}}],
            "sieves": [
                {
                    "name": "Sieve2",
                    "configuration": {"date": "2015-09-15", "foo": "bar"},
                }
            ],
            "steps": [{"name": "Step1", "configuration": {"guido_retirement": 2019}}],
            "strides": [
                {"name": "Stride2", "configuration": {"foo": None}},
                {"name": "Stride1", "configuration": {"linus": "torvalds"}},
            ],
            "wraps": [{"name": "Wrap2", "configuration": {}}],
        }