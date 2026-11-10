# Configuration

This directory contains repository-level configuration templates and contracts:

- `.env.example`: copy to the repository root as `.env` for local or Docker Compose use.
- `robot_capabilities.json`: approved closed-world robot API and safety contract used by generation and remote execution validation.

Keep secrets in the untracked root `.env`; do not add credentials to either file in this directory.
