from pathlib import Path
import glob
import numpy as np
import os
from stl_creator import createStl
import re
from scipy.stats import truncnorm, qmc, norm
import shutil
import hashlib
import json
import sys

def generateCaseValsBatch(batch_size=16, current_count = 0):
    folder_path = "./cleaned_foils"
    search_pattern = Path(folder_path) / "*.dat"
    stl_files = glob.glob(str(search_pattern))
    
    
    sampler = qmc.Sobol(d=3, scramble=True, seed=67)
    if current_count > 0:
        sampler.fast_forward(current_count)

    batch = sampler.random(n=batch_size)

    aoa_batch = batch[:, 0]
    re_batch = batch[:, 1]
    cst_batch = batch[:, 2]

    #convert to aoa
    aoa_sample = []
    for n in aoa_batch:
        if n < 0.7:
            n = norm.ppf(n/0.7, loc=14, scale=4)
        else:
            n = norm.ppf((n-0.7)/0.3, loc=4, scale=3)
        aoa_sample.append(n)


    aoa_sample = np.clip(aoa_sample, -4, 22)

    aoa_sample = np.round(aoa_sample, 4)
    #convert re
    re_sample = re_batch * (100000-20000) + 20000
    re_sample = np.round(re_sample, 4)

    #find stl

    cst_sample = (np.floor(cst_batch * len(stl_files))).astype(int)
    
    stl_files = np.array(stl_files)
    files_sample = stl_files[cst_sample]
    stl_sample = []
    upper_sample = []
    lower_sample = []
    for i, stl_file in enumerate(files_sample):
        mySTL = createStl(stl_file, aoa_sample[i])
        stl_sample.append(mySTL)
        with open(stl_file, "r") as f:
            upper_cst = f.readline()
            lower_cst = f.readline()
    
        upper = re.findall(r"\[(.*?)\]", upper_cst)[0]
        lower = re.findall(r"\[(.*?)\]", lower_cst)[0]
        
        
        upper = np.fromstring(upper, sep=" ")
        upper_sample.append(upper)
        lower = np.fromstring(lower, sep=" ")
        lower_sample.append(lower)

    
    return upper_sample, lower_sample, aoa_sample, stl_sample, re_sample


def generateHash(upper, lower, aoa, re_n):
    hasher = hashlib.md5()

    upper_str = np.array2string(np.round(upper, 6))
    lower_str = np.array2string(np.round(lower, 6))

    str = f"{upper_str}_{lower_str}_{aoa:.2f}_{re_n:.2f}"

    hasher.update(str.encode("utf-8"))

    return hasher.hexdigest()[:8]



def genParams(n=16):
    template_path = "./template_case"
    output_root = "./generated_cases"
    os.makedirs(output_root, exist_ok=True)
    state_path = Path("status.json")

    if state_path.is_file():
        with open(state_path, "r") as f:
            state = json.load(f)
        
    else:
        state = {}
        state["initialized"] = 0
        state["pending"] = 0


    upper_batch, lower_batch, aoa_batch, stl_batch, re_batch = generateCaseValsBatch(n, state["initialized"])
    state["initialized"] += n
    with open(state_path, "w") as f:
        json.dump(state, f, indent=4) 

    n = len(upper_batch)
    for i in range(n):
        upper, lower, aoa, stl, re_n = upper_batch[i], lower_batch[i], aoa_batch[i], stl_batch[i], re_batch[i]
        case_id = generateHash(upper, lower, aoa, re_n)
        

        case_name = f"case_{case_id}"
        case_path = os.path.join(output_root, case_name)
        if Path(case_path).exists():
            shutil.rmtree(case_path)
        shutil.copytree(template_path, case_path, dirs_exist_ok=True)

        param_text_path = os.path.join(case_path, "param.txt")

        upper_str = np.array2string(upper).replace("\n", "")
        lower_str = np.array2string(lower).replace("\n", "")

        #save param.txt
        with open(param_text_path, "w") as param:
            param.write(f"Case ID: {case_id}\n")
            param.write(f"Upper CST: {upper_str}\n")
            param.write(f"Lower CST: {lower_str}\n")
            param.write(f"Angle of Attack: {aoa}\n")
            param.write(f"Reynold's: {re_n}\n")
        
        #replace airfoil_mesh.stl
        target_file = "airfoil_mesh.stl"
        trisurface_dir = os.path.join(case_path, "constant", "triSurface")
        target_path = os.path.join(trisurface_dir, target_file)

        stl.export(target_path)

        
        # subprocess.run([os.path.join(case_path, "Allmesh")])
        meshlist_path = Path(os.path.abspath(os.path.join(case_path, "..", "..", "meshList.txt")))
        with open (meshlist_path, "a") as f:
            f.write(f"{case_id}\n")
        
        target_file = "initialConditions"
        target_dir = os.path.join(case_path, "0", "include")
        target2_dir = os.path.join(case_path, "0.orig", "include")
        target_path = os.path.join(target_dir, target_file)
        target2_path = os.path.join(target2_dir, target_file)

        v = re_n * 1.5e-5
        v = np.round(v, 4)
        with open(target_path, "w") as f:
            f.write(f"flowVelocity\t({v} 0 0);")
        with open(target2_path, "w") as f:
            f.write(f"flowVelocity\t({v} 0 0);")

        target_path = os.path.join(case_path, "system", "forceCoeffs")
        with open(target_path, "r") as f:
            content = f.read()
        
        pattern = r"(magUInf\s+)\d+(\.\d+)?"
        sub = f"\\g<1>{v}"
        content = re.sub(pattern, sub, content)
        
        xCofR = np.round(0.25 * np.cos(np.radians(aoa)), 4)
        yCofR = np.round(-1 * 0.25 * np.sin(np.radians(aoa)), 4)

        pattern = r"(CofR\s+)\(.+?\);"
        sub = f"\\g<1>({xCofR} {yCofR} 0);"

        content = re.sub(pattern, sub, content)
        with open(target_path, "w") as f:
            f.write(content)
        


        



if __name__ == "__main__":
    n = int(sys.argv[1])
    
    genParams(n)
    


