# Interface: Structured Parameter and Decorator Storage

**Version**: 0.8.0  
**Status**: Design Phase

---

## Overview

This document defines the interface for structured parameter and decorator storage. Starting in v0.8.0, parameters and decorators are stored as structured data (attrs models) instead of serialized strings.

**Benefits**:
- Enables precise Cypher queries on parameter/decorator metadata
- Type-safe data structures with validation
- Queryable without string parsing

---

## Data Models

### ParameterKind

**Purpose**: Enum representing different parameter types in Python function signatures.

**Definition**:
```python
from enum import Enum

class ParameterKind(str, Enum):
    """Parameter kind classification.
    
    This enum matches Python's inspect.Parameter.kind values, using the same
    names and semantics. See Python's inspect module documentation for details:
    https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind
    
    Values:
        POSITIONAL_ONLY: Parameters before / in signature (e.g., def f(a, b, /))
        POSITIONAL_OR_KEYWORD: Normal parameters that can be passed by position or keyword
        VAR_POSITIONAL: *args - captures arbitrary positional arguments
        KEYWORD_ONLY: Parameters after * or *args that must be passed by keyword
        VAR_KEYWORD: **kwargs - captures arbitrary keyword arguments
    """
    
    POSITIONAL_ONLY = "POSITIONAL_ONLY"
    POSITIONAL_OR_KEYWORD = "POSITIONAL_OR_KEYWORD"
    VAR_POSITIONAL = "VAR_POSITIONAL"
    KEYWORD_ONLY = "KEYWORD_ONLY"
    VAR_KEYWORD = "VAR_KEYWORD"
```

**Usage Examples**:
```python
# Normal parameters - POSITIONAL_OR_KEYWORD
def create_user(user_id, name, email):
    pass

# Positional-only (before /) - POSITIONAL_ONLY
def pow(x, y, /, mod=None):
    pass

# With *args - VAR_POSITIONAL
def print(*values, sep=' '):
    pass

# Keyword-only (after *) - KEYWORD_ONLY
def create_user(user_id, *, admin=False, verified=False):
    pass

# With **kwargs - VAR_KEYWORD
def configure(**options):
    pass
```

---

### ParameterInfo

**Purpose**: Represents a single function/method parameter with full metadata.

**Definition**:
```python
import attrs

@attrs.define(frozen=True)
class ParameterInfo:
    """Information about a function parameter.
    
    Attributes:
        name: Parameter name (e.g., "user_id", "args", "kwargs")
        type_hint: Type annotation string (e.g., "int", "str | None"), None if no annotation
        has_type_hint: Whether parameter has a type annotation
        default: String representation of default value, None if no default
        position: Zero-indexed position in parameter list
        kind: Parameter kind (matches Python's inspect.Parameter.kind)
    """
    
    name: str
    type_hint: str | None
    has_type_hint: bool
    default: str | None
    position: int
    kind: ParameterKind
```

