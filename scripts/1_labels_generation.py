import os
import sys
import argparse
import numpy as np
from UAC_lib import utils


# Setup argument parser
parser = argparse.ArgumentParser(description="The regions are calculated using the Laplace method only.")

# Add arguments
parser.add_argument("target_path", type=str, help="Directory containing the target mesh")
parser.add_argument("laplace_path", type=str, help="Directory containing Laplace parameter files (reserved for future steps)")
parser.add_argument("mesh_name", type=str, help="Base mesh filename (before labeling)")
parser.add_argument("threshold_pv", type=float, help="Threshold for pulmonary veins (e.g., 0.8)")
parser.add_argument("threshold_laa", type=float, help="Threshold for left atrial appendage (e.g., 0.35)")
parser.add_argument("region_name", type=str, help="Landmark coordinates file ")

args = parser.parse_args()

base_dir = args.target_path
laplace_dir = args.laplace_path
mesh_name = args.mesh_name
region_name = args.region_name

if not os.path.isdir(base_dir):
    print("directory not found")
    sys.exit()

if not os.path.isdir(laplace_dir):
    print("directory not found")
    sys.exit()

print(base_dir)

# Load mesh geometry
pts, elems, *_ = utils.read_carp(base_dir, mesh_name, return_surface=False)
# Load landmark coordinates
pts_src = utils.load_landmarks(base_dir + region_name)

# Identify Left Atrial Appendage (LAA)
# Uses the 5th landmark (index 4) to find the 50 closest mesh nodes
laa_marker = pts_src[4]
nodes_laa = np.argsort(utils.closest_node(laa_marker, pts))[:50]
print(laa_marker)
print("LAA identification complete.")


#  Identify Pulmonary Veins (PVs)
size = 4
nodes_pv = [None] * size
pts_pv = [None] * size
# t boundary nodes for each PV tag
for i in range(size):
    *_, nodes_pv[i] = utils.find_nodes(elems, pts, i+1)
    pts_pv[i] = np.empty((len(nodes_pv[i]), 3), float)
    for ind in range(len(nodes_pv[i])):
        pts_pv[i][ind] = pts[nodes_pv[i][ind]]

# Map anatomical landmarks to detected PV boundaries
sp = [None] * size
for i in range(size):
    sp[i] = utils.pv_index_remap(pts_src[i], pts_pv, np.mean)
print(sp)

pv_choices = [None] * size
for i in range(size):
    pv_choices[i] = sp.index(i)

nodes_rspv = nodes_pv[pv_choices.index(0)]
nodes_ripv = nodes_pv[pv_choices.index(1)]
nodes_lipv = nodes_pv[pv_choices.index(2)]
nodes_lspv = nodes_pv[pv_choices.index(3)]
print('PVs is done')

#Identify Mitral Valve (MV)
# Assumes MV corresponds to the largest/last boundary returned by find_nodes
*_, nodes_mv = utils.find_nodes(elems, pts) 
print('MV is done')

# Export region labels to .vtx files
utils.write_vtx_extra(nodes_mv, base_dir + "MV.vtx")
utils.write_vtx_extra(nodes_lspv, base_dir + "PV1.vtx")
utils.write_vtx_extra(nodes_lipv, base_dir + "PV2.vtx")
utils.write_vtx_extra(nodes_rspv, base_dir + "PV3.vtx")
utils.write_vtx_extra(nodes_ripv, base_dir + "PV4.vtx")
utils.write_vtx_extra(nodes_laa, base_dir + "LAA.vtx")

print("Region labeling pipeline completed successfully.")
