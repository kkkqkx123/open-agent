# Modular Agent Framework Developer Guide

This document provides essential information for AI agents working with the Modular Agent Framework codebase.

## Project Overview

The Modular Agent Framework is a Python-based multi-agent system built on Graph Workflow, featuring:
- **Multi-model LLM integration** (OpenAI, Gemini, Anthropic, Mock)
- **Flexible tool system** supporting native, MCP, and built-in tools
- **Configuration-driven architecture** with YAML-based configs and environment variable injection
- **Layered architecture with clear separation**: Interfaces + Core + Services + Adapters + Infrastructure
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

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
or directly use `uv run python <...>`

# Install new dependencies
uv add <package-name>
```

## Development Commands

You can use the following commands to check code quality:

```bash
uv run mypy <relative path to the file> --follow-imports=silent
uv run flake8 <relative path to the file>
```

Usually mypy is sufficient. If not asked to use remaining tools, you can skip them.
If not asked to check whole codebase, always use `--follow-imports=silent` to avoid checking relative files.

**Testing**
```bash
uv run pytest <file-path or directory-path>

When test can't run, first you just need to test dependencies import. Usually you can use `from typing import TYPE_CHECKING` to avoid circular dependencies.
```

## Codebase Architecture

### Layered Architecture

The framework uses a balanced layered architecture that reduces complexity while maintaining functionality:

**Architecture**: Interfaces + Core + Services + Adapters + Infrastructure

### Layer Descriptions

**Interfaces Layer** (`src/interfaces/`)
- Centralized interface definitions serving as the foundation for all other layers
- Provides contracts for all major components: LLM, storage, workflow, sessions, etc.
- Contains no implementation details, only abstract definitions

**Core Layer** (`src/core/`)
- Contains domain entities, base classes, and core business logic
- Implements interfaces from the interfaces layer
- Includes core modules for configuration, tools, LLM, workflow, state management, sessions, threads, checkpoints, history, prompts, and storage
- Contains common utilities shared across the application

**Services Layer** (`src/services/`)
- Provides application services and business logic implementations
- Depends on core layer and interface layer
- Includes services for workflow, session, thread, checkpoint, history, LLM, tools, state management
- Contains dependency injection container, logging, and monitoring services

**Adapters Layer** (`src/adapters/`)
- Provides external interface adaptations
- Depends on core layer, service layer, and interface layer
- Includes adapters for storage, API, TUI, CLI, and repository implementations
- Handles integration with external systems and user interfaces

**Infrastructure Layer** (`src/infrastructure/`)
- Provides concrete implementations of external dependencies
- **Depends only on interfaces layer** - never depends on core, services, or adapters
- Includes infrastructure for cache, LLM (HTTP clients, converters), messages, and tools
- Implements low-level technical concerns

### Configuration System

The framework uses a hierarchical YAML-based configuration system with:
- **Configuration inheritance**: Group configurations with individual overrides
- **Environment variable injection**: Automatic resolution with `${ENV_VAR:DEFAULT}` format
- **Type-safe validation**: Strong type validation using Pydantic models
- **Multi-environment support**: Specific overrides for test, development, and production
- **Modular structure**: Separate configurations for LLMs, workflows, tools, prompts, etc.

## Layer Dependency Constraints

### Strict Dependency Rules

**Interfaces Layer**
- **Cannot depend on any other layer**
- Provides contracts that all other layers must implement
- Contains only abstract definitions and interfaces

**Infrastructure Layer**
- **Can only depend on interfaces layer**
- Cannot depend on core, services, or adapters layers
- Implements concrete versions of interfaces for external dependencies

**Core Layer**
- Can depend on interfaces layer
- **Cannot depend on services layer**
- Contains domain logic and entity implementations

**Services Layer**
- Can depend on interfaces layer and core layer
- Provides business logic and application services
- Coordinates between core components

**Adapters Layer**
- Can depend on interfaces layer, core layer, and services layer
- Provides external interface implementations
- Handles integration with external systems

### Dependency Flow

Infrastructure depends only on Interfaces. Core depends on Interfaces. Services depend on Interfaces and Core. Adapters depend on Interfaces, Core, and Services. All layers ultimately depend on Interfaces layer.

## Development Process

### 1. Feature Development
- Follow layered architecture constraints strictly
- Define interfaces in the interfaces layer first
- Implement entities and core logic in the core layer
- Implement business logic in the service layer
- Provide external interfaces in the adapter layer
- Implement infrastructure components depending only on interfaces
- Register services in the dependency container with appropriate lifecycle
- Use configuration files for customization with inheritance support
- Write unit and integration tests with appropriate mocking
- Ensure type annotations and follow Python 3.13+ type hints

### 2. Testing Strategy
- **Unit tests**: Core layer and service layer core business logic coverage ≥ 90%
- **Integration tests**: Module interaction and infrastructure component coverage ≥ 80%
- **Infrastructure tests**: Infrastructure layer implementation coverage ≥ 85%
- **End-to-end tests**: Complete workflow and user scenario coverage ≥ 70%

### 3. Code Quality Standards
- Use type annotations (enforced by mypy strict mode)
- Write complete docstrings with parameter and return type documentation
- Follow dependency injection pattern for all service instantiation
- Use configuration-driven approach for all external dependencies
- Infrastructure components must only depend on interface layer
- Implement proper abstraction layers to enable seamless replacement

### 4. Configuration Changes
- Use the configuration system API for configuration management
- Update group configuration in corresponding `_group.yaml` files
- Create specific `.yaml` configuration files with inheritance
- Validate using environment checker before deployment
- Ensure environment variable references use `${VAR:DEFAULT}` format
- Test configuration inheritance and environment variable resolution

### 5. Error Handling
- Use specific exception types from `src.interfaces.<module>.exceptions`
- Implement proper error propagation between layers
- Log errors with appropriate context and severity
- Provide meaningful error messages to users
- Handle configuration errors gracefully with fallback options

## Core Components Usage

### Container (Dependency Injection)
- Located in `src/services/container/`
- Manages service lifecycle: singleton, transient, scoped
- Use `container.register()` for service registration
- Resolve services via `container.resolve()`

### Logger
- Infrastructure: `src/infrastructure/logger/`
- Service: `src/services/logger/`
- Use structured logging with context
- Supports console, file, and JSON outputs

### Exceptions
- Module-specific exceptions in `src/interfaces/<module>/exceptions/`
- Use specific exception types for error handling
- Implement proper error propagation between layers

## Coding Specifications

Must follow mypy type specifications. Functions must be annotated with type hints.

### Interface Definition Location
- **All interface definitions must be placed in the centralized interface layer** (`src/interfaces/`)
- Core layer implements interfaces from the interface layer
- Services layer depends on interfaces from the interface layer
- Adapters layer implements or depends on interfaces from the interface layer
- Infrastructure layer implements interfaces from the interface layer only
- Scattered interface files across layers are not allowed

### Interface Usage Principles
1. **Single Source of Truth**: All interface definitions are centralized in `src/interfaces/` directory
2. **Type Safety**: Use `TYPE_CHECKING` to avoid runtime circular dependencies. For interfaces, type safety is not required.
3. **Unified Export**: Export all interfaces through `src/interfaces/__init__.py`
4. **Backward Compatibility**: Each layer can re-export interfaces from the interface layer for compatibility
5. **Infrastructure Isolation**: Infrastructure components must only depend on interfaces, never on concrete implementations from other layers

**Note: Sessions service module (Sessions is the top-level module in the service layer, workflow is the module for Graph interaction)**

## Language

Use Chinese in code and documentation. Use English in LLM-interact-related configuration files and code (mainly about prompts).