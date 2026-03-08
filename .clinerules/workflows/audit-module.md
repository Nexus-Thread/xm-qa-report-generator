# Workflow: Audit and Improve a Module

Use this workflow when a user gives you a specific module or package and asks you to audit it, improve it, proofread it, or otherwise tighten its quality.

## Purpose
- Review a target module in a structured, repeatable way
- Identify correctness, maintainability, architecture, naming, documentation, logging, and testing issues
- Make safe, scoped improvements instead of broad unrelated refactors
- Leave the module cleaner, clearer, and better validated than before

## Typical inputs
- A package path such as `src/qa_report_generator/adapters/output/parsers/k6_parsed_report/`
- A single module file such as `src/qa_report_generator/adapters/input/cli_adapter/adapter.py`
- A related test area such as `tests/unit/adapters/output/parsers/`

## When to run this workflow
- When the user says to audit a module, adapter, package, or layer
- When the user asks for improvements without giving line-level instructions
- When a module feels awkward, brittle, unclear, noisy, or under-tested
- When you need a disciplined review path before making targeted refactors

## Scope rules
- Prefer the smallest reasonable target area first
- Keep changes focused on the requested module and directly related tests/docs
- Do not widen the task into unrelated cleanup unless the user asks for it
- If the requested module sits at an architectural boundary, inspect adjacent ports and tests as needed for context

## How to run

### 1. Identify the target and its boundary
Determine exactly what the user means by the given module.

Examples:
- package: `src/qa_report_generator/adapters/output/narrative/structured_llm/`
- file: `src/qa_report_generator/adapters/output/persistence/json_file_debug/adapter.py`
- conceptual module: `adapters/input`

Clarify the target if needed:
- exact path to review
- whether the task is documentation-only, refactor-only, bug-fix-focused, or broad quality improvement
- whether tests should be added or updated when behavior changes

### 2. Discover related files
Inspect the target itself and the closest surrounding files needed to understand it.

Useful commands:
```bash
# List files inside the target package
find src/qa_report_generator/adapters/ -path "*<target_fragment>*" -type f | sort

# Find tests that likely cover the target
find tests/ -name "test_*.py" | grep "<target_fragment>"

# Find references to a class, function, or adapter name
rg "ClassName|function_name|AdapterName" src/ tests/
```

Review at least:
- target file(s)
- nearest `__init__.py` exports when the target is a package
- relevant ports or DTOs from `application/` if the module crosses layer boundaries
- closest unit tests and any integration tests that exercise the target

### 3. Check architecture and boundary compliance
Evaluate the target against the repository's hexagonal rules.

Questions to answer:
- Does dependency direction point inward?
- Does the module stay within its layer responsibility?
- Does an adapter depend on application ports rather than concrete peer adapters?
- Is external schema mapping kept in adapters rather than leaked inward?
- Are framework and I/O concerns isolated away from domain and application logic?

For adapter audits, pay special attention to:
- input validation and normalization at the adapter boundary
- translation between external payloads and DTOs/domain objects
- exception translation at the boundary
- avoidance of adapter-to-adapter coupling

### 4. Review code quality inside the module
Audit the target for issues in these categories.

#### Correctness and robustness
- obvious bugs or missing edge-case handling
- fragile assumptions about input shape or state
- error handling that is too broad, unclear, or leaks the wrong exception type
- dead code or unreachable branches

#### Structure and readability
- overly large functions or files
- mixed responsibilities that should be split
- confusing naming
- repeated logic that can be safely consolidated
- public API leakage caused by poor `__init__.py` exports

#### Documentation and proofreading
- unclear docstrings or comments
- typos in names, comments, user-facing messages, or log text
- comments that explain the obvious instead of the non-obvious
- missing brief docstrings on public-facing code where helpful

#### Logging and observability
- use of module-level logger pattern where logging exists
- absence of useful operational context on meaningful logs
- accidental logging of sensitive or noisy payloads
- missing diagnostics around external I/O or failure paths where appropriate

#### Testing quality
- missing unit coverage for changed behavior
- weak assertions tied to implementation details instead of outcomes
- missing regression tests for discovered bugs
- test layout drift from the source structure

### 5. Decide what to improve
Prefer safe, high-value changes with clear justification.

Typical improvements:
- simplify branching or data flow
- tighten validation and exception handling
- extract helpers to reduce duplication
- split responsibilities when the file is too large or muddled
- improve names, docstrings, comments, and user-facing strings
- add or update focused tests
- fix import/export organization in `__init__.py`

Avoid unless explicitly requested:
- repository-wide style churn
- speculative abstractions
- cross-layer redesign unrelated to the target
- broad renames outside the audit scope

### 6. Implement changes in a controlled order
Recommended execution order:
1. add or update regression tests first when fixing a specific bug
2. make focused source changes in the target module
3. update related exports or helper modules if the structure changes
4. update docs only when behavior, usage, or structure meaningfully changes

### 7. Validate the result
Run focused checks early, then the full quality gate before handoff.

Focused examples:
```bash
pytest tests/unit/adapters/output/parsers/test_k6_parsed_report_parser.py
pytest tests/unit/adapters/output/narrative/test_structured_llm_adapter.py
```

Required full validation before handoff:
```bash
ruff format .
ruff check . --fix
ruff check .
mypy src/ tests/
pytest tests/
```

### 8. Report the audit outcome clearly
Summarize both what you found and what you changed.

Include:
- target module audited
- key issues found
- changes made
- tests added or updated
- validation performed
- any intentionally deferred issues or wider refactors left out of scope

## Expected deliverables

### If the user asked for an audit only
Provide:
- a concise findings summary
- prioritized improvement recommendations
- risk notes
- suggested next steps

### If the user asked you to improve the module
Provide:
- implemented fixes/refactors
- updated tests
- short explanation of why each change matters
- validation evidence

## Audit checklist
- [ ] Target module/path is clearly identified
- [ ] Related tests and boundary files were inspected
- [ ] Architecture/layer compliance was checked
- [ ] Naming, structure, docs, logging, and error handling were reviewed
- [ ] Safe, scoped improvements were applied or proposed
- [ ] Tests were updated when behavior changed
- [ ] Full local quality gate was run before handoff

## Example prompts

### Example 1: adapter package audit
"Audit `src/qa_report_generator/adapters/output/parsers/k6_parsed_report/`, improve the design where needed, proofread user-facing text, and update tests if behavior changes."

### Example 2: single module audit
"Review `src/qa_report_generator/adapters/input/cli_adapter/adapter.py` for code quality, architecture compliance, and readability, then make safe improvements."

### Example 3: findings-first audit
"Audit `src/qa_report_generator/adapters/output/narrative/structured_llm/` and first tell me what you would change before editing anything."
