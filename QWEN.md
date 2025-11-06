# Open-Agent Framework - QWEN Context Documentation

## Project Overview

Open-Agent is a sophisticated modular agent framework built in Python 3.13+, designed for creating multi-agent systems with LangGraph integration. The framework follows a clean architectural pattern with clear separation of concerns and supports multi-model LLM integration (OpenAI, Gemini, Anthropic, Mock), flexible tool systems, configuration-driven architecture, and provides both TUI and API interfaces.

### Key Features
- Multi-model LLM integration (OpenAI, Gemini, Anthropic, Mock)
- Flexible tool system supporting native, MCP, and built-in tools
- Configuration-driven architecture with YAML-based configs and environment variable injection
- LangGraph Studio integration for visualization and debugging
- Clean architectural layers: Domain → Application → Infrastructure → Presentation
- Complete dependency injection with multi-environment support
- Real-time TUI interface with rich components
- RESTful API for external integration
- Session and thread management with checkpoint persistence
- Workflow engine with ReAct and other patterns

## Architecture

The project follows a hexagonal architecture pattern with clear layer separation:

```
Presentation Layer (TUI/API/CLI) → Application Layer → Domain Layer → Infrastructure Layer
```

### Layer Descriptions

1. **Domain Layer**: Contains business logic and entities with no dependencies on other layers
   - Core business entities and value objects
   - Domain services and repositories interfaces
   - Business rules and validation logic

2. **Infrastructure Layer**: Technical implementations that depend only on domain
   - Configuration systems
   - LLM integration
   - Tool systems
   - Database/storage implementations
   - Logger implementations
   - State management

3. **Application Layer**: Use cases and workflows that depend on domain and infrastructure
   - Service orchestrations
   - Application services
   - Workflow management
   - Session management

4. **Presentation Layer**: UI and API interfaces that depend on all other layers
   - Terminal User Interface (TUI)
   - RESTful API
   - Command Line Interface (CLI)

## Directory Structure

The project is organized in a modular structure to maintain separation of concerns:

```
open-agent/
├── .venv/                    # Virtual environment directory (Git-ignored)
├── .vscode/                  # VS Code settings
├── configs/                  # Configuration files
│   ├── global.yaml           # Global settings
│   ├── application.yaml      # Application-specific settings
│   ├── history.yaml          # History and checkpoint configuration
│   ├── prompts.yaml          # Prompt templates
│   ├── threads.yaml          # Thread management configuration
│   ├── checkpoints/          # Checkpoint configurations
│   ├── graphs/               # Graph and workflow example configs
│   ├── hooks/                # Hook configurations
│   ├── llms/                 # Model configurations
│   ├── nodes/                # Node configurations
│   ├── prompts/              # Prompt templates and system messages
│   ├── tool-sets/            # Tool set configurations
│   ├── tools/                # Individual tool configurations
│   └── workflows/            # Workflow configurations
├── demo/                     # Example implementations
├── docs/                     # Documentation files
├── examples/                 # Usage examples
├── src/                      # Source code
│   ├── domain/               # Domain layer (business logic)
│   │   ├── agent/            # Agent domain models
│   │   ├── session/          # Session domain models
│   │   ├── thread/           # Thread domain models
│   │   └── value_objects/    # Value objects
│   ├── application/          # Application layer (use cases)
│   │   ├── agent/            # Agent application services
│   │   ├── session/          # Session application services
│   │   ├── thread/           # Thread application services
│   │   └── workflow/         # Workflow application services
│   ├── infrastructure/       # Infrastructure layer (technical implementations)
│   │   ├── config/           # Configuration loading and validation
│   │   ├── container/        # Dependency injection container
│   │   ├── graph/            # LangGraph integration
│   │   ├── llm/              # LLM integration
│   │   ├── tools/            # Tool system
│   │   ├── logging/          # Logging implementation
│   │   ├── state/            # State management
│   │   └── utils/            # Utility functions
│   └── presentation/         # Presentation layer (UI/API)
│       ├── api/              # REST API
│       ├── cli/              # Command line interface
│       └── tui/              # Terminal user interface
├── tests/                    # Test files
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── e2e/                  # End-to-end tests
│   └── performance/          # Performance tests
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore patterns
├── AGENTS.md                # Agent system documentation
├── FLEXIBLE_CONTEXT_CONTROL.md # Flexible context control documentation
├── NODE_CONTEXT_PASSING.md  # Node context passing documentation
├── pyproject.toml           # Project configuration (dependencies, build settings)
├── QWEN.md                  # Context documentation (this file)
├── TEMPLATE_VARIABLE_EXTENSIONS.md # Template variable extensions documentation
├── TUI_LOGGER_REFACTOR_SUMMARY.md # TUI logger refactor summary
├── uv.lock                  # Dependency lock file
└── ...
```

