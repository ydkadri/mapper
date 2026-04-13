"""Quality rule executor for running quality checks."""

from mapper import graph
from mapper.quality import config, models, registry


class QualityExecutor:
    """Executes quality rules against a package in Neo4j."""

    def __init__(self, connection: graph.Neo4jConnection):
        """Initialize executor with Neo4j connection.

        Args:
            connection: Neo4j database connection
        """
        self.connection = connection
        self.registry = registry.get_registry()

    def execute(
        self, rule_name: str, package: str, quality_config: models.QualityConfig | None = None
    ) -> models.CoverageQualityResult | models.ComplexityQualityResult:
        """Execute a single quality rule.

        Args:
            rule_name: Name of the rule to execute (e.g., 'type-coverage')
            package: Package name to check
            quality_config: Quality configuration (loads from file if None)

        Returns:
            Quality result for the rule

        Raises:
            ValueError: If rule not found or disabled
        """
        # Load config if not provided
        if quality_config is None:
            quality_config = config.load_quality_config()

        # Get rule from registry
        rule = self.registry.get(rule_name)
        if rule is None:
            available = ", ".join(self.registry.get_rule_names())
            raise ValueError(
                f"Quality rule '{rule_name}' not found. Available rules: {available}"
            )

        # Check if rule is enabled
        if not rule.is_enabled(quality_config):
            raise ValueError(f"Quality rule '{rule_name}' is disabled in configuration")

        # Execute rule
        return rule.run(self.connection, package)

    def execute_all(
        self, package: str, quality_config: models.QualityConfig | None = None
    ) -> list[models.CoverageQualityResult | models.ComplexityQualityResult]:
        """Execute all enabled quality rules.

        Args:
            package: Package name to check
            quality_config: Quality configuration (loads from file if None)

        Returns:
            List of quality results for all enabled rules

        Raises:
            ValueError: If no rules are enabled
        """
        # Load config if not provided
        if quality_config is None:
            quality_config = config.load_quality_config()

        # Get all rules and filter enabled
        all_rules = self.registry.list_all()
        enabled_rules = [rule for rule in all_rules if rule.is_enabled(quality_config)]

        if not enabled_rules:
            raise ValueError("No quality rules are enabled in configuration")

        # Execute all enabled rules
        results = []
        for rule in enabled_rules:
            result = rule.run(self.connection, package)
            results.append(result)

        return results
