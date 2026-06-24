# Contributing to SAM2 Annotation Tool

Thank you for your interest in contributing! This guide covers the basics.

## Getting Started

1. Fork the repository and clone your fork.
2. Create a virtual environment: python -m venv venv && source venv/bin/activate (Windows: env\Scripts\activate).
3. Install dependencies: pip install -r requirements.txt.
4. Download the SAM2 model weights from the [SAM2 official repo](https://github.com/facebookresearch/sam2) and update config.yaml.
5. Run python main.py to verify the application starts.

## Development Workflow

1. Create a branch: git checkout -b feature/your-feature-name.
2. Make your changes, keeping commits focused.
3. Add or update tests under 	ests/ for any new behavior.
4. Run tests: pytest tests/ -v.
5. Ensure no __pycache__ or model weights are committed.
6. Open a Pull Request with a clear description of what and why.

## Code Style

- Follow the existing snake_case naming for files, functions, and variables.
- Use PascalCase for class names.
- Keep docstrings concise; Chinese is acceptable for inline comments.
- Prefer the existing layered architecture: Presentation -> Business -> Engine -> Data.

## Reporting Issues

Use GitHub Issues. Include:
- OS and Python version
- Whether you are using GPU or CPU
- Steps to reproduce
- Error output (stack trace if available)

## License

By contributing you agree that your contributions are licensed under the MIT License.
