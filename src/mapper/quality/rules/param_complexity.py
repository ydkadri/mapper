"""Parameter complexity quality rule implementation."""

import fnmatch

from mapper import graph
from mapper.quality import models


class ParamComplexityRule:
    """Quality rule for enforcing parameter count limits on functions."""

    @property
    def name(self) -> str:
        """Machine-readable rule name."""
        return "param_complexity"

    @property
    def display_name(self) -> str:
        """Human-readable rule name."""
        return "Parameter Complexity"

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
        MATCH (f:Function {package: $package})
        WHERE f.is_public = true
          AND size(f.parameters) > $max_parameters

        // Return violations grouped by file
        RETURN f.file_path as file_path,
               collect({
                 function: f.name,
                 line: f.start_line,
                 param_count: size(f.parameters)
               }) as violations
        ORDER BY file_path
        """

        with neo4j_connection.driver.session(
            database=neo4j_connection.database
        ) as session:
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

        # Determine pass/fail status
        status = "pass" if total_violations == 0 else "fail"

        return models.ComplexityQualityResult(
            rule=self.name,
            status=status,
            threshold=param_cfg.max_parameters,
            total_violations=total_violations,
            by_file=file_violations,
        )
