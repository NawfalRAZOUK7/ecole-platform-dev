# Domain Protocols

Python Protocol classes (PEP 544) defining structural typing interfaces. These enable duck-typing without inheritance coupling.

## Files

- **evaluatable.py** — Protocol for entities that can be evaluated/scored
- **grading.py** — Protocol for grading strategies (Moroccan 0-20 scale, letter grades, pass/fail)

## Pattern

Services depend on protocols rather than concrete classes, enabling strategy pattern and easier testing with mock implementations.
