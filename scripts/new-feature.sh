#!/usr/bin/env bash
set -e

NAME=$1

if [ -z "$NAME" ]; then
  echo "Usage: ./scripts/new-feature.sh <feature-name>"
  exit 1
fi

git checkout dev && git pull
git checkout -b feat/$NAME
echo "Branch feat/$NAME created from dev."
