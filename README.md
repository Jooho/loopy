# Loopy

Loopy is an automation framework that allows you to create and run test scripts in your preferred programming language. It provides a unified CLI interface for managing and executing various automation tasks.

## Features

- **Multi-language Support**: Write scripts in your preferred language (Python, Shell, etc.)
- **Unified CLI**: Easy-to-use command-line interface for all operations
- **Script Management**: List, view, and execute scripts with detailed information
- **Parameter Support**: Pass parameters to scripts in KEY=VALUE format
- **Development Tools**: Built-in tools for debugging and development

## Quick Start

1. Clone the repository and initialize:

```bash
git clone https://github.com/Jooho/loopy.git
cd loopy
./loopy init
```

2. Make the CLI executable:

```bash
chmod +x loopy
```

For detailed documentation, please visit:

- [Concepts](docs/concept.md)
- [Quick Start Guide](docs/quickstart.md)
- [Functional Testing](docs/func_test.md)
- [Creating New Role](docs/creating_new_role.md)

## Project Structure

```
loopy/
├── src/
│   ├── cli/          # CLI implementation
│   ├── core/         # Core functionality
│   ├── dev/          # Development tools and scripts
│   └── commons/      # Common utilities
├── tests/            # Test files
├── docs/            # Documentation
└── hacks/           # Development and CI/CD scripts
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the terms of the license included in the repository.
