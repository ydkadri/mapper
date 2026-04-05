"""Unit tests for quality rule registry."""

from mapper.quality import registry


class TestRegistry:
    """Test quality rule registry functions."""

    def test_get_rule_type_coverage(self):
        """Should return type coverage rule by name."""
        rule = registry.get_rule("type_coverage")
        assert rule is not None
        assert rule.name == "type_coverage"

    def test_get_rule_docstring_coverage(self):
        """Should return docstring coverage rule by name."""
        rule = registry.get_rule("docstring_coverage")
        assert rule is not None
        assert rule.name == "docstring_coverage"

    def test_get_rule_param_complexity(self):
        """Should return param complexity rule by name."""
        rule = registry.get_rule("param_complexity")
        assert rule is not None
        assert rule.name == "param_complexity"

    def test_get_rule_nonexistent(self):
        """Should return None for nonexistent rule."""
        rule = registry.get_rule("nonexistent_rule")
        assert rule is None

    def test_get_all_rules(self):
        """Should return all registered rules."""
        rules = registry.get_all_rules()
        assert len(rules) == 3
        rule_names = [r.name for r in rules]
        assert "type_coverage" in rule_names
        assert "docstring_coverage" in rule_names
        assert "param_complexity" in rule_names

    def test_get_rule_names(self):
        """Should return names of all registered rules."""
        names = registry.get_rule_names()
        assert len(names) == 3
        assert "type_coverage" in names
        assert "docstring_coverage" in names
        assert "param_complexity" in names