## Module Division

The project is divided into functional modules that align with the clean architecture:

### Domain Layer Modules
- `domain.agent`: Core agent entities and business rules
- `domain.session`: Session management entities
- `domain.thread`: Thread entities and collaboration rules
- `domain.value_objects`: Immutable value objects used across the system

### Application Layer Modules
- `application.agent`: Agent orchestration and management
- `application.session`: Session workflow coordination
- `application.thread`: Thread interaction and collaboration
- `application.workflow`: Workflow execution and management

### Infrastructure Layer Modules
- `infrastructure.graph`: LangGraph integration and execution
- `infrastructure.tools`: Tool management and execution system
- `infrastructure.llm`: LLM integration and management
- `infrastructure.config`: Configuration loading and validation
- `infrastructure.container`: Dependency injection system
- `infrastructure.state`: State management and persistence

### Presentation Layer Modules
- `presentation.api`: REST API endpoints and controllers
- `presentation.tui`: Terminal user interface components
- `presentation.cli`: Command line interface commands

## Layer Division

The project strictly follows the clean architecture pattern with the following layer dependencies:

```
Presentation → Application → Domain ← Infrastructure
```

### Domain Layer (Innermost)
- Contains pure business logic with no external dependencies
- Defines entities, value objects, domain services, and repository interfaces
- Pure Python classes without framework dependencies
- Contains business rules and validation logic

### Application Layer (Business Rules)
- Orchestrates use cases and application workflows
- Coordinates between domain entities and infrastructure services
- Contains application-specific business rules
- Depends on domain but not on infrastructure

### Infrastructure Layer (External Concerns)
- Implements technical concerns and external integrations
- Provides implementations for repository interfaces defined in domain
- Handles database operations, external APIs, file systems
- Depends on domain but not on application or presentation

### Presentation Layer (User Interface)
- Handles user interaction and system interfaces
- TUI, CLI, and API interfaces
- Depends on all other layers
- Contains controllers and UI components

## Virtual Environment Usage

This project uses `uv` for package management and requires Python 3.13+. 
The virtual environment should be properly managed as follows:

### Prerequisites
- Python 3.13+
- uv package manager (install with `pip install uv`)

### Initial Setup
```bash
# Create virtual environment (creates .venv/ directory)
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install project dependencies
uv sync

# Install test dependencies
uv sync --extra test

# Install development dependencies
uv sync --extra dev
```

### Development Workflow
```bash
# Activate environment (do this for each new terminal session)
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Install new package (updates pyproject.toml and uv.lock)
uv add package_name

# Install new package for development only
uv add --group dev package_name

# Run application with activated environment
python src/run_tui.py

# Run tests
python -m pytest

# Deactivate environment when done
deactivate
```

### Environment Management Tips
- Always activate the virtual environment before running any Python commands
- The `.venv/` directory is Git-ignored, but dependencies are locked in `uv.lock`
- Other developers can recreate the exact same environment with `uv sync`
- Use `uv run command` to run commands in the virtual environment without activation
- Use `uv pip list` to see installed packages

## Configuration System

The framework uses a sophisticated configuration system with inheritance and environment variable injection:

### Configuration Structure
```
configs/
├── global.yaml          # Global settings (logging, secrets, environment)
├── application.yaml     # Application-specific settings
├── history.yaml         # History and checkpoint configuration
├── prompts.yaml         # Prompt templates and system messages
├── threads.yaml         # Thread management configuration
├── checkpoints/         # Checkpoint configurations
├── graphs/              # Graph and workflow example configurations
├── hooks/               # Hook configurations
├── llms/                # Model configurations
├── nodes/               # Node configurations
├── prompts/             # Prompt templates and system messages
├── tool-sets/           # Tool set configurations
├── tools/               # Individual tool configurations
└── workflows/           # Workflow configurations
```

### Configuration Inheritance
- Group configurations with individual overrides using `inherits_from` field
- Environment variable injection with `${ENV_VAR:DEFAULT}` format
- Pydantic models for configuration validation with type safety
- Hot reloading support in development
- Multi-environment support (test, development, production)

## Dependency Injection

The framework uses a sophisticated dependency injection container with:

### Features
- Service lifecycle management (singleton, transient, scoped)
- Multi-environment bindings (development, test, production)
- Automatic dependency resolution with type hints
- Circular dependency detection and prevention
- Performance monitoring and caching
- Dependency analysis and optimization

### Container Types
- `BaseDependencyContainer`: Basic DI container
- `EnhancedDependencyContainer`: Advanced container with:
  - Service instance caching
  - Performance monitoring
  - Dependency analysis
  - Scope management
  - Service tracking

