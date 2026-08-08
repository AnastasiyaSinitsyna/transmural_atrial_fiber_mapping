
#Путь к атласу
PROJECT=/home/nastasiya/jove
# Путь к основной папке со скриптами и параметрами
DATA=/home/nastasiya/jove
# Путь к мешу в формател опенкарп
LAPath=/home/nastasiya/jove/mesh/Test

export PYTHONPATH=$PROJECT

cd $LAPath/Vol

python $DATA/scripts/shell_interpolation.py 
#meshtool resample mesh -msh=Test_solid_Labels.vtk -avrg=1500 -outmsh=Test_solid_Labels -surf_corr=0.95
meshtool resample mesh -msh=Test_solid_Labels.vtk -min=2000 -max=5000 -outmsh=Test_solid_Labels
meshtool smooth mesh -msh=Test_solid_Labels -tags=* -outmsh=Test_solid_Labels

#meshtool convert -imsh=Test_solid_Labels.vtk -omsh=Test_solid_Labels
meshtool clean topology -msh=Test_solid_Labels -outmsh=Test_solid_Labels
meshtool extract surface -msh=Test_solid_Labels -surf=Test_solid_Labels

python $DATA/scripts/6_assign_volumetric_uac.py "$LAPath/Vol/" "$LAPath/Endo/" "$LAPath/Epi/" Test_solid_Labels Test_endo_Labels Test_epi_Labels

openCARP +F $LAPath/Vol/laplace_solutions/laplace_alpha.par -simID Alpha
openCARP +F $LAPath/Vol/laplace_solutions/laplace_beta.par -simID Beta
openCARP +F $LAPath/Vol/laplace_solutions/laplace_gamma.par -simID Gamma

####

python $DATA/scripts/7_assemble_volumetric_uac_mesh.py "$LAPath/Vol/" "$LAPath/Endo/" "$LAPath/Epi/" Test_solid_Labels Test_endo_Labels Test_epi_Labels


cp "$LAPath/Vol/Test_solid_Labels.elem" "$LAPath/Vol/Mesh_UAC_3D.elem"
cp "$LAPath/Vol/Test_solid_Labels.surf" "$LAPath/Vol/Mesh_UAC_3D.surf"

#_________________________________

#now threshold fibres LA
python $DATA/scripts/8_fibre_mapping_with_threshold.py "$LAPath/Vol/" Test_solid_Labels Mesh_UAC_3D "$LAPath/Endo/" Test_endo_Labels Test_endo_Labels.vec "$LAPath/Epi/" Test_epi_Labels Test_epi_Labels.vec Fibre_Threshold.vec
python $DATA/scripts/8_1_fibre_linear_transmural_interpolation.py "$LAPath/Vol/" Test_solid_Labels Mesh_UAC_3D "$LAPath/Endo/" Test_endo_Labels Test_endo_Labels.vec "$LAPath/Epi/" Test_epi_Labels Test_epi_Labels.vec Fibre_Linear.vec

