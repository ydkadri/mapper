"""Tests for built-in queries."""

from mapper.query_system.group import QueryGroup
from mapper.query_system.queries import critical_functions, dead_code, module_centrality
from mapper.query_system.query import Severity


class TestDeadCodeQuery:
    """Tests for find-dead-code query."""

    def test_query_properties(self):
        """Test query has correct properties."""
        q = dead_code.QUERY

        assert q.name == "find-dead-code"
        assert q.group == QueryGroup.RISK
        assert "unused" in q.description.lower()
        assert "$package" in q.cypher
        assert len(q.columns) == 4

    def test_severity_calculation_public(self):
        """Test severity for public unused code."""
        row = {"is_public": True, "fqn": "test.func", "type": "Function"}
        severity = dead_code.QUERY._calculate_severity_impl(row)
        assert severity == Severity.HIGH

    def test_severity_calculation_private(self):
        """Test severity for private unused code."""
        row = {"is_public": False, "fqn": "test._func", "type": "Function"}
        severity = dead_code.QUERY._calculate_severity_impl(row)
        assert severity == Severity.MEDIUM


class TestModuleCentralityQuery:
    """Tests for analyze-module-centrality query."""

    def test_query_properties(self):
        """Test query has correct properties."""
        q = module_centrality.QUERY

        assert q.name == "analyze-module-centrality"
        assert q.group == QueryGroup.CRITICAL
        assert "depended" in q.description.lower()
        assert "$package" in q.cypher
        assert "DEPENDS_ON" in q.cypher
        assert len(q.columns) == 4

    def test_severity_calculation_critical(self):
        """Test severity for modules with >10 dependents."""
        row = {"module": "test.core", "dependents": 15}
        severity = module_centrality.QUERY._calculate_severity_impl(row)
        assert severity == Severity.CRITICAL

    def test_severity_calculation_high(self):
        """Test severity for modules with 6-10 dependents."""
        row = {"module": "test.utils", "dependents": 8}
        severity = module_centrality.QUERY._calculate_severity_impl(row)
        assert severity == Severity.HIGH

    def test_severity_calculation_medium(self):
        """Test severity for modules with 3-5 dependents."""
        row = {"module": "test.helpers", "dependents": 4}
        severity = module_centrality.QUERY._calculate_severity_impl(row)
        assert severity == Severity.MEDIUM

    def test_risk_description_critical(self):
        """Test risk description for critical modules."""
        row = {"module": "test.core", "dependents": 15}
        risk = module_centrality.QUERY._get_risk_description(row)
        assert "single point" in risk.lower() or "failure" in risk.lower()

    def test_risk_description_high(self):
        """Test risk description for high impact modules."""
        row = {"module": "test.utils", "dependents": 8}
        risk = module_centrality.QUERY._get_risk_description(row)
        assert "blast radius" in risk.lower() or "high" in risk.lower()

    def test_risk_description_medium(self):
        """Test risk description for moderate impact modules."""
        row = {"module": "test.helpers", "dependents": 4}
        risk = module_centrality.QUERY._get_risk_description(row)
        assert "moderate" in risk.lower() or "coupling" in risk.lower()


class TestCriticalFunctionsQuery:
    """Tests for find-critical-functions query."""

    def test_query_properties(self):
        """Test query has correct properties."""
        q = critical_functions.QUERY

        assert q.name == "find-critical-functions"
        assert q.group == QueryGroup.CRITICAL
        assert "called" in q.description.lower()
        assert "$package" in q.cypher
        assert "CALLS" in q.cypher
        assert len(q.columns) == 4

    def test_severity_calculation_critical(self):
        """Test severity for functions with >20 callers."""
        row = {"function": "test.auth", "callers": 25}
        severity = critical_functions.QUERY._calculate_severity_impl(row)
        assert severity == Severity.CRITICAL

    def test_severity_calculation_high(self):
        """Test severity for functions with 10-20 callers."""
        row = {"function": "test.serialize", "callers": 15}
        severity = critical_functions.QUERY._calculate_severity_impl(row)
        assert severity == Severity.HIGH

    def test_severity_calculation_medium(self):
        """Test severity for functions with 5-9 callers."""
        row = {"function": "test.helper", "callers": 7}
        severity = critical_functions.QUERY._calculate_severity_impl(row)
        assert severity == Severity.MEDIUM

    def test_risk_description_critical(self):
        """Test risk description for critical functions."""
        row = {"function": "test.auth", "callers": 25}
        risk = critical_functions.QUERY._get_risk_description(row)
        assert risk == "High blast radius"

    def test_risk_description_high(self):
        """Test risk description for high impact functions."""
        row = {"function": "test.serialize", "callers": 15}
        risk = critical_functions.QUERY._get_risk_description(row)
        assert risk == "Significant coupling"

    def test_risk_description_medium(self):
        """Test risk description for moderate impact functions."""
        row = {"function": "test.helper", "callers": 7}
        risk = critical_functions.QUERY._get_risk_description(row)
        assert risk == "Moderate usage"
