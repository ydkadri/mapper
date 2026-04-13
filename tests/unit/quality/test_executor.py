"""Tests for quality rule executor."""

from unittest import mock

import pytest

from mapper.quality import executor, models


class TestQualityExecutor:
    """Test QualityExecutor class."""

    @pytest.fixture
    def mock_connection(self):
        """Create mock Neo4j connection."""
        return mock.MagicMock()

    @pytest.fixture
    def mock_config(self):
        """Create mock quality config."""
        return models.QualityConfig(
            type_coverage=models.TypeCoverageConfig(enabled=True, min_coverage=80),
            docstring_coverage=models.DocstringCoverageConfig(enabled=True, min_coverage=90),
            param_complexity=models.ParamComplexityConfig(enabled=True, max_parameters=5),
        )

    @pytest.fixture
    def sample_coverage_result(self):
        """Sample coverage result."""
        return models.CoverageQualityResult(
            rule="type-coverage",
            threshold=80,
            actual=85.0,
            overall=models.OverallResult(total=20, compliant=17, percentage=85.0),
            by_file=[],
        )

    @pytest.fixture
    def sample_complexity_result(self):
        """Sample complexity result."""
        return models.ComplexityQualityResult(
            rule="param-complexity",
            threshold=5,
            total_violations=0,
            by_file=[],
        )

    def test_init(self, mock_connection):
        """Should initialize with connection."""
        exec = executor.QualityExecutor(mock_connection)
        assert exec.connection == mock_connection
        assert exec.registry is not None

    def test_execute_success(self, mock_connection, mock_config, sample_coverage_result):
        """Should execute single rule successfully."""
        exec = executor.QualityExecutor(mock_connection)

        # Mock the rule's run method
        with mock.patch.object(exec.registry, "get") as mock_get:
            mock_rule = mock.MagicMock()
            mock_rule.is_enabled.return_value = True
            mock_rule.run.return_value = sample_coverage_result
            mock_get.return_value = mock_rule

            result = exec.execute("type-coverage", "testpackage", mock_config)

            assert result == sample_coverage_result
            mock_rule.is_enabled.assert_called_once_with(mock_config)
            mock_rule.run.assert_called_once_with(mock_connection, "testpackage")

    def test_execute_rule_not_found(self, mock_connection, mock_config):
        """Should raise ValueError if rule not found."""
        exec = executor.QualityExecutor(mock_connection)

        with mock.patch.object(exec.registry, "get") as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError, match="not found"):
                exec.execute("nonexistent-rule", "testpackage", mock_config)

    def test_execute_rule_disabled(self, mock_connection, mock_config):
        """Should raise ValueError if rule is disabled."""
        exec = executor.QualityExecutor(mock_connection)

        # Mock the rule's is_enabled to return False
        with mock.patch.object(exec.registry, "get") as mock_get:
            mock_rule = mock.MagicMock()
            mock_rule.is_enabled.return_value = False
            mock_get.return_value = mock_rule

            with pytest.raises(ValueError, match="disabled"):
                exec.execute("type-coverage", "testpackage", mock_config)

    def test_execute_loads_config_if_none(self, mock_connection, sample_coverage_result):
        """Should load config from file if not provided."""
        exec = executor.QualityExecutor(mock_connection)

        with mock.patch("mapper.quality.executor.config.load_quality_config") as mock_load:
            with mock.patch.object(exec.registry, "get") as mock_get:
                mock_config = models.QualityConfig()
                mock_load.return_value = mock_config

                mock_rule = mock.MagicMock()
                mock_rule.is_enabled.return_value = True
                mock_rule.run.return_value = sample_coverage_result
                mock_get.return_value = mock_rule

                result = exec.execute("type-coverage", "testpackage", None)

                mock_load.assert_called_once_with()
                assert result == sample_coverage_result

    def test_execute_all_success(
        self, mock_connection, mock_config, sample_coverage_result, sample_complexity_result
    ):
        """Should execute all enabled rules."""
        exec = executor.QualityExecutor(mock_connection)

        # Create mock rules
        mock_rule1 = mock.MagicMock()
        mock_rule1.is_enabled.return_value = True
        mock_rule1.run.return_value = sample_coverage_result

        mock_rule2 = mock.MagicMock()
        mock_rule2.is_enabled.return_value = True
        mock_rule2.run.return_value = sample_complexity_result

        with mock.patch.object(exec.registry, "list_all") as mock_list:
            mock_list.return_value = [mock_rule1, mock_rule2]

            results = exec.execute_all("testpackage", mock_config)

            assert len(results) == 2
            assert results[0] == sample_coverage_result
            assert results[1] == sample_complexity_result

    def test_execute_all_filters_disabled(
        self, mock_connection, mock_config, sample_coverage_result
    ):
        """Should filter out disabled rules."""
        exec = executor.QualityExecutor(mock_connection)

        # Create mock rules (one enabled, one disabled)
        mock_rule1 = mock.MagicMock()
        mock_rule1.is_enabled.return_value = True
        mock_rule1.run.return_value = sample_coverage_result

        mock_rule2 = mock.MagicMock()
        mock_rule2.is_enabled.return_value = False

        with mock.patch.object(exec.registry, "list_all") as mock_list:
            mock_list.return_value = [mock_rule1, mock_rule2]

            results = exec.execute_all("testpackage", mock_config)

            assert len(results) == 1
            assert results[0] == sample_coverage_result
            mock_rule2.run.assert_not_called()

    def test_execute_all_no_enabled_rules(self, mock_connection, mock_config):
        """Should raise ValueError if no rules are enabled."""
        exec = executor.QualityExecutor(mock_connection)

        # Create mock disabled rule
        mock_rule = mock.MagicMock()
        mock_rule.is_enabled.return_value = False

        with mock.patch.object(exec.registry, "list_all") as mock_list:
            mock_list.return_value = [mock_rule]

            with pytest.raises(ValueError, match="No quality rules are enabled"):
                exec.execute_all("testpackage", mock_config)

    def test_execute_all_loads_config_if_none(
        self, mock_connection, sample_coverage_result
    ):
        """Should load config from file if not provided."""
        exec = executor.QualityExecutor(mock_connection)

        with mock.patch("mapper.quality.executor.config.load_quality_config") as mock_load:
            with mock.patch.object(exec.registry, "list_all") as mock_list:
                mock_config = models.QualityConfig()
                mock_load.return_value = mock_config

                mock_rule = mock.MagicMock()
                mock_rule.is_enabled.return_value = True
                mock_rule.run.return_value = sample_coverage_result
                mock_list.return_value = [mock_rule]

                results = exec.execute_all("testpackage", None)

                mock_load.assert_called_once_with()
                assert len(results) == 1
