from pathlib import Path
import os
import shutil
from case_generator import genParams
import subprocess
import json

def cleanFolder():
    shutil.rmtree(Path("generated_cases").resolve(), ignore_errors=True)
    os.mkdir(Path("generated_cases"))
    open("meshList.txt", "w").close()

if __name__ == "__main__":
    cleanFolder()
    init = 0
    if Path("status.json").exists():
        with open(Path("status.json"), 'r') as f:
            content = json.load(f)
        content["pending"] = 0
        content["meshing"] = 0
        content["solving"] = 0
        init = content["initialized"]
        with open(Path("status.json"), 'w') as f:
            json.dump(content, f, indent=4)

    if init < 2304:
        genParams(256)
        subprocess.run(["python3", "updateStatus.py"])
        job_id = subprocess.run(["sbatch", "--parsable", "master_runner.slurm"], capture_output=True, text=True, check=True)
        job_id = job_id.stdout.strip()
        dependency_arg = f"--dependency=afterany:{job_id}"
        subprocess.run(["sbatch", dependency_arg, "start.slurm"])

