#!/bin/bash
# Batch refresh: search multiple queries → discover executives → generate emails
# Target: ~2000 companies across Trimble reseller/dealer ecosystem

cd "$(dirname "$0")"
LOG="/tmp/company-refresh-$(date +%Y%m%d_%H%M%S).log"
echo "=== Batch Refresh Started: $(date) ===" | tee "$LOG"

QUERIES=(
  "Trimble resellers USA"
  "Trimble authorized dealers United States"
  "Trimble distributors North America"
  "Trimble surveying equipment dealers"
  "Trimble construction technology resellers"
  "Trimble agriculture dealers USA"
  "Trimble GPS equipment distributors"
  "Trimble geospatial solutions partners"
  "Trimble positioning services dealers"
  "Trimble civil engineering resellers"
  "Trimble MEP contractors dealers USA"
  "Trimble transportation logistics resellers"
  "Trimble forestry solutions dealers"
  "Trimble mining equipment distributors"
  "Trimble machine control dealers USA"
  "Trimble field service management resellers"
  "Trimble water utilities technology dealers"
  "Trimble oil gas surveying dealers"
  "Trimble precision agriculture distributors"
  "Trimble building construction partners USA"
)

TOTAL=0
for Q in "${QUERIES[@]}"; do
  echo "" | tee -a "$LOG"
  echo ">>> Searching: $Q (limit 100)" | tee -a "$LOG"
  python3 refresh.py search --query "$Q" --limit 100 --region US 2>&1 | tee -a "$LOG"
  TOTAL=$((TOTAL + 1))
  sleep 2  # be polite to search engines
done

echo "" | tee -a "$LOG"
echo "=== Search phase done ($TOTAL queries). Discovering executives... ===" | tee -a "$LOG"

# Discover executives from company websites
python3 refresh.py discover 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "=== Discover done. Generating emails... ===" | tee -a "$LOG"

# Generate email addresses
python3 refresh.py email 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "=== Final status ===" | tee -a "$LOG"
python3 refresh.py status 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "=== Batch Refresh Completed: $(date) ===" | tee -a "$LOG"
echo "Log: $LOG"
