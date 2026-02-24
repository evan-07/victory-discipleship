#!/bin/bash

# Configuration
TF_DIR="terraform"
EXIT_CODE=0

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: ./cost_sentinel.sh"
    echo "Scans Terraform files for expensive resources not compatible with Free Tier."
    exit 0
fi

# List of Banned Keywords (Expensive Resources)
# - NAT Gateway (~$30/mo base)
# - Load Balancer (~$18/mo base)
# - n1-standard (Not free tier eligible)
# - sql_tier (Standard tier is expensive, use db-f1-micro)
BANNED_TERMS=(
    "google_compute_router_nat"
    "google_compute_global_forwarding_rule"
    "n1-standard"
    "db-n1-standard"
    "PREMIUM"
)

echo "💰 Running Cost Sentinel on $TF_DIR..."

for term in "${BANNED_TERMS[@]}"; do
    # Grep recursively for the banned term
    MATCH=$(grep -r "$term" "$TF_DIR" --include=*.tf)
    
    if [ ! -z "$MATCH" ]; then
        echo "---------------------------------------------------"
        echo "🚨 VIOLATION DETECTED: Expensive Resource Found!"
        echo "   Term: '$term'"
        echo "   File context:"
        echo "$MATCH"
        echo "---------------------------------------------------"
        EXIT_CODE=1
    fi
done

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ [FINOPS PASS] No obviously expensive resources detected."
else
    echo "❌ [FINOPS FAIL] The agent attempted to provision paid resources."
    echo "   Action: Refuse this plan. Ask the agent to use Free Tier alternatives."
fi

exit $EXIT_CODE