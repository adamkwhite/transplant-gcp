# Changelog

All notable changes to the Transplant Medication Adherence project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Task 1.0: Install and configure Google ADK
- Task 2.0: Implement Core Agent Classes (4 ADK agents)
- Task 3.0: Build Multi-Agent Communication Layer
- Task 4.0: Create Backward-Compatible REST API
- Task 5.0: Deploy agents to Cloud Run
- Task 6.0: Testing and Validation
- Task 7.0: Documentation and Demo Preparation

## [1.0.0] - 2025-10-29

### Added
- **Repository Setup & Best Practices**
  - Pre-commit hooks with Ruff, mypy, Bandit, Safety, conventional commits
  - Python 3.12 configuration via pyproject.toml
  - Makefile with development commands (lint, format, typecheck, security)
  - GitHub Actions CI/CD workflows for automated testing and security scanning
  - Dependabot configuration for automated dependency updates
  - Comprehensive .gitignore with ADK and Cloud Run specific exclusions

- **Code Quality Tools**
  - SonarCloud integration (organization: adamkwhite, project: adamkwhite_transplant-gcp)
  - Static analysis with mypy (type checking)
  - Code formatting with Ruff
  - Security scanning with Bandit and Safety

- **Security Improvements**
  - GitHub Actions pinned to full commit SHA hashes for supply chain security
  - Updated gunicorn from 21.2.0 to >=23.0.0 (fixes CVE-2024-6827, CVE-2024-1135)
  - Updated flask-cors from 4.0.0 to >=4.0.2 (fixes CVE-2024-6221, CVE-2024-1681, CVE-2024-6839, CVE-2024-6866)
  - Secret scanning with Gitleaks

- **Project Documentation**
  - PRD for ADK multi-agent migration at docs/features/adk-multi-agent-migration-PLANNED/
  - Detailed task breakdown (103 subtasks across 8 major tasks)
  - Implementation status tracking document
  - AI documentation templates (create-prd.md, generate-tasks.md, process-task-list.md)

- **GitHub Repository**
  - Created repository: https://github.com/adamkwhite/transplant-gcp
  - Configured branch protection with CI/CD checks
  - Set up SonarCloud project integration

### Changed
- **Code Quality Refactoring**
  - Extracted duplicate string literals to constants (GEMINI_FLASH_MODEL, PLATFORM_NAME)
  - Added type annotations for Optional[GenerativeModel] in GeminiClient
  - Fixed None checks to match actual model usage (model vs flash_model)
  - Updated all Python code to comply with Python 3.12 standards

- **CI/CD Configuration**
  - Removed Python 3.11 from test matrix (project requires >=3.12)
  - Updated artifact upload conditions to use Python 3.12
  - Configured SonarCloud to skip tests directory until tests are added

### Fixed
- Resolved 7 security vulnerabilities in dependencies (gunicorn, flask-cors)
- Fixed bare except clause in services/missed-dose/main.py (E722)
- Resolved mypy type errors with proper Optional type annotations
- Fixed Ruff configuration format (migrated to lint.* sections)
- Added nosec B104 comment for Cloud Run host binding requirement

### Technical Details

#### Architecture Decision
- **Target**: Multi-agent system using Google Agent Development Kit (ADK)
- **Pattern**: Coordinator/Dispatcher with 4 specialized agents:
  1. TransplantCoordinator (routing agent)
  2. MedicationAdvisor (missed dose analysis)
  3. SymptomMonitor (rejection detection)
  4. DrugInteractionChecker (medication safety)

#### Technology Stack
- **Language**: Python 3.12
- **Framework**: Google ADK 1.17.0+ (to be installed in Task 1.0)
- **LLM**: Gemini 2.0 Flash for all 4 agents
- **Database**: Google Firestore
- **Deployment**: Google Cloud Run (4 separate services)
- **Code Quality**: Ruff, mypy, Bandit, Safety, SonarCloud
- **CI/CD**: GitHub Actions

#### Development Workflow
- Branch strategy: Feature branches with PR reviews
- Commit convention: Conventional Commits (enforced via pre-commit)
- PR checks: lint, typecheck, test, security, SonarCloud
- Merge strategy: Squash and merge to main

### Known Issues
- SonarCloud reports 15.5% code duplication (services/missed-dose/ contains legacy code)
  - Will be addressed during Task 2.0 ADK agent refactor
  - Legacy directory will be deprecated after multi-agent migration
- No tests directory yet (tests will be added in Task 6.0)
- SonarCloud automatic analysis was disabled (CI-based analysis only)

### Migration Notes
- **From**: Single-service Gemini client architecture
- **To**: Multi-agent ADK system with parallel execution
- **Timeline**: 6 days implementation (Nov 4 deadline for hackathon submission)
- **Backward Compatibility**: Existing REST endpoints preserved

### Contributors
- Adam White (adamkwhite)
- Claude AI (code generation and assistance)

---

## Release Notes

### Version 1.0.0 - Repository Foundation
This release establishes the foundational infrastructure for the Transplant Medication Adherence multi-agent system. All development tooling, CI/CD pipelines, security scanning, and code quality tools are now in place. The repository is ready for Task 1.0: Google ADK installation and configuration.

**Next Milestone**: Task 1.0 - Install and configure Google ADK (Estimated: Nov 5, 2025)
