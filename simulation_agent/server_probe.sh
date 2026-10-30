#!/usr/bin/env bash
# Read-only inventory for an authenticated Linux login node.
# No submission, no engine invocation, no secret/config dumps, no installation.
set -u
printf 'OS: '
uname -s
printf '\nAvailable commands (paths only):\n'
for app in g16 g09 orca lmp lmp_mpi gmx sbatch sacct sinfo squeue qsub qstat; do
    command -v "$app" || true
done
if type module >/dev/null 2>&1; then
    printf '\nRelevant module names:\n'
    module -t avail 2>&1 | grep -Ei 'gaussian|orca|lammps|gromacs|namd' || true
fi
if command -v sinfo >/dev/null 2>&1; then
    printf '\nSlurm partitions (not a price quote):\n'
    sinfo --noheader --format='%P %a %l %D %c %m' || true
fi
printf '\nInventory only. Confirm account tariff, minimum allocation and licenses before a pilot.\n'
