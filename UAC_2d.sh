#Путь к атласу
PROJECT=/home/nastasiya/jove
# Путь к основной папке со скриптами и параметрами
DATA=/home/nastasiya/jove
# Путь к мешу в формател опенкарп
LAPath=/home/nastasiya/jove/mesh/Zvag/Endo

# Задание порогов для уравнения лапласа
# для вен
PV_threshold=0.80
# для ушка
LAA_threshold=0.35

index=1

export PYTHONPATH=$PROJECT
LAendofib_dir="$PROJECT/fibre_files/la/endo/l/"
LAepifib_dir="$PROJECT/fibre_files/la/epi/l/"

# имя меша изначального, endo
MeshName="Zvag_endo_hole"
MeshName_Labels="Zvag_endo_Labels"

# Файлы с точками для выбора регионов 
Labels_LA="main_points_to_par.txt"
Aux_LA="aux_points_to_par.txt"

# Очистка меша
meshtool convert -imsh=Zvag_endo_hole.vtk -omsh=Zvag_endo_hole
meshtool resample surfmesh -msh=Zvag_endo_hole -avrg=300 -outmsh=Zvag_endo_hole -surf_corr=0.95
meshtool clean topology -msh=Zvag_endo_hole -outmsh=Zvag_endo_hole
meshtool convert -imsh=Zvag_endo_hole -omsh=Zvag_endo_hole.stl
meshtool convert -imsh=Zvag_endo_hole.stl -omsh=Zvag_endo_hole

python $DATA/scripts/0_choose_points_script.py
python $DATA/scripts/0_choose_points_script_aux.py

#stage 6 Выбор границ регионов для ур-ний лапласа
python $DATA/scripts/1_labels_generation.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName $PV_threshold $LAA_threshold $Labels_LA 

#stage 7 Решения ур-ний лапласа для регионов
openCARP +F $LAPath/laplace_solutions/laplace_PV1.par -simID MV_PV1
openCARP +F $LAPath/laplace_solutions/laplace_PV2.par -simID MV_PV2
openCARP +F $LAPath/laplace_solutions/laplace_PV3.par -simID MV_PV3
openCARP +F $LAPath/laplace_solutions/laplace_PV4.par -simID MV_PV4
openCARP +F $LAPath/laplace_solutions/laplace_LAA.par -simID MV_LAA

#stage 8 Внедрение регионов обратно
python $DATA/scripts/2_labels_insert.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName $MeshName_Labels $PV_threshold $LAA_threshold 

# переходим в путь к мешу
cd $LAPath

# генерируем стандартные волокна для мешей (чтобы не ломались)
meshtool generate fibres -msh=$MeshName -tags=11,13,21,23,25,27 -outmsh=$MeshName -op=1
meshtool generate fibres -msh=$MeshName_Labels -tags=11,13,21,23,25,27 -outmsh=$MeshName_Labels -op=1

# доп очистка
#meshtool resample surfmesh -msh=Zvag_endo_Labels -avrg=300 -outmsh=Zvag_endo_Labels  -surf_corr=0.95
#meshtool clean topology -msh=Zvag_endo_Labels -outmsh=Zvag_endo_Labels


#stage 9 Вычисление старых атриальных координат (геодезические линии)
python $DATA/scripts/3_uac_boundary_generator.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName_Labels 11 13 21 23 25 27 $Aux_LA


#stage 10 аппроксимация в опенкарпе

openCARP +F $LAPath/laplace_solutions/laplace_PA.par -simID PA_UAC_1
openCARP +F $LAPath/laplace_solutions/laplace_LS.par -simID LS_UAC_1

#_____________________________________________________________________________

#stage 11 Вычисление и разворот
echo "=====New UAC====="
python $DATA/scripts/4_uac_mapper.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName_Labels 11 13 21 23 25 27 $Aux_LA 


#_________Генерация волокон________#
#stage 14
echo "=====Add fibres2 ====="
python $DATA/scripts/5_fibre_mapping.py "$LAPath/" "$DATA/fibre_files/la/endo/l/" "$LAPath/laplace_solutions/" $MeshName_Labels Labelled.lon $MeshName_Labels





###################################################################################
#########################    Epicardium    ########################################
###################################################################################

#Путь к атласу
PROJECT=/home/nastasiya/jove

