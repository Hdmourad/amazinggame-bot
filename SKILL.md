# High-Quality Software Development

## Purpose
Ensure code meets quality standards through Test-Driven Development (TDD), SOLID principles, linting, formatting, and structured review processes.

## Scope
- **Applies to**: Python packages in this workspace
- **Triggers**: When implementing features, refactoring, or fixing bugs
- **Quality gates**: Tests, linting, type checking, formatting

---

## 1. Test-Driven Development (TDD) Workflow

### Step 1: Write Failing Test First
- Define the requirement as a test
- Test should fail (red phase)
- Place tests in `tests/` directory, mirroring source structure
- Use clear, descriptive test names: `test_<function>_<scenario>_<expected>`

**Example**:
```python
# tests/test_generator.py
def test_generate_maze_returns_grid():
    """Maze generator should return a 2D grid structure"""
    maze = MazeGenerator(10, 10).generate()
    assert maze is not None
    assert len(maze) == 10
```

### Step 2: Write Minimal Implementation
- Implement only what's needed to pass the test (green phase)
- Avoid over-engineering
- Keep implementation focused

### Step 3: Refactor
- Improve code quality without changing behavior
- Extract functions, remove duplication
- Ensure tests still pass
- Apply SOLID principles

**Decision Point**:
- All tests passing? ✓ Move to next feature
- Tests failing? → Debug and fix implementation
- Code smells? → Refactor

---

## 2. SOLID Principles

### S - Single Responsibility
- Each class/function has ONE reason to change
- **Check**: Run `grep -n "class\|def" src/` and verify each has clear purpose

### O - Open/Closed
- Open for extension, closed for modification
- Use inheritance, composition, or plugins instead of modifying existing code

### L - Liskov Substitution
- Subtypes must be substitutable for their base types
- Test polymorphic behavior

### I - Interface Segregation
- Clients shouldn't depend on interfaces they don't use
- Keep interfaces small and focused

### D - Dependency Inversion
- Depend on abstractions, not concrete implementations
- Inject dependencies when possible

---

## 3. Code Quality Checks

### Linting (pylint, ruff)
```bash
# Run linter
ruff check src/ tests/

# Auto-fix basic issues
ruff check --fix src/ tests/
```

**Standards**:
- Line length: 88 characters (Ruff standard)
- Complexity: Functions should be ≤10 cyclomatic complexity
- No unused imports or variables
- Type hints for public APIs
- No noqa comments without justification
- No warnings/errors without justification

### Type Checking
```bash
# Check with ty
ty src/
```

**Requirements**:
- Public and private functions/classes must have type hints

### Formatting (Ruff)
```bash
# Format code
ruff format src/ tests/
```

**Standards**:
- Consistent spacing and quotes
- Line length: 88 characters
- Proper docstring formatting

---

## 4. Implementation Checklist

### Before Committing Code

- [ ] **Tests exist and pass**
  ```bash
  pytest tests/ -v
  ```

- [ ] **Linter passes with no errors**
  ```bash
  ruff check src/ tests/
  ```

- [ ] **Type checking passes**
  ```bash
  ty src/
  ```

- [ ] **Code is formatted**
  ```bash
  ruff format --check src/ tests/
  ```

- [ ] **Test coverage is adequate** (target: >80%)
  ```bash
  pytest --cov=src tests/
  ```

- [ ] **Docstrings are present**
  - Public functions: Have docstrings
  - Complex logic: Include "why", not just "what"
  - Modules: Start with docstring

- [ ] **No console debug artifacts**
  - No `print()` statements in library code
  - Remove `breakpoint()`, `pdb` calls

- [ ] **Changelog/docs updated**
  - Update README.md if API changed
  - Document breaking changes

- [ ] **The repo is clean**
  ```bash
  prek run --all-files
  ```

---

## 5. Code Review Criteria

### Structure
- [ ] Follows SOLID principles
- [ ] Functions are small and focused (<20 lines preferred)
- [ ] No deep nesting (max 3 levels)
- [ ] DRY principle followed (no code duplication)

### Functionality
- [ ] All tests pass
- [ ] Edge cases handled
- [ ] No hardcoded values
- [ ] Error handling appropriate

### Maintainability
- [ ] Clear variable/function names
- [ ] Docstrings explain "why"
- [ ] Comments explain complex logic only
- [ ] No dead code

---

## 6. Workflow Summary

```
1. Create test (RED) → 2. Implement (GREEN) → 3. Refactor (BLUE)
       ↓                     ↓                      ↓
  Define requirement    Pass test            Apply SOLID
  Clear naming         Minimal code         Extract functions
  Edge cases           No duplication       Quality checks
       ↓                     ↓                      ↓
  ────────────────────────────────────────────────────
                            ↓
                  Run all quality checks
           (linting, type-checking, formatting)
                            ↓
                         Commit
```

---

## 7. Tools Configuration

### Required Dependencies
Add to `pyproject.toml`:
```toml
[tool.ruff]
target-version = "py314"
```

---

## 8. Example Prompts to Use This Skill

- *"Add a new feature to the maze generator using TDD"*
- *"Review this code for SOLID violations"*
- *"Set up linting and type checking for this package"*
- *"Refactor this function to reduce complexity"*
- *"Help me write tests for this module"*

---

## Notes
- Quality is iterative—refine these practices as you learn
- Balance perfectionism with pragmatism
- Complex features may need multiple TDD cycles
- Document decisions that aren't obvious from code
