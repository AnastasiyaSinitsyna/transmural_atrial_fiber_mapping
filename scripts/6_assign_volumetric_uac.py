"""
Volumetric UAC Coordinate Assignment Script
===========================================
Assigns 3D Universal Atrial Coordinates (α, β, γ) to the outer surface nodes 
of a volumetric atrial mesh. Uses KD-tree nearest-neighbor matching to project 
endocardial UAC fields onto the volumetric boundary and determines the 
transmural coordinate γ based on proximity to endo-/epicardial surfaces.
Output: .vtx strength files for downstream Laplace solves or fiber interpolation.
"""

#
import os
import sys
import argparse
import numpy as np
from sklearn.neighbors import NearestNeighbors
from UAC_lib import utils


# Create the parser
my_parser = argparse.ArgumentParser(description="Writes vtx files for volumetric UAC")

# Add the arguments
my_parser.add_argument("target_path", metavar="path", type=str, help="Path for the volumetric mesh")
my_parser.add_argument("endo_path", metavar="path", type=str, help="Path for the endo mesh")
my_parser.add_argument("epi_path", metavar="path", type=str, help="Path for the epi mesh")
my_parser.add_argument("mesh_name_vol", metavar="filename", type=str, help="Mesh name vol")
my_parser.add_argument("mesh_name_endo", metavar="filename", type=str, help="Mesh name endo")
my_parser.add_argument("mesh_name_epi", metavar="filename", type=str, help="Mesh name epi")

# Execute parse_args()
args = my_parser.parse_args()

base_dir = args.target_path
endo_dir = args.endo_path
epi_dir = args.epi_path
mesh_name_vol = args.mesh_name_vol
mesh_name_endo = args.mesh_name_endo
mesh_name_epi = args.mesh_name_epi

if not os.path.isdir(base_dir):
    print("The target mesh path specified does not exist")
    sys.exit()


print(base_dir)

pts = utils.read_pts(base_dir + mesh_name_vol)
vtx_surf = utils.read_pts(base_dir + mesh_name_vol + ".surf", n=1, vtx=True, item_type=int)

print(vtx_surf)


xlist = []
ylist = []
zlist = []

for loop in pts:
    xlist.append(loop[0])
    ylist.append(loop[1])
    zlist.append(loop[2])


List_SN = vtx_surf

xlist_surf = []
ylist_surf = []
zlist_surf = []

for ind in range(len(List_SN)):
    xlist_surf.append(xlist[List_SN[ind]])
    ylist_surf.append(ylist[List_SN[ind]])
    zlist_surf.append(zlist[List_SN[ind]])

Pts_surf = [xlist_surf, ylist_surf, zlist_surf]
Pts_surf = list(zip(*Pts_surf))

# read in UAC and find values
print(endo_dir)
Pts_XYZ_0 = utils.read_pts(endo_dir + mesh_name_endo)
Pts_ABC_0 = utils.read_pts(endo_dir + "2D_UAC")

xlist_abc_0 = []
ylist_abc_0 = []

for loop in Pts_ABC_0:
    xlist_abc_0.append(loop[0])
    ylist_abc_0.append(loop[1])

print(epi_dir)
Pts_XYZ_0_E = utils.read_pts(epi_dir + mesh_name_epi)

# KD tree as much faster
neigh = NearestNeighbors(n_neighbors=1)
neigh.fit(Pts_XYZ_0)
x_y_z_dist_endo, Endo_List_Nodes = neigh.kneighbors(Pts_surf, return_distance=True)

neigh.fit(Pts_XYZ_0_E)
x_y_z_dist_epi, _ = neigh.kneighbors(Pts_surf, return_distance=True)

alpha = []
beta = []
gamma = []

for ind in range(len(Endo_List_Nodes)):
    node = Endo_List_Nodes[ind]
    node = node[0]
    alpha.append(xlist_abc_0[node])
    beta.append(ylist_abc_0[node])
    D1 = x_y_z_dist_endo[ind]
    D2 = x_y_z_dist_epi[ind]
    Dist_E = np.concatenate([D1, D2])
    IndFound = utils.find_index(Dist_E, min)
    gamma.append(IndFound)

utils.write_vtx_strength_intra(vtx_surf, alpha, base_dir + "Alpha")
utils.write_vtx_strength_intra(vtx_surf, beta, base_dir + "Beta")
utils.write_vtx_strength_intra(vtx_surf, gamma, base_dir + "Gamma")
