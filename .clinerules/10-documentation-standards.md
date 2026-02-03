# Documentation standards: clear, concise, no fluff

Use these rules to keep documentation helpful without being verbose.

## Module docstrings
- **One line** stating the module's purpose
- No bullet lists, feature descriptions, or implementation notes
- Examples belong in README or docstrings of specific functions

## Class docstrings
- **One line** stating what the class does
- Add a second sentence only if it clarifies a non-obvious distinction
- No feature lists or implementation details

## Method/function docstrings
- **Brief description**: One sentence; omit period for single sentences
- **Args**: `name: Brief description` (no "The" prefix, no full sentences)
- **Returns**: Brief description of what's returned
- **Raises**: Only document exceptions that callers should handle

## Inline comments
- Use sparingly for non-obvious logic only
- Prefer self-documenting code (clear names, simple logic)
- Never state the obvious

## What NOT to document in code
- ❌ Feature lists → belongs in README
- ❌ Architecture patterns → belongs in ADRs
- ❌ Performance claims → belongs in benchmarks/docs
- ❌ Marketing language ("rich", "powerful", "advanced")
- ❌ Redundant restatements of parameter names
