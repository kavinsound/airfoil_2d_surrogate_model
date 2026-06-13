#!/bin/bash
#SBATCH --job-name=data_generation
#SBATCH --output=logs/array_%A_%a.out
#SBATCH --error=logs/array_%A_%a.err
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=06:00:00

# Set the array scale to match your batch size (e.g., 1 to 256)
# Limit to 32 active jobs at a time
#SBATCH --array=1-256%64

# --- CONFIGURATION ---
# Define the path to your master text file containing the hashes
MAP_FILE="/scratch/ks2292/run/generate/meshList.txt"
BASE_DIR="/scratch/ks2292/run/generate/generated_cases"

# --- THE MAGIC LINE ---
# Use sed to grab the exact line corresponding to this Slurm Task ID.
# The "-n" flag suppresses normal output, and "${SLURM_ARRAY_TASK_ID}p" 
# prints ONLY that specific line number.
CASE_HASH=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$MAP_FILE")
python3 updateStatus.py
cd $BASE_DIR/case_$CASE_HASH

module purge

source /home/ks2292/.bashrc


echo meshing...

# Move to the case directory
chmod +x Allmesh

python3 updateJobStatus.py

cd ../..
python3 updateStatus.py
cd $BASE_DIR/case_$CASE_HASH

# Decompose the case for parallel run
./Allmesh

echo solving...

python3 updateJobStatus.py
cd ../..
python3 updateStatus.py
cd $BASE_DIR/case_$CASE_HASH

chmod +x Allrun

# Decompose the case for parallel run
./Allrun

python3 updateJobStatus.py
cd ../..
python3 updateStatus.py
cd $BASE_DIR/case_$CASE_HASH
