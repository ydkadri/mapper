"""Parameter complexity quality rule implementation."""

import fnmatch

import attrs

from mapper import graph
from mapper.quality import models


@attrs.define(frozen=True)
class ParamComplexityRule(models.QualityRule):
    """Quality rule for enforcing parameter count limits on functions."""

    name: str = "param-complexity"
    description: str = "Enforce parameter count limits on functions"

    def is_enabled(self, config: models.QualityConfig) -> bool:
        """Check if rule is enabled in configuration."""
        return config.param_complexity.enabled

    def run(
        self, neo4j_connection: graph.Neo4jConnection, package: str
    ) -> models.ComplexityQualityResult:
        """Execute parameter complexity rule and return result.

        Args:
            neo4j_connection: Neo4j connection
            package: Package name to check

        Returns:
            ComplexityQualityResult with pass/fail status
        """
        # Load configuration
        from mapper.quality import config as config_module

        cfg = config_module.load_quality_config()
        param_cfg = cfg.param_complexity

        # Build Cypher query to find functions exceeding parameter threshold
        query = """
        MATCH (m:Module)-[:DEFINES]->(f:Function {package: $package})
        WHERE f.is_public = true

        // Count parameters via HAS_PARAMETER relationships
        OPTIONAL MATCH (f)-[:HAS_PARAMETER]->(p:Parameter)
        WITH m, f, count(p) as param_count
        WHERE param_count > $max_parameters

        // Return violations grouped by file (using Module.path)
        RETURN m.path as file_path,
               collect({
                 function: f.name,
                 line: null,
                 param_count: param_count
               }) as violations
        ORDER BY file_path
        """

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            result = session.run(query, package=package, max_parameters=param_cfg.max_parameters)
            records = list(result)

        # Process results
        file_violations = []
        total_violations = 0

        for record in records:
            file_path = record["file_path"]
            violations_data = record["violations"]

            # Apply exclude patterns
            filtered_violations = []
            for v in violations_data:
                func_name = v["function"]
                if not any(
                    fnmatch.fnmatch(func_name, pattern) for pattern in param_cfg.exclude_patterns
                ):
                    filtered_violations.append(
                        models.ViolationDetail(
                            function=func_name,
                            line=v["line"],
                            param_count=v["param_count"],
                        )
                    )

            if filtered_violations:
                file_violations.append(
                    models.FileViolations(
                        path=file_path,
                        violations=filtered_violations,
                    )
                )
                total_violations += len(filtered_violations)

        return models.ComplexityQualityResult(
            rule=self.name,
            threshold=param_cfg.max_parameters,
            total_violations=total_violations,
            by_file=file_violations,
        )
