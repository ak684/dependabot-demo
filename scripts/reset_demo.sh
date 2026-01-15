#!/bin/bash
# Reset the demo repository to its initial state
#
# Usage: ./scripts/reset_demo.sh
#
# This script:
# 1. Closes any open dependency PRs
# 2. Deletes dependabot/* branches
# 3. Ensures pyproject.toml has the old dependency versions
# 4. Resets any code changes back to v1 syntax

set -e

echo "🔄 Resetting demo repository to initial state..."
echo ""

# Ensure we're on main
git checkout main
git pull origin main 2>/dev/null || true

# Close open dependency PRs
echo "📬 Closing open dependency PRs..."
open_prs=$(gh pr list --label dependencies --json number --jq '.[].number' 2>/dev/null || echo "")
if [[ -n "$open_prs" ]]; then
    for pr_num in $open_prs; do
        echo "   Closing PR #$pr_num"
        gh pr close "$pr_num" --delete-branch 2>/dev/null || true
    done
else
    echo "   No open dependency PRs found"
fi

# Delete any remaining dependabot branches
echo ""
echo "🌿 Cleaning up dependabot branches..."
remote_branches=$(git branch -r | grep 'origin/dependabot/' | sed 's/origin\///' || true)
if [[ -n "$remote_branches" ]]; then
    for branch in $remote_branches; do
        echo "   Deleting $branch"
        git push origin --delete "$branch" 2>/dev/null || true
    done
else
    echo "   No dependabot branches found"
fi

# Clean up local branches
git fetch --prune

# Reset pyproject.toml to original versions
echo ""
echo "📦 Resetting dependencies to original versions..."

# Check if pyproject.toml needs updating
if grep -q "pydantic==2" pyproject.toml 2>/dev/null; then
    echo "   Reverting pydantic to 1.10.7"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' 's/pydantic==2\.[0-9.]*"/pydantic==1.10.7"/' pyproject.toml
    else
        sed -i 's/pydantic==2\.[0-9.]*"/pydantic==1.10.7"/' pyproject.toml
    fi

    git add pyproject.toml
    git commit -m "chore: reset dependencies for demo" || true
    git push origin main || true
fi

echo ""
echo "✅ Demo reset complete!"
echo ""
echo "The repository is now ready for another demo run."
echo "Run ./scripts/simulate_dependabot.sh to start a new demo."
