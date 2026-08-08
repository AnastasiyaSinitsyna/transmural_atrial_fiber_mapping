#!/usr/bin/env python3
"""
Threshold-Based Transmural Fiber Mapping Script
================================================
Assigns fiber orientations to a 3D volumetric atrial mesh using a step-wise 
(binary) interpolation scheme. Elements closer to the endocardium (γ < 0.5) 
inherit fiber directions from the endocardial atlas, while elements closer 
to the epicardium (γ ≥ 0.5) inherit from the epicardial atlas. 
Outputs: VTK visualization and openCARP-compatible (.pts/.vec) fiber fields.
This implements the threshold-based method compared in Figure 11A of the manuscript.
"""

import os
import sys
import argparse
import shutil
import numpy as np
from sklearn.neighbors import NearestNeighbors
from UAC_lib import utils


# =============================================================================
# 1. COMMAND-LINE ARGUMENT PARSING
# =============================================================================
my_parser = argparse.ArgumentParser(description="Assigns fiber orientations using threshold-based transmural interpolation.")

my_parser.add_argument("target_path", metavar="path", type=str, 
                       help="Directory containing the volumetric target mesh")
my_parser.add_argument("mesh3d_input", metavar="filename", type=str, 
                       help="Filename of the 3D volumetric mesh (points + elements)")
my_parser.add_argument("mesh2d_input", metavar="filename", type=str, 
                       help="Filename of the 2D mapped mesh (contains γ coordinate in Z)")
my_parser.add_argument("endo_dir", metavar="path", type=str, 
                       help="Directory containing the endocardial surface mesh")
my_parser.add_argument("endo_mesh", metavar="filename", type=str, 
                       help="Endocardial mesh filename")
my_parser.add_argument("endo_fibre_file", metavar="filename", type=str, 
                       help="Endocardial fiber orientation file (.txt/.dat)")
my_parser.add_argument("epi_dir", metavar="path", type=str, 
                       help="Directory containing the epicardial surface mesh")
my_parser.add_argument("epi_mesh", metavar="filename", type=str, 
                       help="Epicardial mesh filename")
my_parser.add_argument("epi_fibre_file", metavar="filename", type=str, 
                       help="Epicardial fiber orientation file (.txt/.dat)")
my_parser.add_argument("output_file_name", metavar="filename", type=str, 
                       help="Base name for the final output fiber files")

args = my_parser.parse_args()
base_dir = args.target_path

# Validate target directory
if not os.path.isdir(base_dir):
    print(f"Error: Target directory not found at {base_dir}")
    sys.exit(1)

print(f"Processing threshold fiber mapping in: {base_dir}")


# =============================================================================
# 2. LOAD MESHES AND FIBER ORIENTATIONS
# =============================================================================
# Load volumetric target mesh (3D geometry)
Pts_XYZ_1 = utils.read_pts(base_dir + args.mesh3d_input)
Elems_XYZ_1 = utils.read_elem(base_dir + args.mesh3d_input)

# Load 2D mapped mesh (Z-coordinate represents normalized transmural depth γ)
Pts_ABC_1 = utils.read_pts(base_dir + args.mesh2d_input)

# Load endocardial surface mesh and fiber field
Pts_XYZ_0_Endo = utils.read_pts(args.endo_dir + args.endo_mesh)
Elems_XYZ_0_Endo = utils.read_elem(args.endo_dir + args.endo_mesh)
Fibres_XYZ_0_Endo = np.loadtxt(args.endo_dir + args.endo_fibre_file)

# Load epicardial surface mesh and fiber field
Pts_XYZ_0_Epi = utils.read_pts(args.epi_dir + args.epi_mesh)
Elems_XYZ_0_Epi = utils.read_elem(args.epi_dir + args.epi_mesh)
Fibres_XYZ_0_Epi = np.loadtxt(args.epi_dir + args.epi_fibre_file)


