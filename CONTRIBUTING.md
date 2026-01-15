# Contributing to ultraplan

Thank you for your interest in contributing to ultraplan!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ultraplan.git
   cd ultraplan
   ```
3. Install development dependencies:
   ```bash
   uv sync --extra dev
   ```

## Development Workflow

### Running the CLI

```bash
uv run ultraplan record
uv run ultraplan setup
```

### Running Tests

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check src/
uv run ruff format src/
```

## Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure:
   - Tests pass (`uv run pytest`)
   - Code is formatted (`uv run ruff format src/`)
   - No lint errors (`uv run ruff check src/`)

3. Commit your changes with a clear message:
   ```bash
   git commit -m "Add feature: description of change"
   ```

4. Push and open a Pull Request

## Code Style

- Follow existing code patterns
- Use type hints for function signatures
- Add docstrings for public functions
- Keep functions focused and reasonably sized

## Reporting Issues

When reporting bugs, please include:

- Operating system and version
- Python version (`python --version`)
- Steps to reproduce
- Expected vs actual behavior
- Any error messages

## Feature Requests

Feature requests are welcome! Please open an issue describing:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

## Questions?

Feel free to open an issue for questions or discussion.
