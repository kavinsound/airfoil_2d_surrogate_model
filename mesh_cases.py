from pathlib import Path
import os
import subprocess


def run_job(case_id):
    root_path = "generated_cases"
    case_name = f"case_{case_id}"
    job_path = os.path.join(root_path, case_name, "Allmesh")
    job_path = Path(job_path).resolve()
    print(job_path)
    if job_path.exists():
        subprocess.run(job_path)


if __name__ == "__main__":
    with open("meshList.txt", "r") as f:
        for id in f:
            id = id.strip()
            run_job(id)
    with open("meshList.txt", "w") as f:
        pass

    