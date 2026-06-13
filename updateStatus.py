import json
from pathlib import Path
import os
if __name__ == "__main__":
    parent_dir = Path("generated_cases").resolve()
    case_list = [p.resolve() for p in parent_dir.iterdir() if p.is_dir()]

    js = Path("status.json").resolve()

    if js.exists():

        with open(js, "r") as f:
            content = json.load(f)
        
        content["pending"] = 0
        content["meshing"] = 0
        content["solving"] = 0
        content.setdefault("completed", 0)
        content.setdefault("failed", 0)
        
        for c in case_list:
            js_path = os.path.join(c, "job.json")
            js_path = Path(js_path).resolve()
            with open(js_path, "r") as f:
                val = json.load(f)["status"]
            
            content[val] += 1
        
        content["completed"] = content["initialized"] - content["pending"] - content["meshing"] - content["solving"] - content["failed"]
        
        with open(js, "w") as f:
            json.dump(content, f, indent=4)

    else:
        content = {}
        content.setdefault("failed", 0)
        content.setdefault("initialized", 0)
        content.setdefault("pending", 0)
        content.setdefault("meshing", 0)
        content.setdefault("solving", 0)
        content.setdefault("completed", 0)
        with open(js, "w") as f:
            json.dump(content, f, indent=4)