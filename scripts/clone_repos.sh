#!/usr/bin/env bash
set -euo pipefail

mkdir -p repos
cd repos

while read -r repo; do
  [ -z "$repo" ] && continue
  if [ -d "$(basename "$repo")" ]; then
    echo "Skipping $repo (already cloned)"
    continue
  fi
  git clone "https://github.com/$repo.git"
done < ../data/repo_list.txt
