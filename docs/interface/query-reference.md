# Query Reference

Complete reference for Mapper's built-in risk detection queries.

## Overview

Mapper provides built-in queries that identify code risks and opportunities. These queries:
- Require no knowledge of Neo4j or Cypher
- Return actionable results with severity levels
- Can be automated in CI/CD pipelines
- Export to multiple formats (table, JSON, CSV)

## Query Categories

### Risk Detection
Queries that identify code quality issues and technical debt.

### Critical Components
Queries that identify high-impact or high-dependency code elements.

### Architecture
Queries that analyze architectural patterns and coupling.

---

## Query Details

### find-dead-code

**Category**: Risk Detection  
**Severity**: Dynamic (based on visibility)

**What it detects**:
Functions and classes with no incoming CALLS relationships - code that appears unused in the codebase.

**Use case**:
- Identify code candidates for removal
- Reduce codebase size and maintenance burden
- Find forgotten experimental code
- Detect after refactoring orphans

**Interpretation**:
- **High severity** (Public APIs): Unused public functions/classes - verify before removing, may have external users
- **Medium severity** (Private code): Unused private functions/classes - safer to remove immediately
- **Exclude patterns**: `__init__`, `main`, `test_*` functions are filtered out as they may be entry points

**Example results**:
```
Summary: Found 12 unused items (8 functions, 4 classes)
  High severity: 8 items (public APIs)
  Medium severity: 4 items (private utilities)

┌──────────┬────────────────────────────────┬──────────┬──────────┐
│ Severity │ FQN                            │ Type     │ Public   │
├──────────┼────────────────────────────────┼──────────┼──────────┤
│ High     │ myapp.handlers.legacy_handler  │ Function │ Yes      │
│ High     │ myapp.utils.deprecated_helper  │ Function │ Yes      │
│ Medium   │ myapp.internal._unused_helper  │ Function │ No       │
└──────────┴────────────────────────────────┴──────────┴──────────┘
```

**Actions to take**:
1. **Public code**: Deprecate first, then remove in next major version
2. **Private code**: Safe to remove immediately after team review
3. **Verify with tests**: Ensure no indirect usage (e.g., via `getattr`, imports not tracked)
4. **Document decisions**: Add reason to commit message when removing

**Cypher equivalent**:
```cypher
MATCH (f {package: $package})
WHERE (f:Function OR f:Method OR f:Class)
  AND NOT ()-[:CALLS]->(f)
  AND f.name NOT IN ['main', '__init__', '__main__']
  AND NOT f.name STARTS WITH 'test_'
RETURN f.fqn, f.is_public, labels(f)[0] as type
ORDER BY f.is_public DESC, f.fqn
```

---

### analyze-module-centrality

**Category**: Critical Components  
**Severity**: Dynamic (based on dependent count)

**What it detects**:
Modules with many incoming DEPENDS_ON relationships - modules that many other modules depend on.

**Use case**:
- Identify critical modules that affect many parts of the codebase
- Prioritize test coverage and code review for high-impact modules
- Find single points of failure
- Guide architectural decisions (consider breaking up highly central modules)

**Interpretation**:
- **Critical (>10 dependents)**: Changes here have very high blast radius - requires careful review
- **High (6-10 dependents)**: Significant impact - needs thorough testing
- **Medium (3-5 dependents)**: Moderate impact - standard review process

**Example results**:
```
Summary: Found 45 modules, showing most critical
  Critical (>10 dependents): 3 modules
  High (6-10 dependents): 8 modules
  Medium (3-5 dependents): 12 modules

┌──────────┬────────────────┬─────────────┬──────────────────────────┐
│ Severity │ Module         │ Dependents  │ Risk                     │
├──────────┼────────────────┼─────────────┼──────────────────────────┤
│ Critical │ myapp.core     │ 15          │ Single point of failure  │
│ Critical │ myapp.database │ 12          │ High blast radius        │
│ High     │ myapp.models   │ 9           │ Data layer dependency    │
└──────────┴────────────────┴─────────────┴──────────────────────────┘
```

**Actions to take**:
1. **Add comprehensive tests**: Ensure high coverage for critical modules
2. **Implement monitoring**: Track errors/performance for these modules in production
3. **Document public APIs**: Clear documentation reduces breaking changes
4. **Consider refactoring**: Break large critical modules into smaller, focused modules
5. **Review process**: Require multiple reviewers for changes to critical modules

**Cypher equivalent**:
```cypher
MATCH (m:Module {package: $package})<-[:DEPENDS_ON]-(dependent:Module)
WITH m, count(dependent) as dependent_count
WHERE dependent_count >= 3
RETURN m.name, dependent_count
ORDER BY dependent_count DESC
```

---

### find-critical-functions

**Category**: Critical Components  
**Severity**: Dynamic (based on caller count)

**What it detects**:
Functions and methods with many incoming CALLS relationships - code that is called from many places.

