# User Journey: Detecting Code Risks with CLI Queries

**User Goal**: Quickly identify code risks and opportunities (critical dependencies, dead code, complexity issues) without needing to understand the underlying graph database or Cypher query language.

**Prerequisites**:
- Code already analyzed and stored in Neo4j (see [Analyzing a Codebase](03-analyzing-codebase.md))
- Mapper CLI installed and configured

**Estimated Time**: 5-10 minutes

---

## Overview

Mapper provides built-in queries that detect common code risks and opportunities. These queries run from the CLI and provide actionable reports with severity levels and summary statistics.

**Two-tier analysis workflow**:
- **Tier 1 (This guide)**: Run CLI queries to detect issues - fast, automatable, high-level
- **Tier 2 (Advanced)**: Investigate flagged issues with custom queries in Neo4j Browser (see [Analyzing and Querying Code](05-analyzing-querying-code.md))

---

## Step 1: Discover Available Queries

List all available risk detection queries:

```bash
mapper query list
```

**Example output**:
```
Available queries (7 total)

Risk Detection
  find-dead-code              Find unused functions and classes
  detect-circular-dependencies Find module import cycles
  analyze-call-complexity     Find functions with deep call chains

Critical Components
  analyze-module-centrality   Find most depended-on modules
  find-critical-functions     Find most-called functions
  identify-connector-modules  Find modules that bridge different parts

Architecture
  detect-module-clusters      Find tightly coupled module groups

Use 'mapper query list --group <name>' to filter by group
Use 'mapper query run <name> --package <pkg>' to execute
```

Filter by category:

```bash
mapper query list --group risk
```

---

## Step 2: Run Your First Query

Run a query to find dead code:

```bash
mapper query run find-dead-code --package myapp
```

**Example output**:
```
Dead Code Analysis
Package: myapp

Summary: Found 12 unused items (8 functions, 4 classes)
  High severity: 8 items (public APIs)
  Medium severity: 4 items (private utilities)

┌──────────┬────────────────────────────────┬──────────┬──────────┐
│ Severity │ FQN                            │ Type     │ Public   │
├──────────┼────────────────────────────────┼──────────┼──────────┤
│ High     │ myapp.handlers.legacy_handler  │ Function │ Yes      │
│ High     │ myapp.utils.deprecated_helper  │ Function │ Yes      │
│ High     │ myapp.models.OldDataClass      │ Class    │ Yes      │
│ Medium   │ myapp.internal._unused_helper  │ Function │ No       │
│ Medium   │ myapp.internal._old_validator  │ Function │ No       │
│ ...      │ ...                            │ ...      │ ...      │
└──────────┴────────────────────────────────┴──────────┴──────────┘

Showing top 10 of 12 results (use --limit to adjust)
```

---

## Step 3: Identify Critical Dependencies

Find modules that are depended on most heavily:

```bash
mapper query run analyze-module-centrality --package myapp
```

**Example output**:
```
Module Centrality Analysis
Package: myapp

Summary: Found 45 modules, showing most critical
  Critical (>10 dependents): 3 modules
  High (6-10 dependents): 8 modules
  Medium (3-5 dependents): 12 modules

┌──────────┬────────────────┬─────────────┬──────────────────────────┐
│ Severity │ Module         │ Dependents  │ Risk                     │
├──────────┼────────────────┼─────────────┼──────────────────────────┤
│ Critical │ myapp.core     │ 15          │ Single point of failure  │
│ Critical │ myapp.database │ 12          │ High blast radius        │
│ Critical │ myapp.auth     │ 11          │ Security-critical        │
│ High     │ myapp.models   │ 9           │ Data layer dependency    │
│ High     │ myapp.utils    │ 8           │ Utility overuse          │
│ ...      │ ...            │ ...         │ ...                      │
└──────────┴────────────────┴─────────────┴──────────────────────────┘

Showing top 10 of 45 modules (use --limit to adjust)
```

**Interpretation**:
- **Critical modules**: Changes here affect many parts of the codebase - requires careful review
- **High blast radius**: Consider breaking into smaller, focused modules
- **Single point of failure**: If this module breaks, many features fail

---

## Step 4: Find High-Impact Functions

Identify functions that are called most frequently:

```bash
mapper query run find-critical-functions --package myapp
```

