Preparing data generation:
    1. Python scripts to manage creating and deleting new cases
    2. Sbatch job file to mesh each case
    3. Master sbatch job file to start
    4. 256 cases at a time, 2048 cases total
    5. Record time for each case to run

Preprocessing:
    1. Python script to extract data and analyze if converged
    2. Preprocess into csv and normalization and all other tools

Pytorch NN
    1. Code up network, research how many layers and nodes
    2. Create cross validation training scheme
    3. Sweep hyperparameter space for best results
    4. Compile accuracy and time results to compare to traditional


HPC Autorun Pipeline
    case_generator (256) --> mesh.slurm schedule --> run.slurm --> case_generator (1) until 2056