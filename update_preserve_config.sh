#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PRESERVE_FILES=("config.json" "auth.json")

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: this script must run inside a git repository."
    exit 1
fi

if [[ "$#" -eq 0 ]]; then
    PULL_ARGS=("--ff-only")
else
    PULL_ARGS=("$@")
fi

backup_dir="$(mktemp -d)"
backed_up_files=()

cleanup() {
    rm -rf "$backup_dir"
}
trap cleanup EXIT

echo "Checking for local changes outside preserved files..."
non_preserved_changes="$(git status --porcelain -- . ':(exclude)config.json' ':(exclude)auth.json')"
if [[ -n "$non_preserved_changes" ]]; then
    echo "Abort: you have local changes in files other than preserved config files:"
    echo "$non_preserved_changes"
    echo "Commit/stash those changes first, then run this script again."
    exit 1
fi

echo "Backing up preserved files..."
for file in "${PRESERVE_FILES[@]}"; do
    if [[ -e "$file" ]]; then
        mkdir -p "$backup_dir/$(dirname "$file")"
        cp -a "$file" "$backup_dir/$file"
        backed_up_files+=("$file")
        echo "  - backed up $file"
    fi
done

echo "Pulling latest changes: git pull ${PULL_ARGS[*]}"
git pull "${PULL_ARGS[@]}"

if [[ "${#backed_up_files[@]}" -gt 0 ]]; then
    echo "Restoring preserved files..."
    for file in "${backed_up_files[@]}"; do
        mkdir -p "$(dirname "$file")"
        cp -a "$backup_dir/$file" "$file"
        echo "  - restored $file"
    done
fi

echo "Update complete. Preserved files remain local:"
for file in "${PRESERVE_FILES[@]}"; do
    [[ -e "$file" ]] && echo "  - $file"
done

echo "Tip: run 'git status --short' to confirm your local config/auth overrides are present."
