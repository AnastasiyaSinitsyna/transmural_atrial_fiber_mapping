#!/bin/bash
# =============================================================================
# END-TO-END UAC COORDINATE & FIBER MAPPING PIPELINE (2D)
# =============================================================================
# Automates patient-specific left atrial surface modeling for both endocardial
# and epicardial layers. Workflow includes: mesh preprocessing, landmark-based
# anatomical segmentation, Laplace-Dirichlet solves, UAC computation via
# geodesic cuts, and atlas-to-patient fiber orientation transfer.
# =============================================================================


# ==========================================
# ENDO CARDIAL PROCESSING BLOCK
# ==========================================

# 1. ENVIRONMENT & PATH CONFIGURATION
PROJECT="your_path_to_fiber_files"  # Directory containing atlas data & custom UAC scripts
DATA="your_path_to_main_directory"  # Working directory with patient meshes & simulation parameters
LAPath="your_path_to_endocardial_mesh" # Path to endocardial mesh in openCARP format       


# Laplace solution thresholds for anatomical region identification
PV_threshold=0.80     # Scalar field threshold for pulmonary vein ostia segmentation
LAA_threshold=0.35    # Scalar field threshold for left atrial appendage segmentation

index=1               # Pipeline iteration index (reserved for future batch processing)
export PYTHONPATH=$PROJECT  # Add custom UAC libraries to Python environment

# Atlas-derived fiber orientation directories
LAendofib_dir="$PROJECT/fibre_files/la/endo/l/"
LAepifib_dir="$PROJECT/fibre_files/la/epi/l/"

# Mesh filenames (input and output)
MeshName="Test_endo_hole"
MeshName_Labels="Test_endo_Labels"

# Files storing manually selected anatomical landmark coordinates
Labels_LA="main_points_to_par.txt"   # Primary landmarks (PV ostia, LAA apex/base)
Aux_LA="aux_points_to_par.txt"       # Auxiliary reference points for UAC geodesic cuts


# 2. MESH PREPROCESSING & TOPOLOGY CLEANING
# Convert VTK to openCARP native format
meshtool convert -imsh=Test_endo_hole.vtk -omsh=Test_endo_hole
# Resample vertices to improve surface quality and element uniformity
meshtool resample surfmesh -msh=Test_endo_hole -avrg=300 -outmsh=Test_endo_hole -surf_corr=0.95
# Fix topological defects (holes, non-manifold edges, inconsistent normals)
meshtool clean topology -msh=Test_endo_hole -outmsh=Test_endo_hole
# Export to STL for external visualization/inspection if needed
meshtool convert -imsh=Test_endo_hole -omsh=Test_endo_hole.stl
meshtool convert -imsh=Test_endo_hole.stl -omsh=Test_endo_hole


# 3. INTERACTIVE LANDMARK SELECTION
# Run PyVista-based GUI to manually pick anatomical coordinates on the mesh surface
python $DATA/scripts/0_choose_points_script.py


# STAGE 6: ANATOMICAL REGION BOUNDARY GENERATION
# Create initial Dirichlet boundary condition files (.vtx) for Laplace solves using picked landmarks
python $DATA/scripts/1_labels_generation.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName $PV_threshold $LAA_threshold $Labels_LA 


# STAGE 7: LAPLACE EQUATION SOLVES FOR ANATOMICAL REGIONS
# Solve ∇²φ = 0 with Dirichlet boundary conditions to define scalar fields for each target structure
openCARP +F $LAPath/laplace_solutions/laplace_PV1.par -simID MV_PV1   # PV 1
openCARP +F $LAPath/laplace_solutions/laplace_PV2.par -simID MV_PV2   # PV 2
openCARP +F $LAPath/laplace_solutions/laplace_PV3.par -simID MV_PV3   # PV 3
openCARP +F $LAPath/laplace_solutions/laplace_PV4.par -simID MV_PV4   # PV 4
openCARP +F $LAPath/laplace_solutions/laplace_LAA.par -simID  MV_LAA  # Left Atrial Appendage


# STAGE 8: REGION LABEL INTEGRATION
# Apply thresholds to solved scalar fields and assign discrete anatomical labels to mesh nodes/elements
python $DATA/scripts/2_labels_insert.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName $MeshName_Labels $PV_threshold $LAA_threshold 

# Change working directory to mesh location for downstream commands
cd $LAPath

# Generate placeholder fiber orientations to ensure mesh compatibility with openCARP solvers
meshtool generate fibres -msh=$MeshName -tags=11,13,21,23,25,27 -outmsh=$MeshName -op=1
meshtool generate fibres -msh=$MeshName_Labels -tags=11,13,21,23,25,27 -outmsh=$MeshName_Labels -op=1


# STAGE 9: UAC BOUNDARY & GEODESIC PATH COMPUTATION
# Compute shortest geodesic paths to partition the surface into anterior/posterior and septal/lateral domains
python $DATA/scripts/3_uac_boundary_generator.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName_Labels 11 13 21 23 25 27 $Aux_LA


# STAGE 10: UAC COORDINATE LAPLACE SOLVES
# Solve for Posterior-Anterior (PA) and Left-Septal (LS) coordinates on the labelled surface
openCARP +F $LAPath/laplace_solutions/laplace_PA.par -simID PA_UAC_1
openCARP +F $LAPath/laplace_solutions/laplace_LS.par -simID LS_UAC_1