### Usage Pattern
```python
from src.infrastructure.container import get_global_container

container = get_global_container()
service = container.get(IServiceType)
```

## Building and Running

### Prerequisites
- Python 3.13+
- uv (Python package manager)

### Environment Setup
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv sync

# Install test dependencies
uv sync --extra test
```

### Application Execution
```bash
# Run TUI application
python src/run_tui.py

# Run API server
python -m src.presentation.api.run_api

# Run CLI interface
python -m src.presentation.cli.main

# Run infrastructure demo
python demo_infrastructure.py
```

### Development Commands
```bash
# Install a package (use uv add to sync with uv.lock and pyproject.toml)
uv add package_name

# Type checking with mypy
mypy .
# or check specific file
mypy file_relative_path --follow-imports=silent

# Code formatting with black
black src/ tests/

# Import sorting with isort
isort src/ tests/

# Linting with flake8
flake8 src/ tests/

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Generate dependency graph
python -m src.infrastructure.graph.visualization

# Validate configuration files
python -m src.infrastructure.config_loader --validate
```

## Development Conventions

### Coding Standards
- Use Python 3.13+ with strict type annotations (enforced by mypy)
- Follow black formatting (line length: 88, Python 3.13+ target)
- Use isort for imports with black profile
- Pass flake8 linting
- Follow dependency injection patterns for all service instantiation
- Use configuration-driven approach for all external dependencies

### Architecture Adherence
- Follow layer constraints (Domain → Application → Infrastructure → Presentation)
- Register services in dependency container with appropriate lifecycle
- Use configuration files for customization with inheritance and environment variables
- Write unit and integration tests with proper mocking
- Implement proper error handling with custom exception types

### Error Handling
Use specific exception types from `src.infrastructure.exceptions`:
- `InfrastructureError` - Base exception
- `ServiceNotRegisteredError` - DI container issues
- `ServiceCreationError` - Service instantiation problems
- `CircularDependencyError` - Dependency cycle detection
- `ConfigurationError` - Config loading problems
- `EnvironmentCheckError` - Environment validation failures
- `ArchitectureViolationError` - Layer dependency violations

## Testing

### Test Strategy
- Unit tests: Coverage ≥ 90% for core business logic
- Integration tests: Coverage ≥ 80% for module interactions
- End-to-end tests: Coverage ≥ 70% for complete workflows

### Test Utilities
The framework provides `TestContainer` for integration testing:
```python
from src.infrastructure import TestContainer

with TestContainer() as container:
    # Setup test environment
    container.setup_basic_configs()
    
    # Get services for testing
    config_loader = container.get_config_loader()
    checker = container.get_environment_checker()
    
    # Test automatically cleans up
```

## Language and Localization

- Use Chinese in code and documentation
- Use English in config files and prompts sent to LLMs for better LLM understanding

## Key Components

### TUI Interface
- Rich terminal user interface with blessed library
- Real-time workflow visualization
- Interactive session management
- Component-based UI architecture
- Event-driven interaction model

### Workflow Engine
- LangGraph integration with custom extensions
- State management with serialization capabilities
- Node registry for dynamic workflow composition
- Graph execution with checkpoint persistence
- Workflow visualization and debugging support
- Hook system for workflow customization

### Session Management
- Session lifecycle management (create, update, delete)
- Thread management with metadata tracking
- Checkpoint persistence and restoration
- Session state serialization
- Event collection and replay capabilities
- Git integration for session versioning

### Tool System
- Support for native Python tools, MCP tools, and built-in tools
- Dynamic tool discovery and registration
- Schema validation and OpenAPI schema generation
- Tool execution management with error handling
- Tool caching for performance optimization

## File Structure Navigation

Key project directories:
- `src/domain/` - Business logic and entities
- `src/infrastructure/` - Technical implementations
- `src/application/` - Use cases and workflows
- `src/presentation/` - UI and API interfaces
- `configs/` - Configuration files
- `tests/` - Test files
- `demo/` - Example implementations

## Troubleshooting

### Common Issues
- MyPy errors: Often false alarms when packages are installed but not recognized; use `--follow-imports=silent` to check specific files
- Environment variable injection: Ensure proper format `${VAR:DEFAULT}` in configuration files
- Configuration inheritance: Check `inherits_from` field format in YAML files
- Dependency injection: Register services in the container with proper lifetime management

### Debugging
- TUI debugging: Set `TUI_DEBUG=1` environment variable to enable TUI debug mode
- Configuration debugging: Use `python -m src.infrastructure.config_loader --validate` to check configs
- Environment checking: Use `python -m src.infrastructure.env_check_command` to validate dependencies