# Путь к основной папке со скриптами и параметрами
DATA=/home/nastasiya/jove
# Путь к мешу в формател опенкарп
LAPath=/home/nastasiya/jove/mesh/Zvag/Epi

# Задание порогов для уравнения лапласа
# для вен
PV_threshold=0.8
# для ушка
LAA_threshold=0.35

index=1

export PYTHONPATH=$PROJECT
LAendofib_dir="$PROJECT/fibre_files/la/endo/l/"
LAepifib_dir="$PROJECT/fibre_files/la/epi/l/"

# имя меша изначального, endo
MeshName="Zvag_epi_hole"
MeshName_Labels="Zvag_epi_Labels"

# Файлы с точками для выбора регионов 
Labels_LA="main_points_to_par.txt"
Aux_LA="aux_points_to_par.txt"


meshtool convert -imsh=Zvag_epi_hole.vtk -omsh=Zvag_epi_hole# Очистка меша
meshtool resample surfmesh -msh=Zvag_epi_hole -avrg=300 -outmsh=Zvag_epi_hole -surf_corr=0.95
meshtool clean topology -msh=Zvag_epi_hole -outmsh=Zvag_epi_hole
meshtool convert -imsh=Zvag_epi_hole -omsh=Zvag_epi_hole.stl
meshtool convert -imsh=Zvag_epi_hole.stl -omsh=Zvag_epi_hole



python $DATA/scripts/0_choose_points_script.py
python $DATA/choose_points_script_aux.py

#stage 6 Выбор границ регионов для ур-ний лапласа
python $DATA/scripts/1_labels_generation.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName $PV_threshold $LAA_threshold $Labels_LA

#stage 7 Решения ур-ний лапласа для регионов
openCARP +F $LAPath/laplace_solutions/laplace_PV1.par -simID MV_PV1
openCARP +F $LAPath/laplace_solutions/laplace_PV2.par -simID MV_PV2
openCARP +F $LAPath/laplace_solutions/laplace_PV3.par -simID MV_PV3
openCARP +F $LAPath/laplace_solutions/laplace_PV4.par -simID MV_PV4
openCARP +F $LAPath/laplace_solutions/laplace_LAA.par -simID MV_LAA

#stage 8 Внедрение регионов обратно
python $DATA/scripts/2_labels_insert.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName $MeshName_Labels $PV_threshold $LAA_threshold 

# переходим в путь к мешу
cd $LAPath

# генерируем стандартные волокна для мешей (чтобы не ломались)
meshtool generate fibres -msh=$MeshName -tags=11,13,21,23,25,27 -outmsh=$MeshName -op=1
meshtool generate fibres -msh=$MeshName_Labels -tags=11,13,21,23,25,27 -outmsh=$MeshName_Labels -op=1

#meshtool resample surfmesh -msh=Zvag_epi_Labels -avrg=300 -outmsh=Zvag_epi_Labels  -surf_corr=0.95
#meshtool clean topology -msh=Zvag_epi_Labels -outmsh=Zvag_epi_Labels
#meshtool convert -imsh=Zvag_epi_Labels -omsh=Zvag_epi_Labels.stl
#meshtool convert -imsh=Zvag_epi_Labels.stl -omsh=Zvag_epi_Labels

#stage 9 Вычисление старых атриальных координат (геодезические линии)
python $DATA/scripts/3_uac_boundary_generator.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName_Labels 11 13 21 23 25 27 $Aux_LA

#stage 10 аппроксимация в опенкарпе

openCARP +F $LAPath/laplace_solutions/laplace_PA.par -simID PA_UAC_1
openCARP +F $LAPath/laplace_solutions/laplace_LS.par -simID LS_UAC_1

#_____________________________________________________________________________

#stage 11 Вычисление и разворот
echo "=====New UAC====="
python $DATA/scripts/4_uac_mapper.py "$LAPath/" "$LAPath/laplace_solutions/" $MeshName_Labels 11 13 21 23 25 27 $Aux_LA 

#_________Генерация волокон________#
#stage 14
python $DATA/scripts/5_fibre_mapping.py "$LAPath/" "$PROJECT/fibre_files/la/epi/l/" "$LAPath/laplace_solutions/" $MeshName_Labels Labelled.lon $MeshName_Labels
