#!/bin/bash
# Deploy the run board to Cloudflare Pages.
# Usage: bash deploy.sh
# Requires: /Users/I552240/Downloads/randomAIExperiments/hermes-recruiter-agency/.env with
#   CLOUDFLARE_API_TOKEN=...
#   CLOUDFLARE_ACCOUNT_ID=...

set -e

cd "$(dirname "$0")"

if [ ! -d node_modules ]; then
  echo "Installing deps..."
  npm install --legacy-peer-deps
fi

echo "Building..."
npm run build

# Load CF creds from repo root .env
ENV_FILE="../.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE"
  exit 1
fi

CF_TOKEN=$(grep '^CLOUDFLARE_API_TOKEN=' "$ENV_FILE" | cut -d= -f2-)
CF_ACCOUNT=$(grep '^CLOUDFLARE_ACCOUNT_ID=' "$ENV_FILE" | cut -d= -f2-)

if [ -z "$CF_TOKEN" ] || [ -z "$CF_ACCOUNT" ]; then
  echo "CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID not set in $ENV_FILE"
  exit 1
fi

export CLOUDFLARE_API_TOKEN="$CF_TOKEN"
export CLOUDFLARE_ACCOUNT_ID="$CF_ACCOUNT"

PROJECT_NAME="hermes-recruiter"

# Ensure project exists (ignore error if it already does)
echo "Ensuring CF Pages project '$PROJECT_NAME' exists..."
npx --yes wrangler@latest pages project create "$PROJECT_NAME" --production-branch=main 2>/dev/null || echo "  (project already exists — continuing)"

echo "Deploying dist/ ..."
npx --yes wrangler@latest pages deploy dist --project-name="$PROJECT_NAME" --commit-dirty=true --branch=main
