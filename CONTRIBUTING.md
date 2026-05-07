# Contributing

## Getting Started

1. Fork the repository
2. Create a branch: `git checkout -b your-branch-name`
3. Make your changes
4. Open a Pull Request against `main`

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| New design | `design/<topic>` | `design/vending-machine` |
| Fix/improvement | `fix/<topic>` | `fix/parking-lot-thread-safety` |

## PR Guidelines

- One design problem per PR
- Include a `design.py` and a `Readme.md` in the folder
- Keep `Readme.md` consistent with the existing format (Problem Statement, Class Overview, etc.)
- Do not modify unrelated files

## Folder Structure

Each design lives in its own folder:

```
Problem Name/
    design.py
    Readme.md
```
