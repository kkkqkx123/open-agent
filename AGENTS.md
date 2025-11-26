# Modular Agent Framework Developer Guide

This document provides essential information for AI agents working with the Modular Agent Framework codebase.

## Project Overview

The Modular Agent Framework is a Python-based multi-agent system built on LangGraph, featuring:
- **Multi-model LLM integration** (OpenAI, Gemini, Anthropic, Mock)
- **Flexible tool system** supporting native, MCP, and built-in tools
- **Configuration-driven architecture** with YAML-based configs and environment variable injection
- **LangGraph Studio integration** for visualization and debugging
- **Flattened architectural layers**: Core + Services + Adapters
- **Complete dependency injection** with multi-environment support
- **Real-time TUI interface** with rich components
- **RESTful API** for external integration
- **Session and thread management** with checkpoint persistence
- **Workflow engine** with ReAct and other patterns

## Development Environment Setup

### Prerequisites
- Python 3.13+
- uv (Python package manager) - install single package via `uv add`

### Environment Setup with uv

# Activate virtual environment
`.venv\Scripts\activate`  # Windows
or directely use `uv run python <...>`

# Install new dependencies
uv add 

```

## Development Commands
When you find environment issues, you can use uv run to execute python commands in the virtual environment, or use .venv\Scripts\activate to activate the virtual environment first.

You can use the following commands to check the code quality:

```bash
uv run mypy <relative path to the file> --follow-imports=silent
uv run flake8 <relative path to the file>
```

Usually mypy is enough. if I didn't ask you to use remaining tools, you can skip them
If I don't ask you to check whole codebase, always use --follow-imports=silent to avoid check relative files.


**test**
```bash
uv run pytest <file-path or directory-path>
```

## Codebase Architecture

### New Flattened Architecture

The framework has been redesigned from a traditional 4-layer architecture to a flattened structure that reduces complexity while maintaining functionality:

**Previous Architecture**: Entity → Application → Infrastructure → Presentation
**New Architecture**: Core + Services + Adapters

### Directory Structure
src/
├── interfaces/             # Interface layer (centralized interface definitions)
├── core/                   # Core module (domain logic + core infrastructure)
│   ├── config/             # Unified configuration system
│   ├── tools/              # Tool system core
│   ├── llm/                # LLM system core
│   ├── workflow/           # Workflow core
│   ├── state/              # State management core
│   ├── sessions/           # Session management core
│   ├── threads/            # Thread management core
│   ├── checkpoints/        # Checkpoint core
│   ├── history/            # History management core
│   ├── prompts/            # Prompt system core
│   ├── storage/            # Storage core
│   └── common/             # Common utilities
├── services/               # Service layer (application + partial infrastructure)
│   ├── workflow/           # Workflow service
│   ├── session/            # Session service
│   ├── thread/             # Thread service
│   ├── checkpoint/         # Checkpoint service
│   ├── history/            # History service
│   ├── llm/                # LLM service
│   ├── tools/              # Tool service
│   ├── state/              # State service
│   ├── container/          # Dependency injection container
│   ├── logger/             # Logging service
│   └── monitoring/         # Monitoring service
├── adapters/               # Adapter layer (external interfaces)
│   ├── storage/            # Storage adapter
│   ├── api/                # API adapter
│   ├── tui/                # TUI adapter
│   └── cli/                # CLI adapter
└── bootstrap.py            # Application startup entry point

### Core Infrastructure Components

1. **Unified Configuration System** (`src/core/config/`)
   - Simplified configuration manager integrating loading, processing and validation
   - Support for configuration inheritance and environment variable resolution
   - Type-safe configuration models (Pydantic)
   - Configuration caching and performance optimization
   - Configuration export and template generation

2. **Dependency Injection Container** (`src/services/container/`)
   - Manage service lifecycle (singleton, transient, scoped)
   - Support multi-environment bindings (dev, test, prod)
   - Automatic dependency resolution
   - Circular dependency detection and prevention
   - Performance monitoring and caching

3. **LLM Module** (`src/core/llm/` + `src/services/llm/`)
   - Core interfaces and entity definitions
   - Support multiple providers: OpenAI, Gemini, Anthropic, Mock
   - Connection pooling with configurable pool size
   - Intelligent failover mechanism
   - Token counting based on provider tokenizer

4. **Tool System** (`src/core/tools/` + `src/services/tools/`)
   - Core interfaces and factory patterns
   - Support native Python, MCP, and built-in tools
   - Dynamic tool discovery and registration
   - Tool execution management and error handling
   - Tool caching for performance optimization

5. **Workflow Engine** (`src/core/workflow/` + `src/services/workflow/`)
   - Core workflow entities and patterns
   - LangGraph integration and custom extensions
   - State management and serialization capabilities
   - Node registry for dynamic workflow composition
   - Graph execution with checkpoint persistence

6. **Session Management** (`src/core/sessions/` + `src/services/session/`)
   - Core session interfaces and entities
   - Session lifecycle management (create, update, delete)
   - Thread management and metadata tracking
   - Checkpoint persistence and recovery
   - Session state serialization

7. **History Management** (`src/core/history/` + `src/services/history/`)
   - Core history interfaces and storage
   - Complete conversation history persistence
   - Checkpoint management based on SQLite backend
   - History replay and analysis

8. **State Management** (`src/core/state/` + `src/services/state/`)
   - Core state interfaces and storage
   - State management with history and snapshots
   - SQLite backend persistence
   - Snapshot storage and recovery

9. **Thread Management** (`src/core/threads/` + `src/services/thread/`)
   - Core thread interfaces and entities
   - Thread storage and metadata management
   - Branch storage for thread branching
   - Snapshot storage for thread state saving

10. **Checkpoint Management** (`src/core/checkpoints/` + `src/services/checkpoint/`)
    - Core checkpoint interfaces and storage
    - Checkpoint storage and management
    - Memory and SQLite storage backends
    - Performance optimization

11. **Logging System** (`src/services/logger/`)
    - Multi-output logging (console, file, JSON)
    - Structured logging with rich formatting
    - Sensitive information redaction

12. **TUI Interface** (`src/adapters/tui/`)
    - Rich terminal user interface based on blessed
    - Real-time workflow visualization
    - Component-based UI architecture
    - Event-driven interaction model

13. **API Interface** (`src/adapters/api/`)
    - RESTful API based on FastAPI framework
    - WebSocket support for real-time communication
    - Authentication and authorization
    - Data access layer based on DAO pattern

14. **Performance Monitoring** (`src/services/monitoring/`)
    - Unified performance monitoring system
    - YAML-driven configuration
    - Performance metrics collection and reporting

### Configuration System

Configuration structure:
configs/
├── global.yaml          # Global settings (logging, keys, environment)
├── application.yaml     # Application-specific settings
├── history.yaml         # History and checkpoint configuration
├── prompts.yaml         # Prompt templates and system messages
├── monitoring.yaml      # Performance monitoring configuration
├── llms/                # Model configuration
│   ├── _group.yaml      # Model group configuration
│   ├── mock.yaml        # Mock LLM configuration
│   ├── test_no_function_calling.yaml
│   ├── provider/        # Provider-specific configuration
│   │   ├── anthropic/   # Anthropic models
│   │   ├── gemini/      # Gemini models
│   │   ├── human_relay/ # Human relay models
│   │   └── openai/      # OpenAI models
│   └── tokens_counter/  # Token counting configuration
├── nodes/               # Node configuration
├── prompts/             # Prompt templates and system messages
│   ├── rules/           # Prompt rules
│   ├── system/          # System prompts
│   └── user_commands/   # User command prompts
├── tool-sets/           # Tool set configuration
├── tools/               # Individual tool configuration
└── workflows/           # Workflow configuration

Key features:
- **Configuration inheritance**: Use `inherits_from` field for group configuration and individual overrides
- **Environment variable injection**: Automatic resolution with `${ENV_VAR:DEFAULT}` format
- **Validation**: Type-safe configuration validation using Pydantic models
- **Hot reload**: File watching support in development environment
- **Multi-environment**: Specific overrides for test, development, and production environments
- **Modular structure**: Layered configuration for easy maintenance
- **Type safety**: Strong type validation for all configuration options
- **Performance**: Caching and lazy loading for optimal performance

## Module Dependencies

Module dependencies:
Interface layer provides all interface definitions as the foundation constraints.
Core layer contains entities, base classes, and core logic, depending on interface layer.
Service layer depends on core layer and interface layer, providing specific business service implementations.
Adapter layer depends on core layer, service layer, and interface layer, providing external interface adaptations.
Dependency injection container provides service resolution for all layers.
Configuration system provides configuration support for all layers.
Logging and monitoring systems span across all layers.

### Dependency Flow

```
Adapters (API/TUI/CLI) → Services (Business Logic) → Core (Entities & Core Logic) → Interfaces (Abstract Contracts)
```

## Development Process

### 1. Feature Development
- Follow flattened architecture constraints (Interfaces-Core-Services-Adapters)
- Define interfaces and entities in the core layer
- Implement business logic in the service layer
- Provide external interfaces in the adapter layer
- Register services in the dependency container with appropriate lifecycle (singleton, transient, scoped)
- Use configuration files for customization, supporting inheritance and environment variable injection
- Write unit and integration tests with appropriate mocking
- Ensure type annotations and follow Python 3.13+ type hints
- Use dependency injection for all service dependencies
- Implement proper error handling using custom exception types

### 2. Testing Strategy
- **Unit tests**: Core layer and service layer core business logic coverage ≥ 90%
- **Integration tests**: Module interaction and infrastructure component coverage ≥ 80%
- **End-to-end tests**: Complete workflow and user scenario coverage ≥ 70%

### 3. Code Quality Standards
- Use type annotations (enforced by mypy strict mode)
- Write complete docstrings with parameter and return type documentation
- Follow dependency injection pattern for all service instantiation
- Use configuration-driven approach for all external dependencies

### 4. Configuration Changes
- Use the new configuration system API for configuration management
- Update group configuration in the corresponding `_group.yaml` file
- Create specific `.yaml` configuration files with inheritance
- Validate using environment checker before deployment
- Document new configuration options in configuration guide
- Ensure environment variable references use `${VAR:DEFAULT}` format
- Test configuration inheritance and environment variable resolution
- Update configuration validation schema when adding new options

### 5. Error Handling
- Use specific exception types from `src.core.common.exceptions`
- Implement proper error propagation between layers
- Log errors with appropriate context and severity
- Provide meaningful error messages to users
- Handle configuration errors gracefully with fallback options


## Coding Specifications
Must follow mypy type specifications. For example, functions must be annotated with type hints.

### Interface Definition Location
- **All interface definitions must be placed in the centralized interface layer** (`src/interfaces/`)
- Core layer implements interfaces from the interface layer
- Services layer depends on interfaces from the interface layer
- Adapters layer implements or depends on interfaces from the interface layer
- Scattered interface files across layers are not allowed

### Interface Usage Principles
1. **Single Source of Truth**: All interface definitions are centralized in `src/interfaces/` directory
2. **Type Safety**: Use `TYPE_CHECKING` to avoid runtime circular dependencies. For core external dependencies like langchain, type safety is not required.
3. **Unified Export**: Export all interfaces through `src/interfaces/__init__.py`
4. **Backward Compatibility**: Each layer can re-export interfaces from the interface layer for compatibility

**Note: Sessions service module (Sessions is the top-level module in the service layer, workflow is the module for LangGraph interaction)**

## Language
Use Chinese in code and documentation. Use English in LLM-interact-related configuration files and code(mainly about prompts).