# =============================================================================
# 3. COMPUTE ELEMENT MIDPOINTS (BARYCENTERS)
# =============================================================================
# Midpoints are used for spatial correspondence between meshes
M_XYZ_0_2D = utils.mp_calc_ele_4(Pts_ABC_1, Elems_XYZ_1)   # 2D mapped mesh midpoints
M_XYZ_0_Endo = utils.mp_calc_ele_3(Pts_XYZ_0_Endo, Elems_XYZ_0_Endo)  # Endo midpoints
M_XYZ_0_Epi = utils.mp_calc_ele_3(Pts_XYZ_0_Epi, Elems_XYZ_0_Epi)     # Epi midpoints
M_XYZ_0_Vol = utils.mp_calc_ele_4(Pts_XYZ_1, Elems_XYZ_1)             # Volumetric midpoints


# =============================================================================
# 4. KD-TREE NEAREST-NEIGHBOR MATCHING
# =============================================================================
neigh = NearestNeighbors(n_neighbors=1)

# Find closest endocardial element midpoint for each volumetric element
neigh.fit(M_XYZ_0_Endo)
Closest_Endo = neigh.kneighbors(M_XYZ_0_Vol, return_distance=False)

# Find closest epicardial element midpoint for each volumetric element
neigh.fit(M_XYZ_0_Epi)
Closest_Epi = neigh.kneighbors(M_XYZ_0_Vol, return_distance=False)


# =============================================================================
# 5. THRESHOLD-BASED FIBER ASSIGNMENT (γ = 0.5 CUT)
# =============================================================================
Fibres_ABC_A_1 = []
Fibres_ABC_B_1 = []
Fibres_ABC_C_1 = []

n_elements = len(Closest_Endo)
print(f"Assigning fibers to {n_elements} volumetric elements (threshold γ = 0.5)...")

for ind in range(n_elements):
    # Z-coordinate of the 2D mapped mesh represents normalized transmural depth γ
    if M_XYZ_0_2D[ind, 2] < 0.5:
        idx = Closest_Endo[ind, 0]
        Fibres_ABC_A_1.append(Fibres_XYZ_0_Endo[idx, 0])
        Fibres_ABC_B_1.append(Fibres_XYZ_0_Endo[idx, 1])
        Fibres_ABC_C_1.append(Fibres_XYZ_0_Endo[idx, 2])
    else:
        idx = Closest_Epi[ind, 0]
        Fibres_ABC_A_1.append(Fibres_XYZ_0_Epi[idx, 0])
        Fibres_ABC_B_1.append(Fibres_XYZ_0_Epi[idx, 1])
        Fibres_ABC_C_1.append(Fibres_XYZ_0_Epi[idx, 2])
        
    # Progress indicator
    if ind % 500 == 0:
        print(f"  Processed {ind}/{n_elements} elements")

# Combine components into list of (X, Y, Z) vectors
Fibres_ABC_Mesh1 = list(zip(Fibres_ABC_A_1, Fibres_ABC_B_1, Fibres_ABC_C_1))


# =============================================================================
# 6. EXPORT FIBER FIELD TO VTK AND CARP FORMATS
# =============================================================================
print("Exporting threshold-based fiber field...")

# Read original mesh to attach fibers for VTK visualization
pts, elems, fiber, data = utils.read_carp(base_dir, args.mesh3d_input, return_surface=False)
utils.write_vtk(pts, elems, Fibres_ABC_Mesh1, data, base_dir + "Fibres_Threshold.vtk")

# Write CARP-compatible format
mname = base_dir + "Fibres_Threshold"
utils.write_carp(pts, elems, Fibres_ABC_Mesh1, None, mname)

# Write visualization mesh with midpoints and fibers
mname_aux = base_dir + "Aux_2"
utils.write_carp(M_XYZ_0_Vol, elems, Fibres_ABC_Mesh1, None, mname_aux)

# Convert to openCARP standard vector/point files
shutil.copyfile(mname_aux + ".pts", base_dir + args.output_file_name + ".vpts")
shutil.copyfile(mname_aux + ".lon", base_dir + args.output_file_name + ".vec")

# Save angles/threshold variant for comparison
mname_angles = base_dir + "UAC_Angles_Threshold"
utils.write_carp(M_XYZ_0_Vol, elems, Fibres_ABC_Mesh1, None, mname_angles)

print("Threshold-based fiber mapping completed successfully.")