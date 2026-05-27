#!/bin/bash
#SBATCH --account=pi-lgrandi
#SBATCH --partition=caslake
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=/scratch/midway3/jiafu/EventViewer/scripts/cvmfs_check_%j.out
#SBATCH --error=/scratch/midway3/jiafu/EventViewer/scripts/cvmfs_check_%j.err

echo "Checking CVMFS paths..."
ls /cvmfs/xenon.opensciencegrid.org/releases/nT/ 2>&1 || echo "No nT/ under releases"
ls /cvmfs/xenon.opensciencegrid.org/ 2>&1 || echo "CVMFS not mounted"
echo "---"
which python3
which python
echo "---"
ls /cvmfs/xenon.opensciencegrid.org/releases/ 2>&1 | head -20 || echo "No releases/"
