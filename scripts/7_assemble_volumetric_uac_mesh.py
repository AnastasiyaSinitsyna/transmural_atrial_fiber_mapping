"""
Volumetric UAC Mesh Assembly Script
====================================
Reads precomputed Universal Atrial Coordinate (UAC) scalar fields (α, β, γ) 
from Laplace solver outputs (.igb files), stacks them into a 3D coordinate 
array, and exports the result as a CARP-compatible node mesh file. 
This step converts solved parametric fields into a usable 3D coordinate mesh 
for downstream electrophysiological simulations or visualization.
"""

#
import os
import sys
import argparse
from UAC_lib import utils


# Create the parser
my_parser = argparse.ArgumentParser(description="Writes mesh file of volumetric UAC")

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

if not os.path.isdir(base_dir):
    print("The target mesh path specified does not exist")
    sys.exit()

print(base_dir)

Alpha = utils.read_array_igb(base_dir + "Alpha/phie.igb")[0]
Beta = utils.read_array_igb(base_dir + "Beta/phie.igb")[0]
Gamma = utils.read_array_igb(base_dir + "Gamma/phie.igb")[0]
print(Alpha)

xlist_surf = []
ylist_surf = []
zlist_surf = []

for ind in range(len(Alpha)):
    xlist_surf.append(Alpha[ind])
    ylist_surf.append(Beta[ind])
    zlist_surf.append(Gamma[ind])

Pts_surf = [xlist_surf, ylist_surf, zlist_surf]
Pts_surf = list(zip(*Pts_surf))

print(Pts_surf)
print((len(Pts_surf)))

mname = base_dir + "Mesh_UAC_3D"
utils.write_carp_nodes_uacs_3d(Pts_surf, mname)