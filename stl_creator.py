from pathlib import Path
import glob
import numpy as np
import os
from shapely.geometry import Polygon
from shapely import affinity
import trimesh
import sys
import matplotlib.pyplot as plt
from shapely import make_valid



def createStl(file_path, rotate=10, height=2):
    # print(file_path)
    coords = np.loadtxt(file_path)

    p = Polygon(coords)

    if not p.is_valid:
        print("Warning: The polygon boundary self-intersects or is invalid.")
        with open("invalid_files.txt", "a") as f:
            f.write(f"{file_path}\n")

    # x, y = p.exterior.xy
    rotate = -1 * rotate
    p = affinity.rotate(p, rotate, origin=(0, 0))
    # plt.figure(figsize=(10, 10))   check for ordering
    # plt.plot(x, y, "black")
    # plt.fill(x, y, "blue", alpha=0.5)
    # plt.gca().set_aspect("equal")
    # plt.show()

    mesh = trimesh.creation.extrude_polygon(p, height)
    return mesh

if __name__ == "__main__":
    folder_path = "./cleaned_foils"

    file_name = "ag03_cleaned.dat"

    file_path = os.path.join(folder_path, file_name)
 
    myMesh = createStl(file_path)

    output_folder = "./generated_stls"

    os.makedirs(output_folder, exist_ok=True)

    output_filename = Path(file_path).stem
    output_filepath = f"{Path(output_folder)}/{output_filename}.stl"

    myMesh.export(output_filepath)


