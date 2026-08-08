#!/usr/bin/env python3
"""
Linear Transmural Fiber Interpolation Script
=============================================
Assigns fiber orientations to a 3D volumetric atrial mesh using continuous 
linear interpolation between endocardial and epicardial surface fields. 
For each volumetric element, the fiber vector is computed as:
    F(γ) = (1 - γ) * F_endo + γ * F_epi
where γ ∈ [0,1] is the normalized transmural coordinate (0 = endocardium, 
1 = epicardium). The interpolated vector is normalized to preserve unit length.
This implements the continuous interpolation method compared in Figure 11B of the manuscript.
"""

#
import os
import sys
import argparse
import shutil
import numpy as np
from sklearn.neighbors import NearestNeighbors
from UAC_lib import utils


# Create the parser
my_parser = argparse.ArgumentParser(description="UAC fibre mapping")

# Add the arguments
my_parser.add_argument("target_path", metavar="path", type=str, help="Path for the new target mesh")
my_parser.add_argument("mesh3d_input", metavar="filename", type=str, help="Mesh name 3D")
my_parser.add_argument("mesh2d_input", metavar="filename", type=str, help="Mesh name 2D")
my_parser.add_argument("endo_dir", metavar="path", type=str, help="Path for the endo")
my_parser.add_argument("endo_mesh", metavar="filename", type=str, help="Mesh name endo")
my_parser.add_argument("endo_fibre_file", metavar="filename", type=str, help="Mesh name endo fibre")
my_parser.add_argument("epi_dir", metavar="path", type=str, help="Path for the epi")
my_parser.add_argument("epi_mesh", metavar="filename", type=str, help="Mesh name epi")
my_parser.add_argument("epi_fibre_file", metavar="filename", type=str, help="Mesh name epi fibre")
my_parser.add_argument("output_file_name", metavar="filename", type=str, help="Fibre output file name")

# Execute parse_args()
args = my_parser.parse_args()

base_dir = args.target_path
mesh3d_input = args.mesh3d_input
mesh2d_input = args.mesh2d_input
endo_dir = args.endo_dir
endo_mesh = args.endo_mesh
endo_fibre_file = args.endo_fibre_file
epi_dir = args.epi_dir
epi_mesh = args.epi_mesh
epi_fibre_file = args.epi_fibre_file
output_file_name = args.output_file_name

if not os.path.isdir(base_dir):
    print("The target mesh path specified does not exist")
    sys.exit()


# read carp files, change to 3D versions
print(base_dir)
Pts_XYZ_1 = utils.read_pts(base_dir + mesh3d_input)
Elems_XYZ_1 = utils.read_elem(base_dir + mesh3d_input)
Pts_ABC_1 = utils.read_pts(base_dir + mesh2d_input)

print(endo_dir)
Pts_XYZ_0_Endo = utils.read_pts(endo_dir + endo_mesh)
Elems_XYZ_0_Endo = utils.read_elem(endo_dir + endo_mesh)
print(endo_fibre_file)
Fibres_XYZ_0_Endo = np.loadtxt(endo_dir + endo_fibre_file)


Fibres_XYZ_0_Endo_X = []
Fibres_XYZ_0_Endo_Y = []
Fibres_XYZ_0_Endo_Z = []

for loop in Fibres_XYZ_0_Endo:
    Fibres_XYZ_0_Endo_X.append(loop[0])
    Fibres_XYZ_0_Endo_Y.append(loop[1])
    Fibres_XYZ_0_Endo_Z.append(loop[2])

print(epi_dir)
Pts_XYZ_0_Epi = utils.read_pts(epi_dir + epi_mesh)
Elems_XYZ_0_Epi = utils.read_elem(epi_dir + epi_mesh)
Fibres_XYZ_0_Epi = np.loadtxt(epi_dir + epi_fibre_file)

Fibres_XYZ_0_Epi_X = []
Fibres_XYZ_0_Epi_Y = []
Fibres_XYZ_0_Epi_Z = []

for loop in Fibres_XYZ_0_Epi:
    Fibres_XYZ_0_Epi_X.append(loop[0])
    Fibres_XYZ_0_Epi_Y.append(loop[1])
    Fibres_XYZ_0_Epi_Z.append(loop[2])


