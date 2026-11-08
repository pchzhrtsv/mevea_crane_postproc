# AGENTS.md

## Project Overview

This Python project is a collection of independent procedures for processing simulation results, analyzing data, and generating scientific visualizations.

**The project is not a standalone application.** Do not introduce unnecessary application architecture, frameworks, or dependencies.

## Agent Responsibilities

- Maintain a clear, logical project hierarchy and directory structure.
- Organize existing scripts and procedures by functionality.
- Develop new procedures according to user requests.
- Improve code readability, modularity, and maintainability.
- Reuse existing functions and dependencies where practical.
- Preserve compatibility with existing workflows.

## Data Integrity — Critical

- **Never modify, overwrite, or delete original simulation or calculation data without explicit user permission.**
- Any modification of original data requires **two separate user confirmations** before execution.
- Treat all source data as read-only by default.
- Save processed data and generated figures separately from original datasets.
- Never silently alter numerical values, units, or simulation parameters.

## Development Guidelines

- Prefer simple, independent Python scripts and reusable functions.
- Follow PEP 8 and use descriptive function and variable names.
- Avoid unnecessary abstractions and project restructuring.
- Document function inputs, outputs, and assumptions.
- Do not change existing calculation logic without user approval.
- Ask for clarification when requirements or data formats are ambiguous.

## Execution Rules

- Do not execute destructive operations without authorization.
- Validate procedures using temporary files or copied datasets.
- Clearly communicate proposed structural changes before applying significant modifications.
- Prioritize scientific reproducibility and preservation of existing results.