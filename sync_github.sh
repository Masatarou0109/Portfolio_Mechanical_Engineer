#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

branch="$(git branch --show-current)"
message="${1:-Update portfolio projects}"

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "Git remote 'origin' is not set."
  echo "Run: git remote add origin <your-github-repository-url>"
  exit 1
fi

git add .gitignore README.md resume automated-cae-design-review-tool coaster-bearing-thermal-lab thermal-resistance-network-optimizer

if git diff --cached --quiet; then
  echo "No portfolio project changes to commit."
  exit 0
fi

git commit -m "$message"
git push -u origin "$branch"
