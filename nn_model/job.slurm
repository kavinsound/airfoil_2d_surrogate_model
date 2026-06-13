#!/bin/bash
#SBATCH --job-name=torch_training   # Job name
#SBATCH --output=log.%j.out        # Standard output log (%j = job ID)
#SBATCH --error=log.%j.err         # Standard error log
#SBATCH --time=12:00:00            # Max wall time (HH:MM:SS)
#SBATCH --nodes=1                  # Number of nodes
#SBATCH --ntasks=1                 # Total number of tasks (usually matches processors)
#SBATCH --cpus-per-task=1          # Threads per task        # Partition/queue name (cluster-specific)
#SBATCH --mem=32000                  # Memory per node (adjust)
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
# Load OpenFOAM environment if needed

module purge

source /home/ks2292/.bashrc

echo "Running..."

python3 -u pytorch_nn.py
