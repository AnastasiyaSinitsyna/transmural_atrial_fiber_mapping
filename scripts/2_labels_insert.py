#!/usr/bin/python3
#
import os
import sys
import argparse
import numpy as np
from UAC_lib import utils


# Initialize argument parser
my_parser = argparse.ArgumentParser(description="Calculation of labels using laplace solves only")

# Add the arguments
my_parser.add_argument("target_path", metavar="path", type=str, help="Path for the new target mesh")
my_parser.add_argument("laplace_path", metavar="path", type=str, help="Path for the laplace par files")
my_parser.add_argument("mesh_name", metavar="filename", type=str, help="Mesh name before labelling")
my_parser.add_argument("mesh_name_label", metavar="filename", type=str, help="Mesh name after labelling")
my_parser.add_argument("threshold_pv", metavar="float", type=float, help="Threshold for PV ")
my_parser.add_argument("threshold_laa", metavar="float", type=float, help="Threshold for LAA ")

#  Parse command-line arguments
args = my_parser.parse_args()

base_dir = args.target_path
laplace_dir = args.laplace_path
mesh_name = args.mesh_name
mesh_name_label = args.mesh_name_label
threshold_pv = args.threshold_pv
threshold_laa = args.threshold_laa


print(base_dir)
# Load mesh elements, nodes, and surface geometry
pts, elems, *_, surface = utils.read_carp(base_dir, mesh_name)

# Load Laplace solution fields (.igb format)
mv_pv1 = utils.read_array_igb(base_dir + "MV_PV1/phie.igb")[0]
mv_pv2 = utils.read_array_igb(base_dir + "MV_PV2/phie.igb")[0]
mv_pv3 = utils.read_array_igb(base_dir + "MV_PV3/phie.igb")[0]
mv_pv4 = utils.read_array_igb(base_dir + "MV_PV4/phie.igb")[0]
mv_laa = utils.read_array_igb(base_dir + "MV_LAA/phie.igb")[0]


# Initialize default region label 11 for all nodes
node_inds = np.ones(len(pts), int) * 11
# Assign region IDs to pulmonary veins 21/23/25/27
node_inds[mv_pv1 > threshold_pv] = 21
node_inds[mv_pv2 > threshold_pv] = 23
node_inds[mv_pv3 > threshold_pv] = 25
node_inds[mv_pv4 > threshold_pv] = 27
# Assign region ID to left atrial appendage 13
node_inds[mv_laa > threshold_laa] = 13


# Export node labels to .dat file
utils.write_dat_simple(node_inds, "Data_Labels.dat")

# Map node labels to element regions and save the updated mesh
regs = np.empty(len(elems), int)
for i in range(len(elems)):
    regs[i] = node_inds[min(elems[i].n)]

surface = utils.add_celldata_array(surface, "tags")
utils.write_surface_to_carp_mesh(surface, base_dir + mesh_name_label, labels=regs)