**Example output**:
```
Critical Functions Analysis
Package: myapp

Summary: Found 234 functions, showing most critical
  Critical (>20 callers): 2 functions
  High (10-20 callers): 7 functions
  Medium (5-9 callers): 18 functions

┌──────────┬────────────────────────────────┬─────────┬──────────────────────────┐
│ Severity │ Function                       │ Callers │ Risk                     │
├──────────┼────────────────────────────────┼─────────┼──────────────────────────┤
│ Critical │ myapp.database.execute_query   │ 28      │ Database bottleneck      │
│ Critical │ myapp.auth.verify_token        │ 23      │ Auth single point        │
│ High     │ myapp.utils.serialize_data     │ 15      │ High coupling            │
│ High     │ myapp.core.process_request     │ 14      │ Core dependency          │
│ High     │ myapp.validation.check_input   │ 12      │ Validation chokepoint    │
│ ...      │ ...                            │ ...     │ ...                      │
└──────────┴────────────────────────────────┴─────────┴──────────────────────────┘

Showing top 10 of 234 functions (use --limit to adjust)
```

**Interpretation**:
- **Critical functions**: Changes require extensive testing across many call sites
- **High coupling**: Consider extracting interface or protocol for flexibility
- **Bottlenecks**: Performance issues here affect many features

---

## Step 5: Customize Output

### Control result count

Show more or fewer results:

```bash
mapper query run find-dead-code --package myapp --limit 25
```

### Export to JSON

For automation or further processing:

```bash
mapper query run analyze-module-centrality --package myapp --json > risks.json
```

### Export to CSV

For spreadsheets or reporting:

```bash
mapper query run find-critical-functions --package myapp --csv > critical-functions.csv
```

### Use explicit format flag

```bash
mapper query run find-dead-code --package myapp --format table
mapper query run find-dead-code --package myapp --format json
mapper query run find-dead-code --package myapp --format csv
```

---

## Step 6: Interpret Results and Take Action

### Dead Code (find-dead-code)

**What it means**: Functions/classes with no incoming calls
**Actions**:
- High severity (public): Remove after deprecation period
- Medium severity (private): Safe to remove immediately
- Verify with team before removing public APIs

### Module Centrality (analyze-module-centrality)

**What it means**: Modules with many dependents
**Actions**:
- Critical: Add comprehensive tests, careful review process
- Consider breaking into smaller modules
- Document public APIs thoroughly
- Monitor for changes

### Critical Functions (find-critical-functions)

**What it means**: Functions called from many places
**Actions**:
- Critical: Ensure thorough test coverage
- Consider stability guarantees (semantic versioning)
- Add logging/monitoring
- Extract interface if many callers need different implementations

---

## Advanced: Integrate with CI/CD

Run queries automatically in CI to detect new risks:

```bash
#!/bin/bash
# Check for new dead code
mapper analyse start . --package myapp
mapper query run find-dead-code --package myapp --json > dead-code.json

# Fail if critical issues found
CRITICAL_COUNT=$(jq '[.results[] | select(.severity == "Critical")] | length' dead-code.json)
if [ $CRITICAL_COUNT -gt 0 ]; then
  echo "ERROR: Found $CRITICAL_COUNT critical dead code items"
  exit 1
fi
```

---

## Outcomes

After this journey, you can:
- ✅ Run CLI queries to detect code risks without Neo4j knowledge
- ✅ Identify critical dependencies and high-impact functions
- ✅ Find dead code and complexity issues
- ✅ Export results for reporting or automation
- ✅ Integrate risk detection into CI/CD pipelines

---

## Troubleshooting

### "Package not found" error

**Problem**: The specified package hasn't been analyzed yet

**Solution**:
```bash
# Verify analyzed packages
mapper status

# Analyze your package
mapper analyse start /path/to/code --package myapp
```

### Query returns no results

**Problem**: No risks detected for this query

**Solution**: This is good news! Your codebase passes this check. Try other queries to get broader coverage.

### "No Neo4j connection" error

**Problem**: Cannot connect to Neo4j database

**Solution**:
```bash
# Check status
mapper status

# Verify Neo4j is running
docker ps | grep neo4j

# Start Neo4j if needed
docker start mapper-neo4j
```

---

## Next Steps

### When issues are found:
1. **For simple cases**: Take action directly (remove dead code, add tests)
2. **For complex issues**: Investigate with Neo4j Browser (see [Analyzing and Querying Code](05-analyzing-querying-code.md))
3. **For architectural concerns**: Discuss with team and plan refactoring

### Run additional queries:
- **v0.7.1** (coming soon): Call complexity analysis, circular dependency detection
- **v0.7.2** (coming soon): Module clustering, architectural bottleneck detection

### Automate:
- Add query checks to pre-commit hooks
- Run in CI/CD to catch issues early
- Track metrics over time to measure code health improvements

---

**Related Documentation**:
- [Analyzing a Codebase](03-analyzing-codebase.md) - How to analyze code before running queries
- [Analyzing and Querying Code](05-analyzing-querying-code.md) - Deep dive investigation with Neo4j Browser
- [Checking System Status](07-checking-status.md) - Verify Mapper and Neo4j are working
