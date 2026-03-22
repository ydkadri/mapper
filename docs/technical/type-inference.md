# Type Inference

Technical documentation for the type inference system.

---

## Overview

The `type_inference` package infers types from Python code and validates them against type annotations. It helps identify type mismatches without running the code.

**Purpose**: Validate that actual code behavior matches declared type annotations, catching potential bugs early.

**Key Design Principle**: Infer types from code patterns (return statements, literals, assignments), then compare against type hints.

---

## Architecture

```
src/mapper/type_inference/
├── __init__.py        # Package exports
├── models.py          # Data models (InferenceResult, ValidationResult)
└── inferrer.py        # TypeInferrer implementation
```

### Package Structure

**`models.py`**: Data models for inference results
- `InferenceResult`: Inferred type and confidence level
- `ValidationResult`: Comparison between inferred and annotated types

**`inferrer.py`**: Core inference logic
- `TypeInferrer`: Main class that infers types and validates annotations

---

## Usage

### Basic Type Validation

```python
from mapper import ast_parser, type_inference

code = '''
def get_user_age() -> int:
    return "not an int"  # Type mismatch!
'''

extractor = ast_parser.ASTExtractor(code, "example.py")
extraction = extractor.extract()

inferrer = type_inference.TypeInferrer(extraction, extractor.tree)
validation = inferrer.validate_function("get_user_age")

if validation.matches is False:
    print(f"Type mismatch: expected int, inferred {validation.inferred_type}")
```

### Type Inference Only

```python
from mapper import ast_parser, type_inference

code = '''
def calculate():
    return 42
'''

extractor = ast_parser.ASTExtractor(code, "example.py")
extraction = extractor.extract()

inferrer = type_inference.TypeInferrer(extraction, extractor.tree)
result = inferrer.infer_return_type("calculate")

print(result.inferred_type)  # "int"
print(result.confidence)     # "high"
```

---

## How It Works

### Initialization

The `TypeInferrer` requires both extraction results and the AST tree:

```python
def __init__(self, extraction: ExtractionResult, tree: ast.Module):
    self.extraction = extraction  # High-level structure
    self.tree = tree              # Low-level AST for analysis
    self._build_function_index()  # Index functions by name
```

**Why both?**:
- `extraction`: Provides function info with type annotations
- `tree`: Provides AST nodes for analyzing return statements

### Type Inference Process

1. **Find function**: Look up function AST node by name
2. **Analyze returns**: Walk AST to find all `return` statements
3. **Infer each return**: Determine type from expression
4. **Aggregate**: Combine multiple return types
5. **Confidence**: Assess inference reliability

### Validation Process

1. **Get annotation**: Extract declared return type from `FunctionInfo`
2. **Infer type**: Use type inference on return statements
3. **Compare**: Check if inferred type matches annotation
4. **Report**: Return `ValidationResult` with match status

---

## Type Inference Rules

### Literals

Direct type inference from literal values:

```python
return 42              # → int
return "hello"         # → str
return 3.14            # → float
return True            # → bool
return None            # → None
return [1, 2, 3]       # → list
return {"key": "val"}  # → dict
```

**Confidence**: High

### Function Calls

Type inference from called function's return type:

```python
def get_user() -> User:
    return User()

def process():
    return get_user()  # → User (from get_user's annotation)
```

**Confidence**: Medium (depends on annotation accuracy)

### Variable References

Type inference from variable name patterns:

```python
user = fetch_user()
return user  # → Unknown (can't track variable types across statements)
```

**Confidence**: Low

### Implicit None Returns

Functions with no explicit return statement implicitly return `None`:

```python
def print_hello():
    print("Hello")
    # No return statement

# → None
```

**Bare return statements** also return `None`:

```python
def early_exit(x: int):
    if x < 0:
        return  # Bare return → None
    return x
# → int | None
```

**Confidence**: High (for implicit None), Medium (for mixed returns)

### Unknown Types

When type cannot be determined:

```python
return complex_expression()  # → Unknown
```

**Confidence**: Low

---

## Data Models

### InferenceResult

Result of inferring a type:

```python
@attrs.define
class InferenceResult:
    inferred_type: str           # Inferred type name
    confidence: str = "low"      # "low", "medium", "high"
```

**Example**:
```python
InferenceResult(inferred_type="int", confidence="high")
InferenceResult(inferred_type="User", confidence="medium")
InferenceResult(inferred_type="Unknown", confidence="low")
```

### ValidationResult

Result of validating a function's return type:

```python
@attrs.define
class ValidationResult:
    matches: bool | None         # True/False/None (no annotation)
    inferred_type: str | None    # What was inferred
    warnings: list[str]          # Warning messages
```

**Example**:
```python
# Matches annotation
ValidationResult(matches=True, inferred_type="int", warnings=[])

# Mismatch
ValidationResult(
    matches=False,
    inferred_type="str",
    warnings=["Expected int, got str"]
)

# No annotation to validate
ValidationResult(matches=None, inferred_type="int", warnings=[])
```

---

## Implementation Details

### Function Indexing

On initialization, build two indexes:

1. **AST nodes by name**: `_function_nodes: dict[str, ast.FunctionDef]`
2. **Function info by name**: `_function_info: dict[str, FunctionInfo]`

This allows O(1) lookup by function name.

### Return Statement Analysis

Walk the function's AST to find all return statements, using a **set** for automatic uniqueness:

```python
return_types = set()  # Use set to automatically deduplicate

for node in ast.walk(func_node):
    if isinstance(node, ast.Return):
        if node.value:  # Has return value
            inferred = self._infer_from_expression(node.value)
            if inferred:
                return_types.add(inferred)
        else:  # Bare "return" statement
            return_types.add("None")
```