**Use case**:
- Identify high-impact functions where bugs affect many features
- Prioritize test coverage for frequently called code
- Find potential bottlenecks
- Guide optimization efforts (optimize critical functions first)

**Interpretation**:
- **Critical (>20 callers)**: Changes here ripple across entire codebase - extensive testing required
- **High (10-20 callers)**: Significant usage - thorough testing needed
- **Medium (5-9 callers)**: Moderate usage - standard testing

**Example results**:
```
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
└──────────┴────────────────────────────────┴─────────┴──────────────────────────┘
```

**Actions to take**:
1. **Ensure test coverage**: Critical functions need comprehensive unit and integration tests
2. **Add monitoring**: Track performance and errors for these functions
3. **Consider interfaces**: Extract protocol/interface if many callers need different implementations
4. **Performance optimization**: Profile and optimize critical functions
5. **Backward compatibility**: Maintain stability guarantees (semantic versioning)
6. **Add logging**: Detailed logging helps debug issues across many call sites

**Cypher equivalent**:
```cypher
MATCH (f {package: $package})<-[:CALLS]-(caller)
WHERE f:Function OR f:Method
WITH f, count(caller) as caller_count
WHERE caller_count >= 5
RETURN f.fqn, caller_count
ORDER BY caller_count DESC
```

---

## Coming in v0.7.1

### analyze-call-complexity

**Category**: Risk Detection  
**What it detects**: Functions with deep call chains (high transitive call depth)  
**Use case**: Find functions that are difficult to understand and debug due to many layers of calls

### detect-circular-dependencies

**Category**: Risk Detection  
**What it detects**: Modules with circular DEPENDS_ON relationships (import cycles)  
**Use case**: Find architectural issues that can cause import errors and tight coupling

---

## Coming in v0.7.2

### detect-module-clusters

**Category**: Architecture  
**What it detects**: Groups of tightly coupled modules (high internal connectivity, low external connectivity)  
**Use case**: Understand architectural boundaries and opportunities for service extraction

### identify-connector-modules

**Category**: Architecture  
**What it detects**: Modules with high betweenness centrality (bridge different parts of the codebase)  
**Use case**: Find architectural bottlenecks and critical integration points

---

## Interpreting Severity Levels

Severity levels are calculated dynamically based on query-specific thresholds:

### Critical
- Immediate attention required
- High risk of widespread impact
- Should be addressed in current sprint
- Examples: >20 callers, >10 dependents, public unused API

### High
- Should be addressed soon
- Significant but manageable risk
- Plan for next sprint
- Examples: 10-20 callers, 6-10 dependents

### Medium
- Monitor and address when convenient
- Moderate risk
- Can be addressed during regular maintenance
- Examples: 5-9 callers, 3-5 dependents

### Low
- Informational
- Minimal risk
- Address during refactoring opportunities
- Examples: <5 callers/dependents, private unused utilities

---

## Export Formats

### Table (default)
Human-readable formatted output with:
- Summary statistics
- Severity-based sorting
- Limited to top N results (default 10)
- Best for: Terminal viewing, quick triage

### JSON
Complete machine-readable output with:
- All results (no limit)
- Full metadata
- Structured data
- Best for: CI/CD integration, automation, further processing

Example:
```json
{
  "query": "find-dead-code",
  "package": "myapp",
  "summary": {
    "total": 12,
    "by_severity": {
      "High": 8,
      "Medium": 4
    }
  },
  "results": [
    {
      "severity": "High",
      "fqn": "myapp.handlers.legacy_handler",
      "type": "Function",
      "is_public": true
    }
  ]
}
```

### CSV
Spreadsheet-compatible output with:
- Column headers
- One row per result
- All result fields
- Best for: Reporting, spreadsheet analysis, management visibility

---

## Using Queries in CI/CD

Example GitHub Actions workflow:

```yaml
name: Code Risk Detection

on: [push, pull_request]

jobs:
  detect-risks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Mapper
        run: |
          pip install mapper
          mapper init
      
      - name: Analyze code
        run: mapper analyse start . --package myapp
      
      - name: Check for critical issues
        run: |
          # Export results to JSON
          mapper query run find-dead-code --package myapp --json > dead-code.json
          mapper query run find-critical-functions --package myapp --json > critical.json
          
          # Fail if critical severity items found
          DEAD_CODE_CRITICAL=$(jq '[.results[] | select(.severity == "Critical")] | length' dead-code.json)
          
          if [ $DEAD_CODE_CRITICAL -gt 0 ]; then
            echo "ERROR: Found $DEAD_CODE_CRITICAL critical dead code items"
            exit 1
          fi
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: risk-reports
          path: |
            dead-code.json
            critical.json
```

---

## Related Documentation

- [User Journey: Detecting Code Risks](../user-journeys/08-detecting-code-risks.md) - Step-by-step guide
- [CLI Reference](cli.md) - Complete CLI command reference
- [Neo4j Schema](../technical/neo4j-schema.md) - Graph database schema

---

**Last Updated**: 2026-04-01