# STAGE 11: UAC COORDINATE COMPUTATION & 2D UNFOLDING
echo "=====New UAC====="
# Compute final 2D UAC coordinates (α, β), apply anterior/posterior rescaling, and export mapped mesh
python $DATA/scripts/4_uac_mapper.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName_Labels 11 13 21 23 25 27 $Aux_LA 


# STAGE 14: FIBER ORIENTATION TRANSFER & MAPPING
echo "=====Add fibres2 ====="
# Map atlas-derived fiber vectors to patient mesh using KD-tree nearest-neighbor matching in UAC space
python $DATA/scripts/5_fibre_mapping.py "$LAPath/" "$DATA/fibre_files/la/endo/l/" "$LAPath/laplace_solutions/" $MeshName_Labels Labelled.lon $MeshName_Labels





# ==========================================
# EPI CARDIAL PROCESSING BLOCK
# ==========================================

# 1. ENVIRONMENT & PATH CONFIGURATION (Epicardium)
PROJECT="your_path_to_fiber_files"
DATA="your_path_to_main_directory"
LAPath="your_path_to_epicardial_mesh"  # Path to epicardial mesh in openCARP format

PV_threshold=0.8     # Epicardium-specific threshold for pulmonary veins
LAA_threshold=0.35   # Epicardium-specific threshold for left atrial appendage

index=1
export PYTHONPATH=$PROJECT
LAendofib_dir="$PROJECT/fibre_files/la/endo/l/"
LAepifib_dir="$PROJECT/fibre_files/la/epi/l/"

MeshName="Test_epi_hole"
MeshName_Labels="Test_epi_Labels"

Labels_LA="main_points_to_par.txt"
Aux_LA="aux_points_to_par.txt"


# 2. MESH PREPROCESSING & CONVERSION (Epicardium)
meshtool convert -imsh=Test_epi_hole.vtk -omsh=Test_epi_hole
meshtool resample surfmesh -msh=Test_epi_hole -avrg=300 -outmsh=Test_epi_hole -surf_corr=0.95
meshtool clean topology -msh=Test_epi_hole -outmsh=Test_epi_hole
meshtool convert -imsh=Test_epi_hole -omsh=Test_epi_hole.stl
meshtool convert -imsh=Test_epi_hole.stl -omsh=Test_epi_hole


# 3. INTERACTIVE LANDMARK SELECTION (Epicardium)
python $DATA/scripts/0_choose_points_script.py
python $DATA/scripts/0_choose_points_script_aux.py  # Additional auxiliary points for epicardial cuts


# STAGE 6: ANATOMICAL REGION BOUNDARY GENERATION (Epicardium)
python $DATA/scripts/1_labels_generation.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName $PV_threshold $LAA_threshold $Labels_LA


# STAGE 7: LAPLACE EQUATION SOLVES FOR ANATOMICAL REGIONS (Epicardium)
openCARP +F $LAPath/laplace_solutions/laplace_PV1.par -simID MV_PV1
openCARP +F $LAPath/laplace_solutions/laplace_PV2.par -simID MV_PV2
openCARP +F $LAPath/laplace_solutions/laplace_PV3.par -simID MV_PV3
openCARP +F $LAPath/laplace_solutions/laplace_PV4.par -simID MV_PV4
openCARP +F $LAPath/laplace_solutions/laplace_LAA.par -simID  MV_LAA


# STAGE 8: REGION LABEL INTEGRATION (Epicardium)
python $DATA/scripts/2_labels_insert.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName $MeshName_Labels $PV_threshold $LAA_threshold 

cd $LAPath

# Generate placeholder fibers for solver compatibility
meshtool generate fibres -msh=$MeshName -tags=11,13,21,23,25,27 -outmsh=$MeshName -op=1
meshtool generate fibres -msh=$MeshName_Labels -tags=11,13,21,23,25,27 -outmsh=$MeshName_Labels -op=1

# Optional secondary cleaning step (currently commented out)
# meshtool resample surfmesh -msh=Test_epi_Labels -avrg=300 -outmsh=Test_epi_Labels -surf_corr=0.95
# meshtool clean topology -msh=Test_epi_Labels -outmsh=Test_epi_Labels


# STAGE 9: UAC BOUNDARY & GEODESIC PATH COMPUTATION (Epicardium)
python $DATA/scripts/3_uac_boundary_generator.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName_Labels 11 13 21 23 25 27 $Aux_LA


# STAGE 10: UAC COORDINATE LAPLACE SOLVES (Epicardium)
openCARP +F $LAPath/laplace_solutions/laplace_PA.par -simID PA_UAC_1
openCARP +F $LAPath/laplace_solutions/laplace_LS.par -simID LS_UAC_1


# STAGE 11: UAC COORDINATE COMPUTATION & 2D UNFOLDING (Epicardium)
echo "=====New UAC====="
python $DATA/scripts/4_uac_mapper.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName_Labels 11 13 21 23 25 27 $Aux_LA 


# STAGE 14: FIBER ORIENTATION TRANSFER & MAPPING (Epicardium)
python $DATA/scripts/5_fibre_mapping.py "$LAPath/" "$PROJECT/fibre_files/la/epi/l/" "$LAPath/laplace_solutions/" $MeshName_Labels Labelled.lon $MeshName_Labels
