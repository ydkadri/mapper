# Neo4j Schema Reference

Complete schema reference for Mapper's Neo4j graph database, including node types, properties, relationships, constraints, and indexes.

---

## Table of Contents

- [Overview](#overview)
- [Node Types](#node-types)
- [Relationship Types](#relationship-types)
- [Constraints](#constraints)
- [Indexes](#indexes)
- [Schema Initialization](#schema-initialization)
- [Schema Evolution](#schema-evolution)
- [Querying Best Practices](#querying-best-practices)

---

## Overview

Mapper stores Python code structure in Neo4j using a graph model where:
- **Nodes** represent code entities (modules, classes, functions, methods)
- **Relationships** represent connections (defines, contains, inherits, calls, imports)
- **Properties** store metadata about each entity

The schema is designed for:
- **Fast querying** via strategic indexes and constraints
- **Referential integrity** via uniqueness constraints on FQNs
- **Multi-package support** via package property on all nodes
- **Version tracking** (future) via package versioning

---

## Node Types

### Module

Represents a Python file (`.py`).

**Label**: `Module`

**Properties**:

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `name` | string | Yes | Module name (filename without .py) | `"handlers"` |
| `path` | string | Yes | Full file path (UNIQUE) | `"src/handlers.py"` |
| `fqn` | string | Yes | Fully qualified name | `"myapp.handlers"` |
| `package` | string | Yes | Package this module belongs to | `"my-project"` |
| `type` | string | Yes | Always `"module"` | `"module"` |
| `docstring` | string | No | Module-level docstring | `"Handler functions"` |

**Constraints**:
- **Uniqueness**: `path` must be unique across all modules

**Indexes**:
- `name` - Fast lookups by module name
- `type` - Fast filtering by node type

**Example**:
```cypher
CREATE (m:Module {
  name: "handlers",
  path: "src/myapp/handlers.py",
  fqn: "myapp.handlers",
  package: "my-project",
  type: "module",
  docstring: "HTTP request handlers"
})
```

---

### Class

Represents a class definition.

**Label**: `Class`

**Properties**:

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `name` | string | Yes | Class name | `"UserService"` |
| `fqn` | string | Yes | Fully qualified name (UNIQUE) | `"services.UserService"` |
| `package` | string | Yes | Package name | `"my-project"` |
| `is_public` | boolean | Yes | Public vs private (naming) | `true` |
| `docstring` | string | No | Class docstring | `"User management service"` |
| `bases` | string | No | Serialized base classes* | `"['BaseService', 'Protocol']"` |
| `decorators` | string | No | Serialized decorators* | `"['@dataclass']"` |

**Constraints**:
- **Uniqueness**: `fqn` must be unique across all classes

**Indexes**:
- `name` - Fast lookups by class name
- `package` - Filter by package
- `is_public` - Filter public/private

**Example**:
```cypher
CREATE (c:Class {
  name: "UserService",
  fqn: "services.UserService",
  package: "my-project",
  is_public: true,
  docstring: "Handles user operations",
  bases: "['BaseService']",
  decorators: "[]"
})
```

**Notes**:
- *`bases` and `decorators` are string-serialized lists (improvement tracked in #30)
- `is_public` determined by naming: `_PrivateClass` → false, `PublicClass` → true

---

### Function

Represents a top-level function (not in a class).

**Label**: `Function`

**Properties**:

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `name` | string | Yes | Function name | `"process_request"` |
| `fqn` | string | Yes | Fully qualified name (UNIQUE) | `"handlers.process_request"` |
| `package` | string | Yes | Package name | `"my-project"` |
| `is_public` | boolean | Yes | Public vs private (naming) | `true` |
| `docstring` | string | No | Function docstring | `"Process HTTP request"` |
| `return_type` | string | No | Return type annotation | `"Response"` |
| `parameters` | string | No | Serialized parameters* | `"['request: Request', 'timeout: int = 30']"` |
| `decorators` | string | No | Serialized decorators* | `"['@app.post', '@validate']"` |

**Constraints**:
- **Uniqueness**: `fqn` must be unique across all functions

**Indexes**:
- `name` - Fast lookups by function name
- `package` - Filter by package
- `is_public` - Filter public/private

**Example**:
```cypher
CREATE (f:Function {
  name: "process_request",
  fqn: "handlers.process_request",
  package: "my-project",
  is_public: true,
  docstring: "Process incoming HTTP request",
  return_type: "Response",
  parameters: "['request: Request', 'timeout: int']",
  decorators: "['@app.post']"
})
```

**Notes**:
- *`parameters` and `decorators` are string-serialized (improvement tracked in #30)
- `is_public` determined by naming: `_private_func` → false, `public_func` → true

---

### Method

Represents a class method.

**Label**: `Method`

**Properties**: Same as Function

**Difference from Function**:
- Methods are functions defined within a class
- Methods have `self` or `cls` as first parameter (stored in `parameters`)
- Methods are connected to their class via `CONTAINS` relationship

**Example**:
```cypher
CREATE (m:Method {
  name: "save",
  fqn: "services.UserService.save",
  package: "my-project",
  is_public: true,
  docstring: "Save user to database",
  return_type: "None",
  parameters: "['self', 'user: User']",
  decorators: "[]"
})
```

---

## Relationship Types

### DEFINES

**Pattern**: `(Module)-[:DEFINES]->(Class|Function)`

**Description**: A module defines a class or function at the top level.

**Properties**: None

**Example**:
```cypher
MATCH (m:Module {fqn: "handlers"}), (f:Function {fqn: "handlers.process_request"})
CREATE (m)-[:DEFINES]->(f)
```

**Use cases**:
- Find what classes/functions are defined in a module
- Navigate from module to its contents

---

### CONTAINS

**Pattern**: `(Class)-[:CONTAINS]->(Method)`

**Description**: A class contains a method.

**Properties**: None

**Example**:
```cypher
MATCH (c:Class {fqn: "services.UserService"}), (m:Method {fqn: "services.UserService.save"})
CREATE (c)-[:CONTAINS]->(m)
```

**Use cases**:
- Find all methods in a class
- Navigate from class to its methods

---

### INHERITS

**Pattern**: `(Class)-[:INHERITS]->(Class)`

**Description**: A class inherits from another class (parent/base class).

**Properties**: None

**Example**:
```cypher
MATCH (child:Class {fqn: "models.User"}), (parent:Class {fqn: "models.BaseModel"})
CREATE (child)-[:INHERITS]->(parent)
```

**Use cases**:
- Find class hierarchy
- Trace inheritance chains
- Find all subclasses of a class

**Notes**:
- Relationships created during `finalize()` step (deferred)
- Only tracks inheritance within the same package
- External base classes (e.g., `Exception`) not stored as nodes

---

### CALLS

**Pattern**: `(Function|Method)-[:CALLS]->(Function|Method)`

**Description**: A function or method calls another function or method.

**Properties**: None

**Example**:
```cypher
MATCH (caller:Function {fqn: "handlers.process_request"}),
      (callee:Function {fqn: "utils.validate_input"})
CREATE (caller)-[:CALLS]->(callee)
```

**Use cases**:
- Trace function call chains
- Find callers of a function (reverse dependencies)
- Analyze coupling and dependencies
- Detect unused functions

**Notes**:
- Relationships created during `finalize()` step (deferred)
- Only tracks calls within the same package
- Calls to external libraries not stored

---

### IMPORTS

**Pattern**: `(Module)-[:IMPORTS]->(Module)`

**Description**: A module imports another module.

**Properties**: None

**Example**:
```cypher
MATCH (m1:Module {fqn: "handlers"}), (m2:Module {fqn: "services"})
CREATE (m1)-[:IMPORTS]->(m2)
```

**Use cases**:
- Analyze module dependencies
- Find circular imports
- Trace transitive dependencies

**Notes**:
- Relationships created during `finalize()` step (deferred)
- Only tracks imports within the same package
- External imports (e.g., `typing`, `json`) not stored

---

## Constraints

Constraints ensure data integrity and enable fast lookups. Created automatically by `mapper init`.

### Module Path Uniqueness

```cypher
CREATE CONSTRAINT module_path_unique IF NOT EXISTS
FOR (m:Module) REQUIRE m.path IS UNIQUE
```

**Purpose**: Ensure each file path appears only once in the database.

**Impact**: Prevents duplicate module entries.

---

### Class FQN Uniqueness

```cypher
CREATE CONSTRAINT class_fqn_unique IF NOT EXISTS
FOR (c:Class) REQUIRE c.fqn IS UNIQUE
```

**Purpose**: Ensure each class fully qualified name is unique.

**Impact**:
- Prevents duplicate class entries
- Enables fast lookups by FQN
- Automatically creates index on `c.fqn`

---

### Function FQN Uniqueness

```cypher
CREATE CONSTRAINT function_fqn_unique IF NOT EXISTS
FOR (f:Function) REQUIRE f.fqn IS UNIQUE
```

**Purpose**: Ensure each function fully qualified name is unique.

**Impact**:
- Prevents duplicate function entries (includes methods)
- Enables fast lookups by FQN
- Automatically creates index on `f.fqn`

**Note**: This constraint applies to both Function and Method nodes since they share the same label pattern.

---

## Indexes

Indexes improve query performance. Created automatically by `mapper init`.

### Name Indexes

```cypher
CREATE INDEX module_name_index IF NOT EXISTS FOR (m:Module) ON (m.name);
CREATE INDEX class_name_index IF NOT EXISTS FOR (c:Class) ON (c.name);
CREATE INDEX function_name_index IF NOT EXISTS FOR (f:Function) ON (f.name);
```

**Purpose**: Fast lookups by name (without FQN).

**Use case**: Finding entities by simple name across packages.

**Example query**:
```cypher
MATCH (f:Function {name: "process"})
RETURN f.fqn, f.package
```

---

### Type Index

```cypher
CREATE INDEX module_type_index IF NOT EXISTS FOR (m:Module) ON (m.type);
```

**Purpose**: Fast filtering by node type.

**Use case**: Distinguish modules from other node types in mixed queries.

---

### Package Index (Implicit)

The `package` property is frequently queried, and Neo4j query planner may create implicit indexes.

**Recommended manual index** (future enhancement):
```cypher
CREATE INDEX package_index IF NOT EXISTS FOR (n) ON (n.package);
```

**Use case**: Filter nodes by package in all queries.

---

### Visibility Index (Implicit)

The `is_public` property is queried for API surface analysis.

**Recommended manual index** (future enhancement):
```cypher
CREATE INDEX visibility_index IF NOT EXISTS FOR (n) ON (n.is_public);
```

**Use case**: Find public vs private entities efficiently.

---

## Schema Initialization

### Automatic Initialization

Schema is created automatically by `mapper init`:

```bash
mapper init
```

This command:
1. Connects to Neo4j
2. Creates all constraints (idempotent)
3. Creates all indexes (idempotent)
4. Saves configuration to file

### Manual Initialization

You can manually initialize the schema via Python:

```python
from mapper import graph

# Connect to Neo4j
connection = graph.Neo4jConnection(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="devpassword",
    database="neo4j"
)

# Initialize schema
connection.initialize_database()
```

### Verifying Schema

Check that constraints and indexes exist:

```cypher
// Show all constraints
SHOW CONSTRAINTS;

// Show all indexes
SHOW INDEXES;
```

---

## Schema Evolution

### Current Version: v0.5.0

**Nodes**: Module, Class, Function, Method
**Relationships**: DEFINES, CONTAINS, INHERITS, CALLS, IMPORTS
**Constraints**: path (Module), fqn (Class, Function)
**Indexes**: name (all types), type (Module)

### Planned Improvements

#### v0.6.0: Structured Property Storage (#30)

**Problem**: Properties like `parameters`, `decorators`, and `bases` are string-serialized lists.

**Solution**: Store as structured data:

**Option 1: JSON properties**
```cypher
// Store as JSON string, query with apoc functions
CREATE (f:Function {
  name: "process",
  parameters: '{"args": [{"name": "request", "type": "Request"}]}'
})
```

**Option 2: Separate nodes**
```cypher
// Create Parameter nodes
CREATE (f:Function {name: "process"})
CREATE (p:Parameter {name: "request", type: "Request", position: 0})
CREATE (f)-[:HAS_PARAMETER]->(p)
```

**Option 3: Array properties**
```cypher
// Store as Cypher arrays (simple types only)
CREATE (f:Function {
  name: "process",
  parameter_names: ["request", "timeout"],
  parameter_types: ["Request", "int"]
})
```

#### v0.8.0: Cross-Package Relationships (#29)

**Problem**: Relationships only tracked within same package.

**Solution**: Store package as relationship property:

```cypher
CREATE (f1:Function {fqn: "pkg1.handler", package: "pkg1"})
CREATE (f2:Function {fqn: "pkg2.utils", package: "pkg2"})
CREATE (f1)-[:CALLS {from_package: "pkg1", to_package: "pkg2"}]->(f2)
```

This enables:
- Cross-package dependency analysis
- Package-level architecture queries
- Multi-package impact analysis

#### Future: External File Tracking (#41)

**New node type**: `ExternalFile`

```cypher
CREATE (f:ExternalFile {
  path: "templates/email.html",
  type: "template",
  package: "my-project"
})
CREATE (func:Function {fqn: "handlers.send_email"})-[:REFERENCES]->(f)
```

#### Future: Version Tracking

**Property additions**:
```cypher
CREATE (m:Module {
  name: "handlers",
  package: "my-project",
  version: "0.5.0",
  analyzed_at: datetime("2026-03-27T10:30:00Z")
})
```

**Enables**:
- Historical analysis
- Version comparison
- Incremental updates

### Migration Strategy

#### Non-Breaking Changes

Add new properties, nodes, or relationships without removing old ones:
- Old queries continue to work
- New queries can use new features
- No migration needed

**Example**: Adding `version` property:
```cypher
// Old queries still work
MATCH (m:Module {package: "my-project"}) RETURN m

// New queries can filter by version
MATCH (m:Module {package: "my-project", version: "0.5.0"}) RETURN m
```

#### Breaking Changes

When removing or renaming properties:

1. **Add new property**, keep old one:
   ```cypher
   // Both old and new queries work
   MATCH (f:Function) RETURN f.parameters, f.parameter_list
   ```

2. **Deprecation period** (2 versions):
   - Document old property as deprecated
   - Update internal code to use new property

3. **Remove old property**:
   ```cypher
   MATCH (f:Function) REMOVE f.parameters
   ```

4. **Update version** in docs

#### Data Migration Script

For major schema changes, provide migration script:

```python
# migrate_v05_to_v06.py
from mapper import graph

connection = graph.Neo4jConnection.from_config()

# Migrate string-serialized parameters to JSON
with connection.driver.session() as session:
    result = session.run("""
        MATCH (f:Function)
        WHERE f.parameters IS NOT NULL
        WITH f, apoc.convert.fromJsonList(f.parameters) as param_list
        SET f.parameter_list = param_list
    """)
```

---

## Querying Best Practices

### Use Labels

Always specify node labels for better performance:

```cypher
// ✅ Good - uses label index
MATCH (f:Function {package: "my-project"}) RETURN f

// ❌ Slow - scans all nodes
MATCH (n {package: "my-project"}) WHERE n:Function RETURN n
```

### Use Constraints for Lookups

When looking up by FQN, leverage uniqueness constraints:

```cypher
// ✅ Fast - uses unique constraint index
MATCH (f:Function {fqn: "handlers.process_request"}) RETURN f

// ❌ Slower - uses name index + filter
MATCH (f:Function {name: "process_request"})
WHERE f.fqn CONTAINS "handlers"
RETURN f
```

### Filter Early

Push WHERE clauses before traversal:

```cypher
// ✅ Good - filter before traversal
MATCH (f:Function {package: "my-project", is_public: true})
MATCH (f)-[:CALLS]->(target)
RETURN f, target

// ❌ Less efficient - filter after traversal
MATCH (f:Function)-[:CALLS]->(target)
WHERE f.package = "my-project" AND f.is_public = true
RETURN f, target
```

### Limit Variable Paths

Always bound variable-length path patterns:

```cypher
// ✅ Good - bounded depth
MATCH path = (f)-[:CALLS*1..5]->(target) RETURN path

// ❌ Dangerous - unbounded
MATCH path = (f)-[:CALLS*]->(target) RETURN path
```

### Use Parameters

Always parameterize queries for performance and security:

```cypher
// ✅ Good - parameterized
MATCH (f:Function {package: $package}) RETURN f

// ❌ Bad - string interpolation
MATCH (f:Function {package: 'my-project'}) RETURN f
```

---

## Related Documentation

- [Graph Loader](graph_loader.md) - How data is loaded into Neo4j
- [Cypher Query Cookbook](cypher-queries.md) - Query examples for analysis
- [Analyzing and Querying Code](../user-journeys/05-analyzing-querying-code.md) - User guide for querying
