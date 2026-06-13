import shutil
import os
from pathlib import Path


if __name__ == "__main__":
    shutil.rmtree(Path("generated_cases"), ignore_errors=True)
    os.remove("status.json")
    os.remove("meshList.txt")
    os.remove("sim_data.csv")