**Benefits of using sets**:
- Automatic deduplication (multiple `return 42` statements → single `int`)
- Efficient membership testing
- Reflects mathematical nature of union types (sets)

### Multiple Return Types

When a function has multiple return statements with different types:

```python
def maybe_user(user_id: int) -> User | None:
    if user_id > 0:
        return User(user_id)  # → User
    return None               # → None
```

**Strategy**: Combine with union type using sorted output for consistency:

```python
# Multiple types detected
return_types = {"User", "None"}

# Sort for consistent output
return " | ".join(sorted(return_types))  # → "None | User"
```

**Why sorted?** Ensures `"int | str"` and `"str | int"` produce the same output for comparison purposes.

### Type String Extraction

Convert AST nodes to type strings:

- `ast.Name` → Simple type: `"int"`, `"str"`, `"User"`
- `ast.Attribute` → Qualified type: `"module.Type"`
- `ast.Subscript` → Generic type: `"list[str]"`, `"dict[str, int]"`

Handles nested generics: `Optional[list[dict[str, Any]]]`

---

## Confidence Levels

### High Confidence

- Inferred from literal values
- Type is unambiguous

```python
return 42  # int, high confidence
```

### Medium Confidence

- Inferred from function call with annotation
- Assumes annotation is correct

```python
return get_user()  # User (if get_user() -> User), medium confidence
```

### Low Confidence

- Inferred from variable reference
- Complex expressions
- Cannot determine type

```python
return user  # Unknown, low confidence
```

---

## Limitations

### Current Limitations

1. **No flow analysis**: Cannot track variable types across statements
   ```python
   user = fetch_user()  # Don't know user's type
   return user          # → Unknown
   ```

2. **No type narrowing**: Cannot handle conditional type refinement
   ```python
   if isinstance(x, int):
       return x  # Still treated as generic type
   ```

3. **No generic inference**: Cannot infer generic type parameters
   ```python
   return [1, 2, 3]  # → list, not list[int]
   ```

4. **No attribute analysis**: Cannot infer types from attributes
   ```python
   return user.name  # → Unknown
   ```

### Why These Limitations?

These features require static type analysis similar to mypy or pyright, which is complex. Current implementation focuses on simple, reliable inference for common cases.

**Future**: Could integrate with `mypy` or `pyright` for advanced analysis.

---

## Integration Points

### With AST Parser

Requires extraction results and AST tree from parser:

```python
from mapper import ast_parser, type_inference

extractor = ast_parser.ASTExtractor(code, file_path)
extraction = extractor.extract()

# Pass both to inferrer
inferrer = type_inference.TypeInferrer(extraction, extractor.tree)
```

### With Analyzer

The `analyser` package uses type inference for validation:

```python
inferrer = type_inference.TypeInferrer(extraction, extractor.tree)

for func in extraction.functions:
    if func.return_type:  # Has annotation to validate
        validation = inferrer.validate_function(func.name)
        if validation.matches is False:
            # Report type mismatch
            pass
```

---

## Error Handling

### Missing Functions

If function name not found:

```python
result = inferrer.infer_return_type("nonexistent")
# Returns: InferenceResult(inferred_type="Unknown", confidence="low")
```

Graceful degradation - doesn't raise exception.

### No Return Statements

If function has no return statements:

```python
def no_return():
    print("hello")

result = inferrer.infer_return_type("no_return")
# Returns: InferenceResult(inferred_type="None", confidence="high")
```

Assumes implicit `return None`.

---

## Testing

### Test Coverage

Tests in `tests/unit/type_inference/test_inference.py`:

- Literal type inference (int, str, bool, None)
- Function call type inference
- Multiple return types (union handling)
- Type validation (match, mismatch, no annotation)
- Unknown type handling
- Confidence level assignment

### Test Approach

Create minimal code examples and verify inference:

```python
def test_infer_from_literal(self):
    code = '''
    def get_number():
        return 42
    '''

    extractor = ast_parser.ASTExtractor(code, "test.py")
    extraction = extractor.extract()
    inferrer = type_inference.TypeInferrer(extraction, extractor.tree)

    result = inferrer.infer_return_type("get_number")
    assert result.inferred_type == "int"
    assert result.confidence == "high"
```

---

## Use Cases

### Type Mismatch Detection

Find functions where implementation doesn't match annotation:

```python
def get_count() -> int:
    return "not an int"  # Bug!
```

**Detection**:
```python
validation = inferrer.validate_function("get_count")
if validation.matches is False:
    print(f"Type error: {validation.warnings}")
```

### Missing Annotations

Find functions that should have type hints:

```python
def process_data():  # No return type
    return {"status": "ok"}
```

**Detection**:
```python
func_info = extraction.functions[0]
if func_info.return_type is None:
    result = inferrer.infer_return_type(func_info.name)
    print(f"Suggestion: Add return type: {result.inferred_type}")
```

### Code Quality Metrics

Track type annotation coverage:

```python
total_functions = len(extraction.functions)
annotated = sum(1 for f in extraction.functions if f.return_type)
coverage = (annotated / total_functions) * 100
```

---

## Future Enhancements

Potential improvements for future versions:

- **Flow-sensitive analysis**: Track variable types through assignments
- **Generic type inference**: Infer `list[int]` not just `list`
- **Attribute type inference**: Track types through object attributes
- **Union type handling**: Better support for `Union[X, Y]` types
- **Integration with mypy**: Use mypy for advanced type analysis
- **Type narrowing**: Handle `isinstance` checks and type guards
- **Async function support**: Validate `async def` return types

---

**See Also**:
- [AST Parser](ast-parser.md) - Extraction of code structure
- [Analyzer](analyser.md) - Orchestration of analysis workflow
- [CLI Commands](cli-commands.md) - Using type validation in CLI
