"""Output formatters for quality rule results."""

import csv
import io
import json
from enum import Enum
from typing import Protocol

from rich.console import Console

from mapper.quality import models


class OutputFormat(str, Enum):  # noqa: UP042
    """Output format types for quality rule results.

    String-backed enum for compatibility with string operations while providing
    type safety and validation. Uses (str, Enum) pattern for Python 3.10+ compatibility
    (StrEnum is only available in Python 3.11+).
    """

    CONSOLE = "console"
    JSON = "json"
    CSV = "csv"


class FormatsQualityResults(Protocol):
    """Protocol for quality result formatters.

    All formatters must implement format_results() to return a string representation
    of quality results. This allows formatters to be used consistently across
    different output contexts (CLI, file, tests).
    """

    def format_results(
        self, results: list[models.CoverageQualityResult | models.ComplexityQualityResult]
    ) -> str:
        """Format quality results as string.

        Args:
            results: List of quality rule results to format

        Returns:
            Formatted string ready for output
        """
        ...


class ConsoleFormatter:
    """Format quality results for human-readable console output."""

    def _format_check_mark(self, status: str) -> str:
        """Get check mark symbol for status.

        Args:
            status: "pass" or "fail"

        Returns:
            Colored check mark or X symbol
        """
        if status == "pass":
            return "[bold green]✓[/bold green]"
        else:
            return "[bold red]✗[/bold red]"

    def _format_coverage_result(
        self, result: models.CoverageQualityResult, show_details: bool = False
    ) -> str:
        """Format a coverage-based result (type/docstring coverage).

        Args:
            result: Coverage quality result
            show_details: Whether to show file-level breakdown

        Returns:
            Formatted string
        """
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        # Summary line
        check = self._format_check_mark(result.status)
        rule_name = result.rule.replace("-", " ").title()
        console.print(f"{check} {rule_name}: {result.actual:.1f}% (threshold: {result.threshold}%)")

        # File breakdown if requested
        if show_details and result.by_file:
            console.print("\n  By File:")
            for file_result in result.by_file:
                status_icon = "✓" if file_result.percentage >= result.threshold else "✗"
                console.print(
                    f"  {file_result.path:50s}  {file_result.compliant}/{file_result.total}  ({file_result.percentage:.0f}%) {status_icon}"
                )

            console.print(
                f"\n  Overall: {result.overall.compliant}/{result.overall.total} "
                f"functions meet the standard"
            )

            # Show violations if any
            if result.status == "fail":
                all_violations = []
                for file_result in result.by_file:
                    if file_result.violations:
                        for violation in file_result.violations:
                            all_violations.append(f"{file_result.path}:{violation}")

                if all_violations:
                    console.print("\n  Missing coverage:")
                    for violation in all_violations[:10]:  # Limit to 10
                        console.print(f"  - {violation}")
                    if len(all_violations) > 10:
                        console.print(f"  ... and {len(all_violations) - 10} more")

        return output.getvalue()

    def _format_complexity_result(
        self, result: models.ComplexityQualityResult, show_details: bool = False
    ) -> str:
        """Format a complexity-based result (parameter complexity).

        Args:
            result: Complexity quality result
            show_details: Whether to show violation details

        Returns:
            Formatted string
        """
        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        # Summary line
        check = self._format_check_mark(result.status)
        rule_name = result.rule.replace("-", " ").title()

        if result.total_violations == 0:
            console.print(
                f"{check} {rule_name}: No violations (max: {result.threshold} parameters)"
            )
        else:
            console.print(
                f"{check} {rule_name}: {result.total_violations} violations (max: {result.threshold} parameters)"
            )

        # Violation details if requested
        if show_details and result.by_file:
            console.print("\n  Functions exceeding threshold:")
            for file_violations in result.by_file:
                console.print(f"\n  {file_violations.path}:")
                for violation in file_violations.violations:
                    console.print(
                        f"    - {violation.function} (line {violation.line}): {violation.param_count} parameters"
                    )

        return output.getvalue()

    def format_results(
        self, results: list[models.CoverageQualityResult | models.ComplexityQualityResult]
    ) -> str:
        """Format quality results for console output.

        For multiple results (mapper quality check), shows summary.
        For single result, shows detailed breakdown.

        Args:
            results: List of quality rule results

        Returns:
            Formatted console output with Rich markup
        """
        if len(results) == 0:
            return ""

        output = io.StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        show_details = len(results) == 1

        if len(results) > 1:
            console.print("\n[bold]Running quality checks...[/bold]\n")

        # Format each result
        for result in results:
            if isinstance(result, models.CoverageQualityResult):
                console.print(self._format_coverage_result(result, show_details))
            else:  # ComplexityQualityResult
                console.print(self._format_complexity_result(result, show_details))

        # Overall summary for multiple checks
        if len(results) > 1:
            failed_count = sum(1 for r in results if r.status == "fail")
            if failed_count > 0:
                console.print(f"\n{failed_count} of {len(results)} checks failed")
            else:
                console.print(f"\n[bold green]All {len(results)} checks passed[/bold green]")

        console.print()  # Trailing newline

        return output.getvalue()


