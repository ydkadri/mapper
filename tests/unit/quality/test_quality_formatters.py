"""Tests for quality result formatters."""

import json

import pytest

from mapper.quality import formatters, models


@pytest.fixture
def sample_coverage_result() -> models.CoverageQualityResult:
    """Sample coverage result for testing."""
    return models.CoverageQualityResult(
        rule="type-coverage",
        threshold=80,
        actual=85.5,
        overall=models.OverallResult(
            total=20,
            compliant=17,
            percentage=85.5,
        ),
        by_file=[
            models.FileResult(
                path="src/example/module.py",
                total=10,
                compliant=9,
                percentage=90.0,
                violations=["uncovered_func"],
            ),
            models.FileResult(
                path="src/example/utils.py",
                total=10,
                compliant=8,
                percentage=80.0,
                violations=["helper1", "helper2"],
            ),
        ],
    )


@pytest.fixture
def sample_failing_coverage_result() -> models.CoverageQualityResult:
    """Sample failing coverage result for testing."""
    return models.CoverageQualityResult(
        rule="docstring-coverage",
        threshold=90,
        actual=75.0,
        overall=models.OverallResult(
            total=20,
            compliant=15,
            percentage=75.0,
        ),
        by_file=[
            models.FileResult(
                path="src/example/api.py",
                total=20,
                compliant=15,
                percentage=75.0,
                violations=["func1", "func2", "func3", "func4", "func5"],
            ),
        ],
    )


