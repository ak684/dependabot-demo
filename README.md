# TaskFlow API - OpenHands Dependabot Demo

A demonstration of **OpenHands** automatically fixing breaking changes caused by dependency updates.

## What This Demo Shows

When Dependabot (or a simulated update) bumps a dependency to a new major version:

1. **Tests fail** due to breaking API changes
2. **OpenHands automatically** analyzes the failures
3. **OpenHands fixes the code** to work with the new dependency version
4. **OpenHands commits the fix** and updates the PR
5. **Tests pass** and the PR is ready for review

This demo specifically showcases the **Pydantic v1 to v2 migration**, which involves:
- `.dict()` → `.model_dump()`
- `.parse_obj()` → `.model_validate()`
- `from_orm()` → `model_validate()`
- `class Config` → `model_config = ConfigDict(...)`
- `orm_mode` → `from_attributes`
- `@validator` → `@field_validator`

## Quick Start - Running the Demo

### Option 1: Manual Trigger via GitHub UI

1. Go to **Actions** → **Simulate Dependabot Update**
2. Click **Run workflow**
3. Select `pydantic` as the package
4. Click **Run workflow**
5. Watch the magic happen!

### Option 2: Trigger via curl

```bash
# Set your GitHub token
export GITHUB_TOKEN=your_token

# Trigger the simulation
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/YOUR_ORG/dependabot-demo/actions/workflows/simulate-dependabot.yml/dispatches" \
  -d '{"ref":"main"}'
```

### Option 3: Using gh CLI

```bash
gh workflow run simulate-dependabot.yml --field package=pydantic
```

### Option 4: Local script

```bash
./scripts/simulate_dependabot.sh
```

## Demo Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEMO WORKFLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. TRIGGER                                                      │
│     ┌──────────────┐                                            │
│     │ curl/gh/UI   │ ──triggers──▶ simulate-dependabot.yml      │
│     └──────────────┘                                            │
│                                                                  │
│  2. DEPENDENCY UPDATE                                            │
│     ┌──────────────┐      ┌─────────────────┐                   │
│     │ Workflow     │ ───▶ │ Creates PR with │                   │
│     │ updates deps │      │ pydantic 2.x    │                   │
│     └──────────────┘      └─────────────────┘                   │
│                                    │                             │
│                                    ▼                             │
│  3. CI RUNS                                                      │
│     ┌──────────────┐      ┌─────────────────┐                   │
│     │ CI workflow  │ ───▶ │ Tests FAIL! ❌  │                   │
│     │ runs tests   │      │ (v1 syntax)     │                   │
│     └──────────────┘      └─────────────────┘                   │
│                                    │                             │
│                                    ▼                             │
│  4. OPENHANDS ACTIVATES                                          │
│     ┌──────────────┐      ┌─────────────────┐                   │
│     │ OpenHands    │ ───▶ │ Analyzes test   │                   │
│     │ workflow     │      │ failures        │                   │
│     └──────────────┘      └─────────────────┘                   │
│                                    │                             │
│                                    ▼                             │
│  5. AUTOMATED FIX                                                │
│     ┌──────────────┐      ┌─────────────────┐                   │
│     │ OpenHands    │ ───▶ │ Updates code to │                   │
│     │ fixes code   │      │ v2 syntax       │                   │
│     └──────────────┘      └─────────────────┘                   │
│                                    │                             │
│                                    ▼                             │
│  6. SUCCESS                                                      │
│     ┌──────────────┐      ┌─────────────────┐                   │
│     │ Commits fix  │ ───▶ │ Tests PASS! ✅  │                   │
│     │ to PR        │      │ PR ready        │                   │
│     └──────────────┘      └─────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
dependabot-demo/
├── src/
│   ├── api/
│   │   ├── routes.py       # FastAPI endpoints
│   │   └── schemas.py      # Pydantic schemas (v1 syntax!)
│   ├── models/
│   │   ├── base.py         # SQLAlchemy setup
│   │   ├── user.py         # User model
│   │   └── task.py         # Task model
│   ├── services/
│   │   ├── user_service.py # User business logic
│   │   └── task_service.py # Task business logic
│   ├── utils/
│   │   └── helpers.py      # Utility functions
│   └── main.py             # FastAPI app entry point
├── tests/
│   ├── unit/
│   │   ├── test_schemas.py   # Schema tests (v1 syntax!)
│   │   └── test_services.py  # Service tests
│   └── integration/
│       └── test_api.py       # API integration tests
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # CI pipeline
│   │   ├── openhands-dependabot.yml  # OpenHands auto-fix
│   │   └── simulate-dependabot.yml   # Demo trigger
│   └── dependabot.yml               # Dependabot config
├── scripts/
│   ├── simulate_dependabot.sh  # Local demo trigger
│   ├── reset_demo.sh           # Reset for re-demo
│   └── trigger_via_curl.sh     # curl trigger example
├── pyproject.toml              # Dependencies (old versions!)
└── README.md
```

## Setup Requirements

### For the GitHub Repository

1. **Secrets needed** (Settings → Secrets → Actions):
   - `LLM_API_KEY`: Your Anthropic/OpenAI API key
   - `LLM_MODEL`: (optional) Model to use, defaults to `anthropic/claude-sonnet-4-20250514`

2. **Permissions** (Settings → Actions → General):
   - Enable "Read and write permissions" for GITHUB_TOKEN
   - Enable "Allow GitHub Actions to create and approve pull requests"

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies (with old versions for demo)
pip install -e ".[dev]"

# Run tests (should pass with v1 pydantic)
pytest tests/ -v

# Run the API locally
uvicorn src.main:app --reload
```

## Key Files for the Demo

### `src/api/schemas.py`
Contains Pydantic v1 syntax that will break:
- Uses `.dict()` method
- Uses `class Config` with `orm_mode`
- Uses `@validator` decorator
- Uses `.from_orm()` and `.parse_obj()`

### `tests/unit/test_schemas.py`
Tests specifically exercise v1 features:
- Tests `.dict()` method
- Tests `from_orm()`
- Tests `parse_obj()`

### `.github/workflows/openhands-dependabot.yml`
The OpenHands integration that:
- Detects Dependabot/dependency PRs
- Runs tests to check for failures
- Invokes OpenHands to fix breaking changes
- Commits fixes back to the PR

## Resetting the Demo

After running the demo, reset for another run:

```bash
./scripts/reset_demo.sh
```

This will:
1. Close any open dependency PRs
2. Delete dependabot branches
3. Reset pyproject.toml to old versions

## Real-World Application

While this is a demo, the same workflow works for real Dependabot updates:

1. **Enable Dependabot** on any repository
2. **Add the `openhands-dependabot.yml` workflow**
3. **Configure secrets** with your LLM API key
4. When Dependabot creates PRs, OpenHands will automatically fix any breaking changes

## Troubleshooting

### Tests don't fail after update
The pyproject.toml may already have new versions. Run `./scripts/reset_demo.sh`.

### OpenHands doesn't trigger
Check that:
- PR has the `dependencies` label
- Workflow has correct permissions
- `LLM_API_KEY` secret is set

### OpenHands fails to fix
Check the workflow logs. Common issues:
- API key invalid or rate limited
- Complex changes requiring manual intervention
- Timeout (increase `max-iterations` if needed)

## License

MIT License - See LICENSE file for details.