class JSONFormatter:
    """Format quality results as JSON."""

    def _format_coverage_result(self, result: models.CoverageQualityResult) -> dict:
        """Convert coverage result to dict for JSON serialization.

        Args:
            result: Coverage quality result

        Returns:
            Dictionary representation
        """
        return {
            "rule": result.rule,
            "status": result.status,
            "threshold": result.threshold,
            "actual": result.actual,
            "overall": {
                "total": result.overall.total,
                "compliant": result.overall.compliant,
                "percentage": result.overall.percentage,
            },
            "by_file": [
                {
                    "path": fr.path,
                    "total": fr.total,
                    "compliant": fr.compliant,
                    "percentage": fr.percentage,
                    "violations": fr.violations,
                }
                for fr in result.by_file
            ],
        }

    def _format_complexity_result(self, result: models.ComplexityQualityResult) -> dict:
        """Convert complexity result to dict for JSON serialization.

        Args:
            result: Complexity quality result

        Returns:
            Dictionary representation
        """
        return {
            "rule": result.rule,
            "status": result.status,
            "threshold": result.threshold,
            "total_violations": result.total_violations,
            "by_file": [
                {
                    "path": fv.path,
                    "violations": [
                        {
                            "function": v.function,
                            "line": v.line,
                            "param_count": v.param_count,
                        }
                        for v in fv.violations
                    ],
                }
                for fv in result.by_file
            ],
        }

    def format_results(
        self, results: list[models.CoverageQualityResult | models.ComplexityQualityResult]
    ) -> str:
        """Format quality results as JSON.

        Args:
            results: List of quality rule results

        Returns:
            JSON-formatted string (array of rule results)
        """
        output = []
        for result in results:
            if isinstance(result, models.CoverageQualityResult):
                output.append(self._format_coverage_result(result))
            else:  # ComplexityQualityResult
                output.append(self._format_complexity_result(result))

        return json.dumps(output, indent=2)


class CSVFormatter:
    """Format quality results as CSV."""

    def _format_coverage_csv(self, result: models.CoverageQualityResult) -> str:
        """Format coverage result as CSV rows.

        Args:
            result: Coverage quality result

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write rows (one per file)
        for file_result in result.by_file:
            status = "pass" if file_result.percentage >= result.threshold else "fail"
            writer.writerow(
                [
                    result.rule,
                    file_result.path,
                    file_result.total,
                    file_result.compliant,
                    f"{file_result.percentage:.1f}",
                    status,
                ]
            )

        return output.getvalue()

    def _format_complexity_csv(self, result: models.ComplexityQualityResult) -> str:
        """Format complexity result as CSV rows.

        Args:
            result: Complexity quality result

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write rows (one per violation)
        for file_violations in result.by_file:
            for violation in file_violations.violations:
                writer.writerow(
                    [
                        result.rule,
                        file_violations.path,
                        violation.function,
                        violation.line,
                        violation.param_count,
                        "fail",
                    ]
                )

        return output.getvalue()

    def format_results(
        self, results: list[models.CoverageQualityResult | models.ComplexityQualityResult]
    ) -> str:
        """Format quality results as CSV.

        Different schemas for coverage vs complexity rules:
        - Coverage: rule,file_path,total_functions,compliant_functions,compliance_percentage,status
        - Complexity: rule,file_path,function_name,line_number,parameter_count,status

        Args:
            results: List of quality rule results

        Returns:
            CSV-formatted string with headers
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Separate coverage and complexity results
        coverage_results: list[models.CoverageQualityResult] = [
            r for r in results if isinstance(r, models.CoverageQualityResult)
        ]
        complexity_results: list[models.ComplexityQualityResult] = [
            r for r in results if isinstance(r, models.ComplexityQualityResult)
        ]

        # Write coverage results with header
        if coverage_results:
            writer.writerow(
                [
                    "rule",
                    "file_path",
                    "total_functions",
                    "compliant_functions",
                    "compliance_percentage",
                    "status",
                ]
            )
            for coverage_result in coverage_results:
                output.write(self._format_coverage_csv(coverage_result))

        # Write complexity results with header
        if complexity_results:
            writer.writerow(
                ["rule", "file_path", "function_name", "line_number", "parameter_count", "status"]
            )
            for complexity_result in complexity_results:
                output.write(self._format_complexity_csv(complexity_result))

        return output.getvalue()


def get_formatter(format_type: OutputFormat) -> FormatsQualityResults:
    """Get formatter for the specified format type.

    Args:
        format_type: Format type (OutputFormat enum)

    Returns:
        Appropriate formatter instance
    """
    match format_type:
        case OutputFormat.CONSOLE:
            return ConsoleFormatter()
        case OutputFormat.JSON:
            return JSONFormatter()
        case OutputFormat.CSV:
            return CSVFormatter()