@pytest.fixture
def sample_complexity_result() -> models.ComplexityQualityResult:
    """Sample complexity result for testing."""
    return models.ComplexityQualityResult(
        rule="param-complexity",
        threshold=5,
        total_violations=3,
        by_file=[
            models.FileViolations(
                path="src/example/handlers.py",
                violations=[
                    models.ViolationDetail(
                        function="handle_request",
                        line=42,
                        param_count=7,
                    ),
                    models.ViolationDetail(
                        function="process_data",
                        line=89,
                        param_count=6,
                    ),
                ],
            ),
            models.FileViolations(
                path="src/example/validators.py",
                violations=[
                    models.ViolationDetail(
                        function="validate_input",
                        line=15,
                        param_count=8,
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def sample_passing_complexity_result() -> models.ComplexityQualityResult:
    """Sample passing complexity result (no violations)."""
    return models.ComplexityQualityResult(
        rule="param-complexity",
        threshold=5,
        total_violations=0,
        by_file=[],
    )


class TestConsoleFormatter:
    """Tests for ConsoleFormatter."""

    def test_format_single_passing_coverage_result(
        self, sample_coverage_result: models.CoverageQualityResult
    ) -> None:
        """Test formatting a single passing coverage result shows details."""
        formatter = formatters.ConsoleFormatter()
        output = formatter.format_results([sample_coverage_result])

        # Check for check mark and title
        assert "✓" in output
        assert "Type Coverage" in output
        # ANSI codes may split "85.5" so check for parts
        assert "85" in output
        assert "threshold" in output
        assert "80" in output

        # Should show file breakdown for single result
        assert "By File:" in output
        assert "src/example/module.py" in output
        assert "src/example/utils.py" in output
        assert "9" in output and "10" in output
        assert "8" in output

        # Should show overall summary
        assert "17" in output and "20" in output
        assert "functions meet the standard" in output

    def test_format_single_failing_coverage_result(
        self, sample_failing_coverage_result: models.CoverageQualityResult
    ) -> None:
        """Test formatting a single failing coverage result shows violations."""
        formatter = formatters.ConsoleFormatter()
        output = formatter.format_results([sample_failing_coverage_result])

        # Check for X mark and title
        assert "✗" in output
        assert "Docstring Coverage" in output
        assert "75.0" in output or "75" in output
        assert "threshold" in output
        assert "90" in output

        # Should show violations
        assert "Missing coverage:" in output
        assert "src/example/api.py:func1" in output
        assert "src/example/api.py:func2" in output

    def test_format_single_complexity_result(
        self, sample_complexity_result: models.ComplexityQualityResult
    ) -> None:
        """Test formatting a single complexity result shows violations."""
        formatter = formatters.ConsoleFormatter()
        output = formatter.format_results([sample_complexity_result])

        # Check for X mark (has violations)
        assert "✗" in output
        assert "Parameter Complexity" in output or "Param Complexity" in output
        assert "3" in output and "violations" in output
        assert "max" in output and "5" in output and "parameters" in output

        # Should show violation details for single result
        assert "Functions exceeding threshold:" in output
        assert "src/example/handlers.py" in output
        assert "handle_request" in output and "42" in output and "7" in output
        assert "process_data" in output and "89" in output and "6" in output
        assert "src/example/validators.py" in output
        assert "validate_input" in output and "15" in output and "8" in output

    def test_format_single_passing_complexity_result(
        self, sample_passing_complexity_result: models.ComplexityQualityResult
    ) -> None:
        """Test formatting a passing complexity result (no violations)."""
        formatter = formatters.ConsoleFormatter()
        output = formatter.format_results([sample_passing_complexity_result])

        # Check for check mark
        assert "✓" in output
        assert "Parameter Complexity" in output or "Param Complexity" in output
        assert "No violations" in output
        assert "max" in output and "5" in output and "parameters" in output

    def test_format_multiple_results_summary(
        self,
        sample_coverage_result: models.CoverageQualityResult,
        sample_complexity_result: models.ComplexityQualityResult,
    ) -> None:
        """Test formatting multiple results shows summary without details."""
        formatter = formatters.ConsoleFormatter()
        output = formatter.format_results([sample_coverage_result, sample_complexity_result])

        # Should show header
        assert "Running quality checks" in output

        # Should show both results
        assert "Type Coverage" in output
        assert "Parameter Complexity" in output or "Param Complexity" in output

        # Should NOT show detailed breakdown for multiple results
        assert "By File:" not in output
        assert "Functions exceeding threshold:" not in output

        # Should show overall summary
        assert "1" in output and "2" in output and "checks failed" in output

    def test_format_multiple_results_all_passing(
        self,
        sample_coverage_result: models.CoverageQualityResult,
        sample_passing_complexity_result: models.ComplexityQualityResult,
    ) -> None:
        """Test formatting multiple passing results shows success."""
        formatter = formatters.ConsoleFormatter()
        output = formatter.format_results(
            [sample_coverage_result, sample_passing_complexity_result]
        )

        # Should show overall success
        assert "All" in output and "2" in output and "checks passed" in output

    def test_format_empty_results(self) -> None:
        """Test formatting empty results list returns empty string."""
        formatter = formatters.ConsoleFormatter()
        output = formatter.format_results([])

        assert output == ""


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_coverage_result(
        self, sample_coverage_result: models.CoverageQualityResult
    ) -> None:
        """Test JSON formatting of coverage result."""
        formatter = formatters.JSONFormatter()
        output = formatter.format_results([sample_coverage_result])

        data = json.loads(output)
        assert len(data) == 1

        result = data[0]
        assert result["rule"] == "type-coverage"
        assert result["status"] == "pass"
        assert result["threshold"] == 80
        assert result["actual"] == 85.5

        # Check overall section
        assert result["overall"]["total"] == 20
        assert result["overall"]["compliant"] == 17
        assert result["overall"]["percentage"] == 85.5

        # Check by_file section
        assert len(result["by_file"]) == 2
        assert result["by_file"][0]["path"] == "src/example/module.py"
        assert result["by_file"][0]["total"] == 10
        assert result["by_file"][0]["compliant"] == 9
        assert result["by_file"][0]["percentage"] == 90.0
        assert result["by_file"][0]["violations"] == ["uncovered_func"]

    def test_format_complexity_result(
        self, sample_complexity_result: models.ComplexityQualityResult
    ) -> None:
        """Test JSON formatting of complexity result."""
        formatter = formatters.JSONFormatter()
        output = formatter.format_results([sample_complexity_result])

        data = json.loads(output)
        assert len(data) == 1

        result = data[0]
        assert result["rule"] == "param-complexity"
        assert result["status"] == "fail"
        assert result["threshold"] == 5
        assert result["total_violations"] == 3

        # Check by_file section
        assert len(result["by_file"]) == 2
        assert result["by_file"][0]["path"] == "src/example/handlers.py"
        assert len(result["by_file"][0]["violations"]) == 2

        violation = result["by_file"][0]["violations"][0]
        assert violation["function"] == "handle_request"
        assert violation["line"] == 42
        assert violation["param_count"] == 7

    def test_format_multiple_results(
        self,
        sample_coverage_result: models.CoverageQualityResult,
        sample_complexity_result: models.ComplexityQualityResult,
    ) -> None:
        """Test JSON formatting of multiple results."""
        formatter = formatters.JSONFormatter()
        output = formatter.format_results([sample_coverage_result, sample_complexity_result])

        data = json.loads(output)
        assert len(data) == 2
        assert data[0]["rule"] == "type-coverage"
        assert data[1]["rule"] == "param-complexity"

    def test_json_is_valid_and_indented(
        self, sample_coverage_result: models.CoverageQualityResult
    ) -> None:
        """Test JSON output is valid and properly indented."""
        formatter = formatters.JSONFormatter()
        output = formatter.format_results([sample_coverage_result])

        # Should be valid JSON
        data = json.loads(output)
        assert data is not None

        # Should be indented (contains newlines)
        assert "\n" in output
        assert "  " in output


class TestCSVFormatter:
    """Tests for CSVFormatter."""

    def test_format_coverage_result(
        self, sample_coverage_result: models.CoverageQualityResult
    ) -> None:
        """Test CSV formatting of coverage result."""
        formatter = formatters.CSVFormatter()
        output = formatter.format_results([sample_coverage_result])

        lines = output.strip().splitlines()

        # Check header
        assert (
            lines[0]
            == "rule,file_path,total_functions,compliant_functions,compliance_percentage,status"
        )

        # Check data rows (one per file)
        assert len(lines) == 3  # Header + 2 files

        # First file (90% >= 80% = pass)
        assert "type-coverage,src/example/module.py,10,9,90.0,pass" in lines[1]

        # Second file (80% >= 80% = pass)
        assert "type-coverage,src/example/utils.py,10,8,80.0,pass" in lines[2]

    def test_format_failing_coverage_result(
        self, sample_failing_coverage_result: models.CoverageQualityResult
    ) -> None:
        """Test CSV formatting of failing coverage result."""
        formatter = formatters.CSVFormatter()
        output = formatter.format_results([sample_failing_coverage_result])

        lines = output.strip().splitlines()

        # File (75% < 90% = fail)
        assert "docstring-coverage,src/example/api.py,20,15,75.0,fail" in lines[1]

    def test_format_complexity_result(
        self, sample_complexity_result: models.ComplexityQualityResult
    ) -> None:
        """Test CSV formatting of complexity result."""
        formatter = formatters.CSVFormatter()
        output = formatter.format_results([sample_complexity_result])

        lines = output.strip().splitlines()

        # Check header
        assert lines[0] == "rule,file_path,function_name,line_number,parameter_count,status"

        # Check data rows (one per violation)
        assert len(lines) == 4  # Header + 3 violations

        assert "param-complexity,src/example/handlers.py,handle_request,42,7,fail" in lines[1]
        assert "param-complexity,src/example/handlers.py,process_data,89,6,fail" in lines[2]
        assert "param-complexity,src/example/validators.py,validate_input,15,8,fail" in lines[3]

    def test_format_multiple_results_separate_headers(
        self,
        sample_coverage_result: models.CoverageQualityResult,
        sample_complexity_result: models.ComplexityQualityResult,
    ) -> None:
        """Test CSV formatting with both coverage and complexity results."""
        formatter = formatters.CSVFormatter()
        output = formatter.format_results([sample_coverage_result, sample_complexity_result])

        lines = output.strip().splitlines()

        # Should have both headers (coverage first, complexity second)
        coverage_header = (
            "rule,file_path,total_functions,compliant_functions,compliance_percentage,status"
        )
        complexity_header = "rule,file_path,function_name,line_number,parameter_count,status"

        # Find header positions
        coverage_header_idx = None
        complexity_header_idx = None
        for i, line in enumerate(lines):
            if line == coverage_header:
                coverage_header_idx = i
            elif line == complexity_header:
                complexity_header_idx = i

        assert coverage_header_idx is not None
        assert complexity_header_idx is not None

        # Coverage header should come first
        assert coverage_header_idx < complexity_header_idx

        # Should have coverage data rows after coverage header
        assert "type-coverage,src/example/module.py" in lines[coverage_header_idx + 1]

        # Should have complexity data rows after complexity header
        assert (
            "param-complexity,src/example/handlers.py,handle_request"
            in lines[complexity_header_idx + 1]
        )

    def test_format_passing_complexity_result_no_rows(
        self, sample_passing_complexity_result: models.ComplexityQualityResult
    ) -> None:
        """Test CSV formatting of passing complexity result produces header only."""
        formatter = formatters.CSVFormatter()
        output = formatter.format_results([sample_passing_complexity_result])

        lines = output.strip().split("\n")

        # Should only have header (no violations to report)
        assert len(lines) == 1
        assert lines[0] == "rule,file_path,function_name,line_number,parameter_count,status"


class TestGetFormatter:
    """Tests for get_formatter() function."""

    def test_get_console_formatter(self) -> None:
        """Test get_formatter returns ConsoleFormatter for CONSOLE format."""
        formatter = formatters.get_formatter(formatters.OutputFormat.CONSOLE)
        assert isinstance(formatter, formatters.ConsoleFormatter)

    def test_get_json_formatter(self) -> None:
        """Test get_formatter returns JSONFormatter for JSON format."""
        formatter = formatters.get_formatter(formatters.OutputFormat.JSON)
        assert isinstance(formatter, formatters.JSONFormatter)

    def test_get_csv_formatter(self) -> None:
        """Test get_formatter returns CSVFormatter for CSV format."""
        formatter = formatters.get_formatter(formatters.OutputFormat.CSV)
        assert isinstance(formatter, formatters.CSVFormatter)

    def test_formatter_implements_protocol(self) -> None:
        """Test all formatters implement FormatsQualityResults protocol."""
        for format_type in formatters.OutputFormat:
            formatter = formatters.get_formatter(format_type)
            assert hasattr(formatter, "format_results")
            assert callable(formatter.format_results)


class TestOutputFormatEnum:
    """Tests for OutputFormat enum."""

    def test_enum_values(self) -> None:
        """Test OutputFormat enum has correct values."""
        assert formatters.OutputFormat.CONSOLE.value == "console"
        assert formatters.OutputFormat.JSON.value == "json"
        assert formatters.OutputFormat.CSV.value == "csv"

    def test_string_comparison(self) -> None:
        """Test OutputFormat enum supports string comparison."""
        assert formatters.OutputFormat.CONSOLE == "console"
        assert formatters.OutputFormat.JSON == "json"
        assert formatters.OutputFormat.CSV == "csv"

    def test_string_formatting(self) -> None:
        """Test OutputFormat enum supports .value for string formatting."""
        format_type = formatters.OutputFormat.JSON
        # String mixin allows direct comparison with strings
        assert format_type == "json"
        # Use .value for f-string formatting (mypy has false positive with str enums)
        assert f"Format: {format_type.value}" == "Format: json"  # type: ignore[attr-defined]
