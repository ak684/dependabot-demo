#!/bin/bash
# Trigger the Dependabot simulation via GitHub API (curl)
#
# Usage: ./scripts/trigger_via_curl.sh
#
# This script demonstrates how to trigger the demo via a simple curl command.
# It uses the GitHub API to trigger a workflow dispatch event.
#
# Requirements:
# - GITHUB_TOKEN environment variable set with repo access
# - Repository must exist on GitHub

set -e

# Configuration - update these for your repo
REPO_OWNER="${GITHUB_REPO_OWNER:-All-Hands-AI}"
REPO_NAME="${GITHUB_REPO_NAME:-dependabot-demo}"

# Check for required token
if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "❌ Error: GITHUB_TOKEN environment variable is not set"
    echo ""
    echo "Set it with: export GITHUB_TOKEN=your_github_token"
    exit 1
fi

echo "🚀 Triggering Dependabot simulation workflow..."
echo "   Repository: $REPO_OWNER/$REPO_NAME"
echo ""

# Trigger the workflow dispatch
# Note: This requires a workflow_dispatch trigger in the workflow file
curl -X POST \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/simulate-dependabot.yml/dispatches" \
    -d '{"ref":"main"}'

echo "✅ Workflow triggered!"
echo ""
echo "Check the Actions tab to see the workflow running:"
echo "https://github.com/$REPO_OWNER/$REPO_NAME/actions"
