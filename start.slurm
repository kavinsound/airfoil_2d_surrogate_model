#!/bin/bash
#SBATCH --job-name=cleanup_script   # Job name
#SBATCH --time=24:00:00            # Max wall time (HH:MM:SS)
#SBATCH --nodes=1                  # Number of nodes
#SBATCH --output=start_logs/clean_out_%A.out
#SBATCH --ntasks=1                 # Total number of tasks (usually matches processors)
#SBATCH --cpus-per-task=1          # Threads per task        # Partition/queue name (cluster-specific)
#SBATCH --mem=1000                  # Memory per node (adjust)

# Load OpenFOAM environment if needed

module purge

source /home/ks2292/.bashrc

echo reading data...

python3 data_reader.py 

echo generating batch...

python3 generate_next_batch.py
