"""Unit tests for quality rule registry."""

from mapper.quality import registry


class TestRegistry:
    """Test quality rule registry functions."""

    def test_get_rule_type_coverage(self):
        """Should return type coverage rule by name."""
        reg = registry.get_registry()
        rule = reg.get("type-coverage")
        assert rule is not None
        assert rule.name == "type-coverage"

    def test_get_rule_docstring_coverage(self):
        """Should return docstring coverage rule by name."""
        reg = registry.get_registry()
        rule = reg.get("docstring-coverage")
        assert rule is not None
        assert rule.name == "docstring-coverage"

    def test_get_rule_param_complexity(self):
        """Should return param complexity rule by name."""
        reg = registry.get_registry()
        rule = reg.get("param-complexity")
        assert rule is not None
        assert rule.name == "param-complexity"

    def test_get_rule_nonexistent(self):
        """Should return None for nonexistent rule."""
        reg = registry.get_registry()
        rule = reg.get("nonexistent_rule")
        assert rule is None

    def test_list_all(self):
        """Should return all registered rules."""
        reg = registry.get_registry()
        rules = reg.list_all()
        assert len(rules) == 3
        rule_names = [r.name for r in rules]
        assert "type-coverage" in rule_names
        assert "docstring-coverage" in rule_names
        assert "param-complexity" in rule_names

    def test_get_rule_names(self):
        """Should return names of all registered rules."""
        reg = registry.get_registry()
        names = reg.get_rule_names()
        assert len(names) == 3
        assert "type-coverage" in names
        assert "docstring-coverage" in names
        assert "param-complexity" in names

    def test_singleton_pattern(self):
        """Should return same registry instance."""
        reg1 = registry.get_registry()
        reg2 = registry.get_registry()
        assert reg1 is reg2
