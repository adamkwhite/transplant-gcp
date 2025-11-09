#!/bin/bash
#
# Parse all 6 SRTR organ data files in parallel
#
# This script launches 6 parser processes simultaneously,
# one for each organ type. Each writes to a separate output file
# to avoid conflicts.
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 SRTR Multi-Organ Parser - Parallel Execution${NC}"
echo "============================================================"

# Create logs directory
mkdir -p logs

# Array of organs to parse
organs=("kidney" "liver" "heart" "lung" "pancreas" "intestine")

echo -e "\n${YELLOW}🚀 Launching 6 parsers in parallel...${NC}\n"

# Launch parsers in parallel
for organ in "${organs[@]}"; do
    echo "  → Starting $organ parser..."
    (
        source venv/bin/activate
        python scripts/parse_srtr_data_v2.py --organ "$organ" > "logs/parse_$organ.log" 2>&1
        echo "✅ $organ complete"
    ) &
done

# Wait for all background jobs
echo -e "\n${YELLOW}⏳ Waiting for all parsers to complete...${NC}\n"
wait

echo -e "\n${GREEN}✅ All organs parsed successfully!${NC}\n"

# Show summary
echo "📊 Summary:"
echo "─────────────────────────────────────────"

for organ in "${organs[@]}"; do
    if [ -f "data/srtr/processed/${organ}_summary.json" ]; then
        total=$(jq -r '.total_records' "data/srtr/processed/${organ}_summary.json")
        echo "  $organ: $total records"
    fi
done

echo
echo "📁 Output files in: data/srtr/processed/"
echo "📋 Logs in: logs/parse_*.log"
echo

# Optional: Show any errors from logs
echo -e "${YELLOW}🔍 Checking for errors...${NC}"
if grep -q "Error\|ERROR\|Failed" logs/parse_*.log 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Some warnings/errors found in logs. Check logs/ directory.${NC}"
else
    echo -e "${GREEN}✅ No errors detected!${NC}"
fi

echo
echo -e "${BLUE}🎉 Multi-organ parsing complete!${NC}"