M_XYZ_0_2D = utils.mp_calc_ele_4(Pts_ABC_1, Elems_XYZ_1)

#  Midpoints in XYZ for both meshes
M_XYZ_0_Endo = utils.mp_calc_ele_3(Pts_XYZ_0_Endo, Elems_XYZ_0_Endo)
M_XYZ_0_Epi = utils.mp_calc_ele_3(Pts_XYZ_0_Epi, Elems_XYZ_0_Epi)

# now for 3D
M_XYZ_0_Vol = utils.mp_calc_ele_4(Pts_XYZ_1, Elems_XYZ_1)


# find nearest neighbours and assign fibre depending on endo (<0.5) or epi (>0.5)

# update to KD tree as much faster
neigh = NearestNeighbors(n_neighbors=1)
neigh.fit(M_XYZ_0_Endo)
Closest_Endo = neigh.kneighbors(M_XYZ_0_Vol, return_distance=False)
neigh.fit(M_XYZ_0_Epi)
Closest_Epi = neigh.kneighbors(M_XYZ_0_Vol, return_distance=False)


# 5.  calculate fibre in a,b,c on mesh 1
Fibres_ABC_A_1 = []
Fibres_ABC_B_1 = []
Fibres_ABC_C_1 = []

# Преобразуем списки волокон в numpy массивы для удобства расчетов (один раз перед циклом)
Endo_Vecs = np.array([Fibres_XYZ_0_Endo_X, Fibres_XYZ_0_Endo_Y, Fibres_XYZ_0_Endo_Z]).T
Epi_Vecs  = np.array([Fibres_XYZ_0_Epi_X, Fibres_XYZ_0_Epi_Y, Fibres_XYZ_0_Epi_Z]).T

for ind in range(len(Closest_Endo)):
    # 1. Получаем координату gamma (глубина)
    gamma = M_XYZ_0_2D[ind][2]
    
    # 2. Находим индексы ближайших узлов
    idx_endo = Closest_Endo[ind][0]
    idx_epi  = Closest_Epi[ind][0]
    
    # 3. Берем вектора с поверхностей
    vec_endo = Endo_Vecs[idx_endo]
    vec_epi  = Epi_Vecs[idx_epi]
    
    # 4. Интерполируем вектор: (1-gamma)*Endo + gamma*Epi
    # Используем np.clip для gamma на случай ошибок в сетке, чтобы gamma была строго [0, 1]
    gamma_safe = np.clip(gamma, 0.0, 1.0)
    
    mixed_vec = (1.0 - gamma_safe) * vec_endo + gamma_safe * vec_epi
    
    # 5. Нормализуем вектор (делаем его длину равной 1)
    norm = np.linalg.norm(mixed_vec)
    if norm > 0:
        final_vec = mixed_vec / norm
    else:
        final_vec = vec_endo # На случай ошибки
        
    # 6. Записываем компоненты в списки
    Fibres_ABC_A_1.append(final_vec[0])
    Fibres_ABC_B_1.append(final_vec[1])
    Fibres_ABC_C_1.append(final_vec[2])
    if ind % 500 == 0:
        print(ind)

Fibres_ABC_Mesh1 = [Fibres_ABC_A_1, Fibres_ABC_B_1, Fibres_ABC_C_1]
Fibres_ABC_Mesh1 = list(zip(*Fibres_ABC_Mesh1))


# write carp
pts, elems, fiber, data = utils.read_carp(base_dir, mesh3d_input, return_surface=False)
utils.write_vtk(pts, elems, fiber, data, base_dir + "Fibres_Threshold_int_lin.vtk")
mname = base_dir + "Fibres_Threshold_int_lin"
utils.write_carp(pts, elems, Fibres_ABC_Mesh1, None, mname)

# write carp visualisation
mname = base_dir + "Aux_2_int_lin"
utils.write_carp(M_XYZ_0_Vol, elems, Fibres_ABC_Mesh1, None, mname)
shutil.copyfile(mname + ".pts", base_dir + output_file_name + ".vpts")
shutil.copyfile(mname + ".lon", base_dir + output_file_name + ".vec")

mname = base_dir + "UAC_Angles_Threshold_int_lin"
utils.write_carp(M_XYZ_0_Vol, elems, Fibres_ABC_Mesh1, None, mname)
