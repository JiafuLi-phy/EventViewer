#!/bin/bash
#SBATCH --account=pi-lgrandi
#SBATCH --partition=caslake
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=/scratch/midway3/jiafu/EventViewer/scripts/cvmfs_check2_%j.out
#SBATCH --error=/scratch/midway3/jiafu/EventViewer/scripts/cvmfs_check2_%j.err

echo "Host: $(hostname)"
echo ""

# Check /cvmfs existence
if [ -d /cvmfs ]; then
    echo "/cvmfs exists"
    ls /cvmfs/ 2>&1 | head -20
else
    echo "/cvmfs does NOT exist"
fi

echo ""
echo "df | grep cvmfs:"
df -h 2>/dev/null | grep -i cvmfs || echo "  no cvmfs mounts"

echo ""
echo "mount | grep cvmfs:"
mount 2>/dev/null | grep -i cvmfs || echo "  no cvmfs in mount"

echo ""
echo "ls /cvmfs/xenon* 2>&1:"
ls /cvmfs/xenon* 2>&1 || echo "  failed"

echo ""
echo "Checking autofs..."
ls /etc/auto.master 2>/dev/null && cat /etc/auto.master | grep -i cvmfs || echo "  not in auto.master"
