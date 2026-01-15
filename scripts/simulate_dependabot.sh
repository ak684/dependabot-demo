#!/bin/bash
# Simulate a Dependabot PR by updating dependencies and creating a PR
#
# Usage: ./scripts/simulate_dependabot.sh [--dry-run]
#
# This script:
# 1. Creates a new branch
# 2. Updates pyproject.toml with newer dependency versions
# 3. Creates a PR with Dependabot-style formatting
# 4. The PR triggers the OpenHands workflow due to 'dependencies' label
#
# Requirements:
# - gh CLI installed and authenticated
# - Git configured with push access

set -e

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 Dry run mode - no changes will be pushed"
fi

# Configuration
BRANCH_NAME="dependabot/pip/pydantic-2.10.0-$(date +%s)"
PR_TITLE="Bump pydantic from 1.10.7 to 2.10.0"
OLD_VERSION="1.10.7"
NEW_VERSION="2.10.0"

echo "📦 Simulating Dependabot dependency update..."
echo "   Package: pydantic"
echo "   From: $OLD_VERSION"
echo "   To: $NEW_VERSION"
echo ""

# Ensure we're on main and up to date
echo "🔄 Syncing with main branch..."
git checkout main
git pull origin main 2>/dev/null || true

# Create new branch
echo "🌿 Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

# Update pyproject.toml
echo "📝 Updating pyproject.toml..."

# Use sed to update the pydantic version
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS sed
    sed -i '' "s/pydantic==1.10.7/pydantic==$NEW_VERSION/" pyproject.toml
else
    # Linux sed
    sed -i "s/pydantic==1.10.7/pydantic==$NEW_VERSION/" pyproject.toml
fi

# Show the diff
echo ""
echo "📋 Changes made:"
git diff pyproject.toml
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo "🔍 Dry run - would create PR with title: $PR_TITLE"
    git checkout main
    git branch -D "$BRANCH_NAME"
    exit 0
fi

# Commit the change
echo "💾 Committing changes..."
git add pyproject.toml
git commit -m "deps: bump pydantic from $OLD_VERSION to $NEW_VERSION

Bumps [pydantic](https://github.com/pydantic/pydantic) from $OLD_VERSION to $NEW_VERSION.

This is a simulated Dependabot update for demo purposes."

# Push the branch
echo "🚀 Pushing branch to origin..."
git push -u origin "$BRANCH_NAME"

# Create the PR with Dependabot-style formatting
echo "📬 Creating Pull Request..."

PR_BODY="## Bumps [pydantic](https://github.com/pydantic/pydantic) from $OLD_VERSION to $NEW_VERSION.

<details>
<summary>Release notes</summary>

> Sourced from [pydantic's releases](https://github.com/pydantic/pydantic/releases).
>
> ## v2.10.0
>
> ### Breaking Changes
> - \`.dict()\` method renamed to \`.model_dump()\`
> - \`.parse_obj()\` renamed to \`.model_validate()\`
> - \`from_orm()\` renamed to \`model_validate()\` with \`from_attributes=True\`
> - \`class Config\` replaced with \`model_config = ConfigDict(...)\`
> - \`orm_mode\` renamed to \`from_attributes\`
> - \`@validator\` replaced with \`@field_validator\`
</details>

<details>
<summary>Changelog</summary>

> See [full changelog](https://github.com/pydantic/pydantic/blob/main/HISTORY.md)
</details>

---

**Note**: This is a simulated Dependabot update for demo purposes.

The OpenHands workflow will automatically:
1. Run tests to check for breaking changes
2. If tests fail, attempt to fix the code
3. Push fixes and request review"

gh pr create \
    --title "$PR_TITLE" \
    --body "$PR_BODY" \
    --label "dependencies" \
    --label "automated" \
    --base main

echo ""
echo "✅ Done! PR created successfully."
echo ""
echo "The OpenHands Dependabot workflow should now trigger automatically."
echo "Watch the Actions tab to see OpenHands analyze and fix the breaking changes!"