**Validation**:
- `name` must not be empty
- `position` must be >= 0
- `has_type_hint` must match `type_hint is not None`
- `default` must be None when `kind` is VAR_POSITIONAL or VAR_KEYWORD (*args/**kwargs cannot have defaults)
- For `kind` == VAR_POSITIONAL: `name` typically "args" (without * prefix)
- For `kind` == VAR_KEYWORD: `name` typically "kwargs" (without ** prefix)

**Example Instances**:
```python
# Normal typed parameter with no default
ParameterInfo(
    name="user_id",
    type_hint="int",
    has_type_hint=True,
    default=None,
    position=0,
    kind=ParameterKind.POSITIONAL_OR_KEYWORD
)

# Untyped parameter with default
ParameterInfo(
    name="name",
    type_hint=None,
    has_type_hint=False,
    default="'Unknown'",
    position=1,
    kind=ParameterKind.POSITIONAL_OR_KEYWORD
)

# *args parameter
ParameterInfo(
    name="args",
    type_hint=None,
    has_type_hint=False,
    default=None,
    position=2,
    kind=ParameterKind.VAR_POSITIONAL
)

# Keyword-only parameter
ParameterInfo(
    name="admin",
    type_hint="bool",
    has_type_hint=True,
    default="False",
    position=3,
    kind=ParameterKind.KEYWORD_ONLY
)

# **kwargs parameter
ParameterInfo(
    name="kwargs",
    type_hint=None,
    has_type_hint=False,
    default=None,
    position=4,
    kind=ParameterKind.VAR_KEYWORD
)
```

---

### DecoratorInfo

**Purpose**: Represents a decorator applied to a function/method/class.

**Definition**:
```python
@attrs.define(frozen=True)
class DecoratorInfo:
    """Information about a decorator.
    
    Attributes:
        name: Decorator name without @ symbol (e.g., "property", "rate_limit")
        args: Argument string including parentheses (e.g., "(10, timeout=5)"), None if no args
        full_text: Complete decorator text as it appears in source (e.g., "@rate_limit(10)")
    """
    
    name: str
    args: str | None
    full_text: str
```

**Validation**:
- `name` must not be empty
- `full_text` must start with '@'
- If `args` is present, `full_text` should contain it

**Example Instances**:
```python
# Simple decorator with no arguments
DecoratorInfo(
    name="property",
    args=None,
    full_text="@property"
)

# Decorator with arguments
DecoratorInfo(
    name="rate_limit",
    args="(10, timeout=5)",
    full_text="@rate_limit(10, timeout=5)"
)

# Decorator with attribute access
DecoratorInfo(
    name="app.route",
    args="('/users')",
    full_text="@app.route('/users')"
)
```

---

## Usage in Extractor

### Current (v0.7.x)

```python
# Old: String serialization
func_info = FunctionInfo(
    name="create_user",
    parameters="['user_id: int', 'name', 'email: str = None']",
    decorators="['@require_auth', '@rate_limit(10)']",
    # ... other fields
)
```

### New (v0.8.0+)

```python
# New: Structured attrs models
func_info = FunctionInfo(
    name="create_user",
    parameters=[
        ParameterInfo(
            name="user_id",
            type_hint="int",
            has_type_hint=True,
            default=None,
            position=0,
            kind=ParameterKind.POSITIONAL_OR_KEYWORD
        ),
        ParameterInfo(
            name="name",
            type_hint=None,
            has_type_hint=False,
            default=None,
            position=1,
            kind=ParameterKind.POSITIONAL_OR_KEYWORD
        ),
        ParameterInfo(
            name="email",
            type_hint="str",
            has_type_hint=True,
            default="None",
            position=2,
            kind=ParameterKind.POSITIONAL_OR_KEYWORD
        )
    ],
    decorators=[
        DecoratorInfo(
            name="require_auth",
            args=None,
            full_text="@require_auth"
        ),
        DecoratorInfo(
            name="rate_limit",
            args="(10)",
            full_text="@rate_limit(10)"
        )
    ],
    # ... other fields
)
```

---

## Neo4j Storage Schema

### Parameters Storage

**Location**: Stored as property array on Function/Method nodes.

**Format**: Array of maps (Neo4j native type)

**Example**:
```cypher
(:Function {
    name: "create_user",
    fqn: "myapp.users.create_user",
    parameters: [
        {
            name: "user_id",
            type_hint: "int",
            has_type_hint: true,
            default: null,
            position: 0,
            kind: "POSITIONAL_OR_KEYWORD"
        },
        {
            name: "name",
            type_hint: null,
            has_type_hint: false,
            default: null,
            position: 1,
            kind: "POSITIONAL_OR_KEYWORD"
        },
        {
            name: "email",
            type_hint: "str",
            has_type_hint: true,
            default: "None",
            position: 2,
            kind: "POSITIONAL_OR_KEYWORD"
        }
    ]
})
```

**Query Examples**:
```cypher
// Find functions with untyped parameters (excluding *args/**kwargs)
MATCH (f:Function)
WHERE any(p IN f.parameters 
    WHERE NOT p.has_type_hint 
    AND p.kind <> "VAR_POSITIONAL" 
    AND p.kind <> "VAR_KEYWORD")
RETURN f.fqn, [p IN f.parameters WHERE NOT p.has_type_hint | p.name]

// Find functions with >7 named parameters (excluding *args/**kwargs)
MATCH (f:Function)
WHERE size([p IN f.parameters 
    WHERE p.kind IN ["POSITIONAL_OR_KEYWORD", "POSITIONAL_ONLY", "KEYWORD_ONLY"]]) > 7
RETURN f.fqn, size(f.parameters) as param_count

// Find functions with *args or **kwargs
MATCH (f:Function)
WHERE any(p IN f.parameters WHERE p.kind IN ["VAR_POSITIONAL", "VAR_KEYWORD"])
RETURN f.fqn, 
       [p IN f.parameters WHERE p.kind = "VAR_POSITIONAL" | p.name] as args_params,
       [p IN f.parameters WHERE p.kind = "VAR_KEYWORD" | p.name] as kwargs_params

// Find functions with keyword-only parameters
MATCH (f:Function)
WHERE any(p IN f.parameters WHERE p.kind = "KEYWORD_ONLY")
RETURN f.fqn, [p IN f.parameters WHERE p.kind = "KEYWORD_ONLY" | p.name]

// Find parameters with defaults
MATCH (f:Function)
WHERE any(p IN f.parameters WHERE p.default IS NOT NULL)
RETURN f.fqn, [p IN f.parameters WHERE p.default IS NOT NULL | {name: p.name, default: p.default}]
```

---

### Decorators Storage

**Location**: Separate Decorator nodes with DECORATED_WITH relationships.

**Schema**:
```cypher
(:Function)-[:DECORATED_WITH]->(:Decorator)
(:Method)-[:DECORATED_WITH]->(:Decorator)
(:Class)-[:DECORATED_WITH]->(:Decorator)
```

**Decorator Node Properties**:
- `name`: Decorator name (string)
- `args`: Argument string (string or null)
- `full_text`: Complete decorator text (string)

**Example**:
```cypher
// Create decorator nodes
CREATE (d1:Decorator {
    name: "require_auth",
    args: null,
    full_text: "@require_auth"
})

CREATE (d2:Decorator {
    name: "rate_limit",
    args: "(10)",
    full_text: "@rate_limit(10)"
})

// Create relationships
CREATE (f:Function {name: "create_user"})-[:DECORATED_WITH]->(d1)
CREATE (f)-[:DECORATED_WITH]->(d2)
```

**Query Examples**:
```cypher
// Find functions with specific decorator
MATCH (f:Function)-[:DECORATED_WITH]->(d:Decorator {name: "transaction"})
RETURN f.fqn

// Find functions missing required decorator
MATCH (f:Function)
WHERE f.name CONTAINS 'db_'
  AND NOT EXISTS {
    MATCH (f)-[:DECORATED_WITH]->(d:Decorator {name: "transaction"})
  }
RETURN f.fqn

// Count decorator usage
MATCH (f)-[:DECORATED_WITH]->(d:Decorator)
RETURN d.name, count(f) as usage_count
ORDER BY usage_count DESC
```

---

## Model Changes

### FunctionInfo

**Before**:
```python
@attrs.define(frozen=True)
class FunctionInfo:
    name: str
    parameters: str  # Serialized string
    decorators: str  # Serialized string
    # ... other fields
```

**After**:
```python
@attrs.define(frozen=True)
class FunctionInfo:
    name: str
    parameters: list[ParameterInfo]  # Structured list
    decorators: list[DecoratorInfo]  # Structured list
    # ... other fields
```

### ClassInfo

**Before**:
```python
@attrs.define(frozen=True)
class ClassInfo:
    name: str
    decorators: str  # Serialized string
    # ... other fields
```

**After**:
```python
@attrs.define(frozen=True)
class ClassInfo:
    name: str
    decorators: list[DecoratorInfo]  # Structured list
    # ... other fields
```

---

## Migration Strategy

### For Existing Data

**Option 1: Full Re-analysis (Recommended)**

Users must re-analyze their codebase with v0.8.0+ to get structured data:

```bash
# Clear old data
mapper analyse start . --name my-project --force

# Or use Neo4j Browser to clear:
# MATCH (n {package: "my-project"}) DETACH DELETE n
```

**Option 2: Query Migration Script (Optional, Not in v0.8.0)**

Future version could provide a migration script to convert existing string data to structured format.

**Migration Guide** (to be included in CHANGELOG):

```markdown
## Breaking Changes in v0.8.0

**Parameter and decorator storage format changed from strings to structured data.**

If you have existing analyzed projects in Neo4j, you must re-analyze them with v0.8.0+:

```bash
mapper analyse start /path/to/project --name my-project --force
```

This will:
- Clear existing data for `my-project`
- Re-analyze with structured parameter/decorator storage
- Enable new code quality queries

**Impact**: Custom Cypher queries that use string operations on `parameters` or `decorators` properties will need updating.

**Before (v0.7.x)**:
```cypher
WHERE f.parameters CONTAINS ': int'
```

**After (v0.8.0+)**:
```cypher
WHERE any(p IN f.parameters WHERE p.type_hint = 'int')
```

See [Cypher Query Cookbook](../technical/cypher-cookbook.md) for updated query patterns.
```

---

## Backward Compatibility

### Breaking Changes

1. **FunctionInfo.parameters**: Changed from `str` to `list[ParameterInfo]`
2. **FunctionInfo.decorators**: Changed from `str` to `list[DecoratorInfo]`
3. **ClassInfo.decorators**: Changed from `str` to `list[DecoratorInfo]`
4. **Neo4j schema**: Decorator nodes + DECORATED_WITH relationships added

### Non-Breaking Changes

- All other model fields remain unchanged
- Public API (`mapper.graph`, `mapper.analyser`) unchanged
- CLI commands unchanged
- Existing queries that don't use parameters/decorators continue working

### Compatibility Matrix

| Component | v0.7.x | v0.8.0+ | Compatible? |
|-----------|--------|---------|-------------|
| CLI commands | ✓ | ✓ | ✓ Yes |
| Graph storage | String props | Structured props | ✗ No (re-analysis required) |
| Cypher queries (no params/decorators) | ✓ | ✓ | ✓ Yes |
| Cypher queries (params/decorators) | String matching | Structured queries | ✗ No (query update required) |
| Python API (models) | String fields | Structured fields | ✗ No (breaking change) |

---

## Testing Requirements

### Unit Tests

1. **ParameterInfo validation**:
   - Valid instances
   - Invalid name (empty)
   - Invalid position (negative)
   - has_type_hint consistency

2. **DecoratorInfo validation**:
   - Valid instances
   - Invalid name (empty)
   - Invalid full_text (missing @)
   - Args consistency

3. **Model serialization**:
   - attrs to dict conversion
   - Dict to Neo4j map format

### Integration Tests

1. **Extraction**:
   - Extract parameters with/without type hints
   - Extract parameters with/without defaults
   - Extract decorators with/without arguments
   - Verify ParameterInfo/DecoratorInfo instances created correctly

2. **Storage**:
   - Store parameters as array of maps in Neo4j
   - Create Decorator nodes
   - Create DECORATED_WITH relationships
   - Verify data retrieval

3. **Queryability**:
   - Query functions by parameter properties
   - Query functions by decorator presence
   - Verify example queries from user journey work
   - Performance: queries complete in <1s

---

## Example: Complete Flow

### 1. Source Code

```python
@require_auth
@rate_limit(10)
def create_user(user_id: int, name, email: str = "unknown@example.com"):
    """Create a new user."""
    pass
```

### 2. Extracted Models

```python
func_info = FunctionInfo(
    name="create_user",
    fqn="myapp.users.create_user",
    parameters=[
        ParameterInfo(name="user_id", type_hint="int", has_type_hint=True, default=None, position=0, kind=ParameterKind.POSITIONAL_OR_KEYWORD),
        ParameterInfo(name="name", type_hint=None, has_type_hint=False, default=None, position=1, kind=ParameterKind.POSITIONAL_OR_KEYWORD),
        ParameterInfo(name="email", type_hint="str", has_type_hint=True, default='"unknown@example.com"', position=2, kind=ParameterKind.POSITIONAL_OR_KEYWORD),
    ],
    decorators=[
        DecoratorInfo(name="require_auth", args=None, full_text="@require_auth"),
        DecoratorInfo(name="rate_limit", args="(10)", full_text="@rate_limit(10)"),
    ],
    # ... other fields
)
```

### 3. Neo4j Storage

```cypher
// Function node with parameters
CREATE (f:Function {
    name: "create_user",
    fqn: "myapp.users.create_user",
    parameters: [
        {name: "user_id", type_hint: "int", has_type_hint: true, default: null, position: 0, kind: "POSITIONAL_OR_KEYWORD"},
        {name: "name", type_hint: null, has_type_hint: false, default: null, position: 1, kind: "POSITIONAL_OR_KEYWORD"},
        {name: "email", type_hint: "str", has_type_hint: true, default: '"unknown@example.com"', position: 2, kind: "POSITIONAL_OR_KEYWORD"}
    ]
})

// Decorator nodes
CREATE (d1:Decorator {name: "require_auth", args: null, full_text: "@require_auth"})
CREATE (d2:Decorator {name: "rate_limit", args: "(10)", full_text: "@rate_limit(10)"})

// Relationships
CREATE (f)-[:DECORATED_WITH]->(d1)
CREATE (f)-[:DECORATED_WITH]->(d2)
```

### 4. Queryable

```cypher
// Find this function because second parameter lacks type hint
MATCH (f:Function {fqn: "myapp.users.create_user"})
WHERE any(p IN f.parameters WHERE NOT p.has_type_hint)
RETURN f.fqn, f.parameters[1].name as untyped_param
// Returns: "myapp.users.create_user", "name"

// Find this function because it has @rate_limit decorator
MATCH (f:Function {fqn: "myapp.users.create_user"})-[:DECORATED_WITH]->(d:Decorator {name: "rate_limit"})
RETURN f.fqn, d.args
// Returns: "myapp.users.create_user", "(10)"
```

---

## Summary

**Key Changes**:
1. New attrs models: `ParameterInfo`, `DecoratorInfo`
2. New enum: `ParameterKind` (matches Python's `inspect.Parameter.kind`)
3. FunctionInfo/ClassInfo fields change from string to structured lists
4. Parameters stored as array of maps on Function/Method nodes
5. Decorators stored as separate nodes with DECORATED_WITH relationships
6. Breaking change: requires re-analysis of existing projects

**Benefits**:
- Type-safe data structures with validation
- Precise queries without string parsing
- Enables code quality enforcement
- Handles all parameter types (*args, **kwargs, keyword-only, etc.)

**Migration**: Re-analyze projects with `mapper analyse start --force`
