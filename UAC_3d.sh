#!/bin/bash
# =============================================================================
# VOLUMETRIC UAC COORDINATE ASSIGNMENT & TRANSMURAL FIBER MAPPING PIPELINE
# =============================================================================
# This script automates the volumetric processing stage of the atrial modeling workflow.
# It: (1) prepares the 3D mesh, (2) solves Laplace equations for 3D UAC coordinates (α, β, γ),
# (3) assembles the 3D coordinate mesh, and (4) generates both threshold-based and 
# linearly interpolated transmural fiber orientation fields for openCARP simulations.
# =============================================================================

# 1. ENVIRONMENT & PATH CONFIGURATION
PROJECT="your_path_to_fiber_files"         # Directory containing UAC scripts & atlas data
DATA="your_path_to_main_directory"         # Working directory for scripts & parameters
LAPath="your_path_to_endocardial_mesh"     # Patient-specific mesh directory
export PYTHONPATH=$PROJECT                 # Add custom UAC libraries to Python path

# Change to volumetric mesh directory
cd $LAPath/Vol

# 2. VOLUMETRIC MESH PREPROCESSING
# Fix topological defects (holes, non-manifold edges, inconsistent normals) to ensure watertight geometry
meshtool clean topology -msh=Zvag_solid_Labels -outmsh=Zvag_solid_Labels
# Resample volumetric mesh to improve element quality and uniformity
meshtool resample mesh -msh=Zvag_solid_Labels -avrg=300 -outmsh=Zvag_solid_Labels -surf_corr=0.95
# Transfer the tag of the veins and auricle of the atrium from the endocardium and epicardium deep into the solid mesh
python $DATA/scripts/shell_interpolation.py
# Extract outer surface mesh from the volumetric model for boundary condition assignment
meshtool extract surface -msh=Zvag_solid_Labels -surf=Zvag_solid_Labels

# STAGE 6: ASSIGN 3D UAC BOUNDARY CONDITIONS TO VOLUMETRIC SURFACE NODES
# Maps α, β coordinates from the endocardial surface and assigns binary γ labels (0=endo, 1=epi)
# based on proximity to endocardial/epicardial surfaces via KD-tree nearest-neighbor matching.
# Outputs: Alpha.vtx, Beta.vtx, Gamma.vtx (Dirichlet boundary condition files for openCARP)
python $DATA/scripts/6_assign_volumetric_uac.py "$LAPath/Vol/" "$LAPath/Endo/" "$LAPath/Epi/" Zvag_solid_Labels Zvag_endo_Labels Zvag_epi_Labels

# STAGE 7: SOLVE LAPLACE EQUATIONS FOR VOLUMETRIC UAC FIELDS
# Computes continuous scalar fields for α, β, and γ across the atrial wall thickness using openCARP
# with Dirichlet boundary conditions defined in the previous step.
openCARP +F $DATA/laplace_solutions/laplace_alpha.par -simID Alpha
openCARP +F $DATA/laplace_solutions/laplace_beta.par -simID Beta
openCARP +F $DATA/laplace_solutions/laplace_gamma.par -simID Gamma

# STAGE 8: ASSEMBLE 3D UAC COORDINATE MESH
# Reads the solved scalar fields (.igb) and constructs a 3D coordinate mesh (α, β, γ) 
# where each node's position corresponds to its parametric UAC values.
python $DATA/scripts/7_assemble_volumetric_uac_mesh.py "$LAPath/Vol/" "$LAPath/Endo/" "$LAPath/Epi/" Zvag_solid_Labels Zvag_endo_Labels Zvag_epi_Labels

# Attach element and surface topology files to the newly assembled UAC coordinate mesh
cp "$LAPath/Vol/Zvag_solid_Labels.elem" "$LAPath/Vol/Mesh_UAC_3D.elem"
cp "$LAPath/Vol/Zvag_solid_Labels.surf" "$LAPath/Vol/Mesh_UAC_3D.surf"

# STAGE 9: TRANSMURAL FIBER ORIENTATION MAPPING
echo "Generating threshold-based and linearly interpolated fiber fields..."

# Threshold-based interpolation (step-wise transition at γ = 0.5)
# Elements in the inner half of the wall (γ < 0.5) inherit endocardial fiber directions,
# while elements in the outer half (γ ≥ 0.5) inherit epicardial directions.
python $DATA/scripts/8_fibre_mapping_with_threshold.py "$LAPath/Vol/" Zvag_solid_Labels Mesh_UAC_3D "$LAPath/Endo/" Zvag_endo_Labels Zvag_endo_Labels.vec "$LAPath/Epi/" Zvag_epi_Labels Zvag_epi_Labels.vec Fibre_Threshold.vec

# Linear transmural interpolation (continuous gradient from endocardium to epicardium)
# Computes F(γ) = (1-γ)·F_endo + γ·F_epi for each element, followed by vector normalization.
# This preserves physiological continuity of atrial microstructure across the wall thickness.
python $DATA/scripts/8_1_fibre_linear_transmural_interpolation.py "$LAPath/Vol/" Zvag_solid_Labels Mesh_UAC_3D "$LAPath/Endo/" Zvag_endo_Labels Zvag_endo_Labels.vec "$LAPath/Epi/" Zvag_epi_Labels Zvag_epi_Labels.vec Fibre_Linear.vec
