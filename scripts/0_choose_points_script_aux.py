'''
Selecting points on the mesh surface
'''
# The order of point selection:
	# Main points
		#1. Right superior pulmonary vein
		#2. Right inferior pulmonary vein
		#3. Left inferior pulmonary vein
		#4. Left superior pulmonary vein
		#5. Tip of the auricle of the left atrium
		#6. Base of the auricle of the left atrium

	# Auxiliary points
	#1. Front wall
	#2. Back wall
	#3. The base of the left superior pulmonary vein
	#4. The base of the right superior pulmonary vein


# Library import
import pyvista as pv
import numpy as np
import pandas as pd
import os

# The path, the name of the source mesh, and the way the points are recorded
# Directory containing the mesh file
path = '/home/nastasiya/jove/mesh/Zvag/Endo/'
#meshname = 'Ale_Epi_hole.stl'
meshname = 'Zvag_endo_hole.stl'

# Output filenames for the two point sets
aux_outname = 'aux_points_to_par.txt'

 
mesh = pv.read(path + meshname)

picked_points = []

def picking(point):
    mesh = pv.read(path + meshname)
    pl.add_mesh(mesh)
    pl.add_point_labels(point, [f"{point[0]:.2f}, {point[1]:.2f}, {point[2]:.2f}"])
    print(point)
    picked_points.append(point)
	
pl = pv.Plotter()
pl.add_mesh(mesh, show_edges=True)
pl.enable_surface_picking(show_message="Pick 4 points in order:\n"
                 "1-4: Auxiliary landmarks\n"
                 "Press 'q' or close the window to finish.", callback=picking, left_clicking=False, show_point=False)
pl.show()

print(picked_points)
# Convert to numpy array for safe and consistent slicing
picked_points = np.array(picked_points)

# Split into main (first 6) and auxiliary (next 4) sets
aux_points = picked_points[0:4]

# Save main points to CSV/TXT
aux_path = os.path.join(path, aux_outname)
pd.DataFrame(aux_points).to_csv(aux_path, header=None, index=False, sep=',')
print(f" Successfully saved {len(aux_points)} auxiliary points to '{aux_outname}'")

print("Point selection pipeline completed.")