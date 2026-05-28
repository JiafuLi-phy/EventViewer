#!/bin/bash
# Standalone DALI raw data probe — does NOT modify EventViewer
# Output: dali_probe/report.md
set -e
REPORT="$(cd "$(dirname "$0")" && pwd)/report.md"
echo "# DALI Raw Data Probe Report" > "$REPORT"
echo "" >> "$REPORT"
echo "Started: $(date)" >> "$REPORT"
echo "" >> "$REPORT"

echo "### Step 1: SSH connectivity" | tee -a "$REPORT"
ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 dali "hostname && echo 'OK'" 2>&1 | tee -a "$REPORT"
echo "" >> "$REPORT"

echo "### Step 2: Find runs with raw_records" | tee -a "$REPORT"
ssh dali "ls -d /dali/lgrandi/xenonnt/raw/043572 2>/dev/null && echo '043572 exists' || echo '043572 missing'; ls -d /dali/lgrandi/xenonnt/raw/044281 2>/dev/null && echo '044281 exists' || echo '044281 missing'" 2>&1 | tee -a "$REPORT"
echo "" >> "$REPORT"

echo "### Step 3: List raw_records chunks for 043572" | tee -a "$REPORT"
ssh dali "ls /dali/lgrandi/xenonnt/raw/043572/ | head -5" 2>&1 | tee -a "$REPORT"
echo "" >> "$REPORT"

echo "### Step 4: Find Python environment" | tee -a "$REPORT"
ssh dali "which python3 2>/dev/null || echo 'no python3'; python3 -c 'import strax; print(\"strax OK\")' 2>&1 || echo 'strax not in default python'" 2>&1 | tee -a "$REPORT"
echo "" >> "$REPORT"

echo "### Step 5: Try to load a single raw_records chunk" | tee -a "$REPORT"
# Try container approach
ssh dali "singularity exec /cvmfs/singularity.opensciencegrid.org/xenonnt/xenonnt:latest python3 -c \"
import strax
import os
raw_dir = '/dali/lgrandi/xenonnt/raw/043572'
files = sorted(os.listdir(raw_dir))
print(f'Found {len(files)} files in {raw_dir}')
print(f'First file: {files[0]}')
\" 2>&1" 2>&1 | tee -a "$REPORT"

echo "" >> "$REPORT"
echo "Probe completed: $(date)" >> "$REPORT"
echo "Report saved to $REPORT"
