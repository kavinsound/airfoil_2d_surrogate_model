from pathlib import Path
import os
import numpy as np
import re
import pandas as pd
import json
import shutil

def read_coeff(file_path):
    f_path = os.path.join(file_path, "postProcessing", "forceCoeffs", "0", "coefficient_0.dat")
    f_path = Path(f_path).resolve()

    data = np.loadtxt(f_path)
    time, Cd, Cl = data[:, 0], data[:, 1], data[:, 4]

    mask = time[:] > 15

    time, Cd, Cl = time[mask], Cd[mask], Cl[mask]

    avgCd = Cd.mean()
    avgCl = Cl.mean()
    return avgCd, avgCl

def collectData(file_path):

    Cd, Cl = read_coeff(file_path)

    p_txt = os.path.join(file_path, "param.txt")
    with open(p_txt, "r") as f:
        content = f.read()

    uppercst = re.search(r"Upper CST:\s*\[(.*?)\]", content)
    lowercst = re.search(r"Lower CST:\s*\[(.*?)\]", content)
    aoa = re.search(r"Angle of Attack:\s*(.*?)\n", content)
    re_n = re.search(r"Reynold's:\s*(.*?)\n", content)

    uppercst = np.fromstring(uppercst.group(1), sep=" ")
    # print(uppercst.dtype)
    lowercst = np.fromstring(lowercst.group(1), sep=" ")
    aoa = (aoa.group(1))
    re_n = float(re_n.group(1))
    return uppercst, lowercst, aoa, re_n, Cd, Cl


if __name__ == "__main__":

    if Path("generated_cases").exists():



        case_list = [case for case in Path("generated_cases").iterdir() if case.is_dir()]
        
        if not Path("failed_cases").exists():

            os.mkdir("failed_cases")
        
        columns = []
        for i in range(1, 7):
            columns.append(f"CST_U_{i}")
        for i in range(1, 7):
            columns.append(f"CST_L_{i}")

        columns.extend(["AOA", "RE_N", "CD", "CL"])
        data = pd.DataFrame(columns=columns)
        for i, case_path in enumerate(case_list):

            state = json.load(open(os.path.join(case_path, "job.json"), "r"))["status"]
            if state == "completed":
                print(f"{i+1} {case_path.stem} completed.")

                u_cst, l_cst, aoa, re_n, Cd, Cl = collectData(case_path)
                n_row = list(u_cst) + list(l_cst) + [aoa, re_n, Cd, Cl]
                data.loc[len(data)] = n_row
            else:
                shutil.copytree(case_path, os.path.join("failed_cases", case_path.stem), dirs_exist_ok=True)
                print(f"{i+1} {case_path.stem} failed.")
                with open("status.json", "r") as f:
                    vals = json.load(f)
                vals.setdefault("failed", 0)
                vals["failed"] += 1

        if (Path("sim_data.csv").exists()):
            data.to_csv("sim_data.csv", index=False, mode="a", header=False)
        else:
            data.to_csv("sim_data.csv", index=False, mode="w")
