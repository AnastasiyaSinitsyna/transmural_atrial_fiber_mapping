# Transmural fiber mapping code 
A computational pipeline for reconstructing patient-specific 3D left atrial models with depth-resolved myocardial fiber architecture. 

## Methodology



## Pre-processing
For the correct start of the fiber reconstruction pipeline and electrodynamic modeling of the left atrium, one of the following data sets is required:
- **CT-derived**: 
	(i) Segmentations of the left atrial (LA) myocardium and blood pool
	(ii) raw volumetric CT scans (`.nrrd` format)
	(iii) pre-processed endocardial, epicardial, and wall thickness meshes.

- **MRI-derived**: 
	(i) Segmentations of the LA myocardium and blood pool, or
	(ii) pre-processed endocardial, epicardial, and wall thickness meshes.

**Segmentation Guidelines**
- CT segmentation can be performed in accordance with the standardized protocol developed by our group. A detailed guide containing filter settings, threshold values, and validation procedures is available in the [CT_Segmentation_Guide.pdf](https://github.com/AnastasiyaSinitsyna/transmural_atrial_fiber_mapping/blob/main/CT_Segmentation_Guide/CT_Segmentation_Guide.pdf). 
- For automated and reproducible segmentation of MRI data, it is recommended to use the [nnU-Net framework](https://github.com/MIC-DKFZ/nnUNet?spm=a2ty_o01.29997173.0.0.48c655fbGORS4Q), adapted to the tasks of cardiological imaging and showing high accuracy on thin-walled structures of the atria.

All geometric models must be registered to a unified coordinate system. When utilizing pre-processed models, verify that the endocardial and epicardial surfaces are topologically compatible, exhibit no gaps at the pulmonary vein ostia or mitral annulus, and are properly prepared for volumetric tetrahedralization.


## Requirements & Dependencies
This pipeline relies on the following open-source tools and publicly available datasets. Please cite them appropriately if you use this framework in your research.

| Tool / Dataset | Role in Pipeline | Link | Citation |
|----------------|------------------|------|----------------------|
| **openCARP** (v.12.0+)| Electrophysiology simulations (Laplace solves, monodomain/bidomain propagation) | [Website](https://opencarp.org/) [GitHub](https://git.opencarp.org/openCARP/openCARP)| Plank G., et al. (2021). The openCARP simulation environment for cardiac electrophysiology. *Computer Methods and Programs in Biomedicine*, 208, 106223. |
| **Meshtool** (v.2.1+)| Mesh generation, surface extraction, conversion, and topology cleaning | [GitHub](https://bitbucket.org/aneic/meshtool.git) | Neic A., et al. (2020). Automating image-based mesh generation and manipulation tasks in cardiac modeling workflows using meshtool. *SoftwareX*, 11, 100454. |
| **Meshalyzer** | Visualization of fiber fields, activation maps, and scalar coordinate fields | [GitHub](https://git.opencarp.org/openCARP/meshalyzer) | Vigmond E., et al. *meshalyzer*: Open-source software for cardiac simulation visualization. [Software] |
| **Human Atrial Fibre Atlas** | Reference fiber orientations for endocardial and epicardial surfaces | [Paper 1](https://doi.org/10.1007/s10439-020-02525-w) [Paper 2]([https://doi.org/10.1161/CIRCEP.116.004133](https://doi.org/10.1161/CIRCEP.116.004133?spm=a2ty_o01.29997173.0.0.48c655fbGORS4Q&file=CIRCEP.116.004133)) [Data Repository](https://zenodo.org/records/4723288) | Roney C. H., et al. (2021). Constructing a human atrial fibre atlas. *Annals of Biomedical Engineering*, 49(1), 233–250; Pashakhanloo, F., Herzka, D. A., Ashikaga, H., Mori, S., Gai, N., Bluemke, D. A., Trayanova, N. A., & McVeigh, E. R.** (2016). Myofiber architecture of the human atria as revealed by submillimeter diffusion tensor imaging. _Circulation: Arrhythmia and Electrophysiology_, _9_(4), e004133.|


## Installation & Setup
1. Clone the repository
```
git clone https://github.com/.../atrial-fiber-modeling.git
cd atrial-fiber-modeling
```

2. Working with this pipeline is meant in a conda virtual environment. It includes related python packages:
```
numpy>=1.24
scipy>=1.11
scikit-learn>=1.3
vtk>=9.3
pyvista>=0.42
pandas>=2.0
matplotlib>=3.7
```
You can create it with all the dependencies using the following command:
```
conda env create -f environment.yml
```
To activate it:
```
conda activate fibers
```

3. Set environment variables (adjust paths to your system)
```
export DATA=/path/to/main/project
export LAPath=/path/to/patient/mesh
export PROJECT=/path/to/UAC_Codes
export PYTHONPATH=$PROJECT
```

4. To install external tools please follow official guides for [openCARP], [Meshtool] and [Meshalyzer].

## Usage
...

The workflow follows the protocol detailed in the manuscript. Run steps sequentially:

```
bash UAC_2d.sh $LAPath $DATA $PROJECT
bash UAC_3d.sh $LAPath $DATA $PROJECT
```
*See UAC_2d.sh and UAC_3d.sh for full parameterization and details*


## Input & Output Formats
Inputs:
- `*.nrrd` / `*.vtk` : Raw segmented atrial meshes
- `*.txt` / `*.vtx` : Anatomical landmark coordinates & Dirichlet boundary files
- `laplace_*.par` : openCARP parameter files for UAC solves
- Atlas fiber files: `*_fibers.vec` (Human Atrial Fibre Atlas)

Outputs:
- `*_Labels.vtk` : Tagged surface/volumetric meshes (PVs, LAA, MV)
- `Alpha.vtx`, `Beta.vtx`, `Gamma.vtx` : UAC coordinate boundary files
- `Fibre_*.vec`, `Fibre_*.vpts` : openCARP-ready fiber orientation fields
- `Mesh_UAC_3D.vtk` : Volumetric mesh with embedded (α, β, γ) coordinates

