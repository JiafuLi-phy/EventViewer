#!/bin/bash
#SBATCH --job-name=extract_peaks
#SBATCH --partition=caslake
#SBATCH --account=pi-lgrandi
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/midway3/jiafu/EventViewer/scripts/extract_peaks_%j.out
#SBATCH --error=/scratch/midway3/jiafu/EventViewer/scripts/extract_peaks_%j.err

echo "Job started at $(date)"
echo "Running on $(hostname)"

# Source the CVMFS environment for straxen
source /cvmfs/xenon.opensciencegrid.org/releases/nT/development/setup.sh el8.2026.02.2

echo "Environment sourced"

# Run extraction
python /scratch/midway3/jiafu/EventViewer/scripts/extract_peak_data.py \
    --run 023756 \
    --n-events 10 \
    --s1-min 1000 \
    --s2-min 100000 \
    --out /scratch/midway3/jiafu/EventViewer/data/

echo "Job finished at $(date)"
