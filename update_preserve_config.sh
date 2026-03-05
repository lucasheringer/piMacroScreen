#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PRESERVE_FILES=("config.json" "auth.json")
CURRENT_UID="$(id -u)"
CURRENT_GID="$(id -g)"

copy_with_fallback() {
    local src="$1"
    local dst="$2"

    if cp -a "$src" "$dst" 2>/dev/null; then
        return 0
    fi

    if command -v sudo >/dev/null 2>&1; then
        echo "  - retrying copy with sudo for $dst"
        sudo cp -a "$src" "$dst"
        sudo chown "$CURRENT_UID:$CURRENT_GID" "$dst"
        chmod u+rw "$dst" || true
        return 0
    fi

    return 1
}

fix_root_owned_pycache() {
    local found=0

    while IFS= read -r -d '' dir; do
        found=1
        echo "  - fixing ownership: $dir"
        sudo chown -R "$CURRENT_UID:$CURRENT_GID" "$dir"
    done < <(find . -type d -name '__pycache__' -print0)

    if [[ "$found" -eq 0 ]]; then
        return 0
    fi
}

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
        copy_with_fallback "$file" "$backup_dir/$file"
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
        copy_with_fallback "$backup_dir/$file" "$file"
        echo "  - restored $file"
    done
fi

if command -v sudo >/dev/null 2>&1; then
    echo "Checking for root-owned __pycache__ directories..."
    fix_root_owned_pycache || true
fi

echo "Update complete. Preserved files remain local:"
for file in "${PRESERVE_FILES[@]}"; do
    [[ -e "$file" ]] && echo "  - $file"
done

echo "Tip: run 'git status --short' to confirm your local config/auth overrides are present."
