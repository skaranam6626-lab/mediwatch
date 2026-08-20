#!/bin/bash
# Promote the trained model to the production artifact path.
set -e

if [ -z "$HOME_PATH" ]; then
    HOME_PATH="$(pwd)"
fi

cd "$HOME_PATH"

STAGING_MODEL="${MODEL_FILE:-$HOME_PATH/output/mediwatch.joblib}"
PRODUCTION_MODEL="${PRODUCTION_MODEL_FILE:-$HOME_PATH/output/mediwatch_production.joblib}"
DEPLOYMENT_MANIFEST="${DEPLOYMENT_MANIFEST:-$HOME_PATH/output/deployment.json}"

if [ ! -f "$STAGING_MODEL" ]; then
    echo "Staging model not found: $STAGING_MODEL"
    exit 1
fi

mkdir -p "$(dirname "$PRODUCTION_MODEL")"
cp "$STAGING_MODEL" "$PRODUCTION_MODEL"

# Webapp reads MODEL_FILE; keep serving path in sync with production artifact.
#cp "$STAGING_MODEL" "$HOME_PATH/output/mediwatch.joblib"

cat > "$DEPLOYMENT_MANIFEST" <<EOF
{
  "deployed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "staging_model": "$STAGING_MODEL",
  "production_model": "$PRODUCTION_MODEL",
  "serving_model": "$HOME_PATH/output/mediwatch.joblib",
  "deployed_by": "airflow"
}
EOF

echo "Model deployed to $PRODUCTION_MODEL"
echo "Deployment manifest written to $DEPLOYMENT_MANIFEST"
