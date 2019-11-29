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

"""Test adviser's context passed to pipeline units."""

from typing import Tuple

import pytest

from thoth.python import PackageVersion
from thoth.python import Source

from thoth.adviser.context import Context
from thoth.adviser.enums import RecommendationType
from thoth.adviser.enums import DecisionType
from thoth.adviser.exceptions import NotFound

from .base import AdviserTestCase


@pytest.fixture
def context() -> Context:
    """A fixture for a clean context."""
    return Context(
        project=None,
        graph=None,
        library_usage=None,
        limit=None,
        count=None,
        recommendation_type=RecommendationType.TESTING,
    )


@pytest.fixture
def package_version() -> PackageVersion:
    """A fixture for a package version representative."""
    return PackageVersion(
        name="selinon",
        version="==1.0.0",
        index=Source("https://pypi.org/simple"),
        develop=False,
    )


@pytest.fixture
def package_tuple() -> Tuple[str, str, str]:
    """A fixture for a package tuple representative."""
    return "selinon", "1.0.0", "https://pypi.org/simple"


class TestContext(AdviserTestCase):
    """Test context carried within resolution."""

    def test_get_package_version(
        self, context: Context, package_version: PackageVersion
    ) -> None:
        """Test getting registering and getting a package version."""
        with pytest.raises(NotFound):
            context.get_package_version(package_version.to_tuple())

        assert context.register_package_version(package_version) is False
        assert (
            context.get_package_version(package_version.to_tuple()) is package_version
        )

    def test_get_package_version_graceful(self, context: Context, package_version: PackageVersion) -> None:
        """Test getting registered package version, gracefully."""
        assert context.get_package_version(package_version.to_tuple(), graceful=True) is None
        with pytest.raises(NotFound):
            context.get_package_version(package_version.to_tuple(), graceful=False)

        assert context.register_package_version(package_version) is False

        assert context.get_package_version(package_version.to_tuple(), graceful=True) is package_version
        assert context.get_package_version(package_version.to_tuple(), graceful=False) is package_version

    def test_register_package_version_existing(
        self, context: Context, package_version: PackageVersion
    ) -> None:
        """Test registering an existing package version to context."""
        assert context.register_package_version(package_version) is False
        assert (
            context.get_package_version(package_version.to_tuple()) is package_version
        )
        assert context.register_package_version(package_version) is True

    def test_register_package_tuple_new(
        self, context: Context, package_tuple: Tuple[str, str, str]
    ) -> None:
        """Test registering a new package tuple to the context."""
        with pytest.raises(NotFound):
            context.get_package_version(package_tuple)

        environment_marker = "python_version >= 3.6"
        extras = ["postgresql"]

        assert (
            context.register_package_tuple(
                package_tuple, develop=True, markers=environment_marker, extras=extras
            )
            is not None
        )

        package_version = context.get_package_version(package_tuple)

        assert package_version.name == "selinon"
        assert package_version.version == "==1.0.0"
        assert package_version.develop == True
        assert package_version.index is not None
        assert package_version.index.url == "https://pypi.org/simple"
        assert package_version.markers == environment_marker
        assert package_version.extras == extras

    def test_register_package_tuple_existing(
        self, context: Context, package_tuple: Tuple[str, str, str]
    ) -> None:
        """Check registering an existing package tuple does not instantiate a new one."""
        with pytest.raises(NotFound):
            context.get_package_version(package_tuple)

        environment_marker = "python_version >= 3.6"
        extras = ["postgresql"]

        package_version_registered = context.register_package_tuple(
            package_tuple, develop=True, markers=environment_marker, extras=extras
        )

        assert package_version_registered is not None

        package_version_another = context.register_package_tuple(
            package_tuple, develop=True, markers=environment_marker, extras=extras
        )

        assert (
            package_version_registered is package_version_another
        ), "Different instances returned"

    def test_is_dependency_monkey(self) -> None:
        """Test checking if the given context is an adviser context."""
        context = Context(
            project=None,
            graph=None,
            library_usage=None,
            limit=None,
            count=None,
            recommendation_type=None,
            decision_type=DecisionType.ALL,
        )

        assert context.is_dependency_monkey() is True
        assert context.is_adviser() is False

    def test_is_adviser(self) -> None:
        """Test checking if the given context is an adviser context."""
        context = Context(
            project=None,
            graph=None,
            library_usage=None,
            limit=None,
            count=None,
            recommendation_type=RecommendationType.LATEST,
            decision_type=None,
        )

        assert context.is_adviser() is True
        assert context.is_dependency_monkey() is False

    def test_invalid_context_no_type(self) -> None:
        """Exactly one type (recommendation/decision) has to be provided on instantiation."""
        with pytest.raises(ValueError):
            Context(
                project=None,
                graph=None,
                library_usage=None,
                limit=None,
                count=None,
                # Decision type and recommendation type cannot be set to None at the same time.
                recommendation_type=None,
                decision_type=None,
            )

    def test_invalid_context_type(self) -> None:
        """Context type cannot capture both adviser and dependency monkey type."""
        with pytest.raises(ValueError):
            Context(
                project=None,
                graph=None,
                library_usage=None,
                limit=None,
                count=None,
                # Decision type and recommendation type cannot be set at the same time.
                recommendation_type=RecommendationType.LATEST,
                decision_type=DecisionType.ALL,
            )
