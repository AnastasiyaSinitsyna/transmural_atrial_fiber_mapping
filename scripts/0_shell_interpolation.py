#!/usr/bin/env python3
"""
Shell Interpolation & Volumetric Tag Mapping Pipeline
=====================================================
This script interpolates anatomical region tags from surface meshes (epicardium + endocardium)
into a volumetric atrial mesh using VTK's point interpolation and nearest-tag rounding.
The resulting volumetric mesh contains cell-level tags suitable for electrophysiological simulations.
"""

import vtk
import numpy as np
import pyvista as pv
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

# =============================================================================
# 1. LOAD AND COMBINE SURFACE MESHES
# =============================================================================
# Load epicardial and endocardial surface meshes
epi_surface = pv.read('/home/nastasiya/jove/mesh/Test/Epi/Test_epi_Labels.vtk')
endo_surface = pv.read('/home/nastasiya/jove/mesh/Test/Endo/Test_endo_Labels.vtk')

# Combine both surfaces into a single dataset for unified processing
combined_surfaces = epi_surface + endo_surface

# Optional: Visualize the combined surface (requires a display)
# combined_surfaces.plot(show_edges=False)

# =============================================================================
# 2. EXTRACT SURFACE TAGS AND POINT COORDINATES
# =============================================================================
# Extract cell (element) tags from the combined surface mesh
elem_tags = vtk_to_numpy(combined_surfaces.GetCellData().GetArray('data'))
print(f"Number of surface elements: {len(elem_tags)}")
print(f"Surface element tags: {elem_tags}")

# Extract point coordinates from the combined surface mesh
surface_points = vtk_to_numpy(combined_surfaces.GetPoints().GetData())
print(f"Number of surface points: {len(surface_points)}")

# =============================================================================
# 3. INTERPOLATE CELL TAGS TO POINT TAGS
# =============================================================================
def elem_to_point_average(mesh, cell_tag_name='data', point_tag_name="PointTags"):
    """
    Interpolate cell (element) tags to point (node) tags.
    For each point, the tag is assigned as the MAXIMUM tag value among all connected cells.
    (Note: Preserves original pipeline behavior; true averaging would divide by point_counts)
    """
    cell_tags = vtk_to_numpy(mesh.GetCellData().GetArray(cell_tag_name))
    
    # Initialize point tag array
    point_tags = np.zeros(mesh.GetNumberOfPoints(), dtype=np.float64)
    
    # Iterate over all cells and propagate tags to their nodes
    for cell_id in range(mesh.GetNumberOfCells()):
        cell = mesh.GetCell(cell_id)
        num_points = cell.GetNumberOfPoints()
        
        for i in range(num_points):
            point_id = cell.GetPointId(i)
            # Assign the maximum cell tag encountered for this point
            if point_tags[point_id] < cell_tags[cell_id]:
                point_tags[point_id] = cell_tags[cell_id]
                
    # Convert to VTK array and attach to point data
    point_tags_array = numpy_to_vtk(point_tags.astype(int))
    point_tags_array.SetName(point_tag_name)
    mesh.GetPointData().AddArray(point_tags_array)
    
    return mesh

# Apply cell-to-point tag interpolation
surface_with_point_tags = elem_to_point_average(
    combined_surfaces, 
    cell_tag_name="data", 
    point_tag_name="InterpolatedTags"
)

# Verify interpolated point tags
print("Interpolated point tags:")
print(vtk_to_numpy(surface_with_point_tags.GetPointData().GetArray('InterpolatedTags')))

# =============================================================================
# 4. LOAD VOLUMETRIC MESH & SETUP INTERPOLATOR
# =============================================================================
# Load the volumetric finite-element mesh
volume_reader = vtk.vtkUnstructuredGridReader()
volume_reader.SetFileName('/home/nastasiya/jove/mesh/Test/Vol/Test_solid_Labels.vtk')
volume_reader.Update()
volume_mesh = volume_reader.GetOutput()

# Configure VTK point interpolator to map surface point tags into the volume
interpolator = vtk.vtkPointInterpolator()
interpolator.SetInputData(volume_mesh)               # Target: volumetric mesh points
interpolator.SetSourceData(surface_with_point_tags)  # Source: surface point tags
interpolator.SetKernel(vtk.vtkLinearKernel())        # Linear interpolation kernel
interpolator.SetNullPointsStrategyToClosestPoint()   # Fallback for points outside convex hull

# Execute interpolation
interpolator.Update()
solid_with_interpolated_tags = interpolator.GetOutput()

# Verify interpolated point tags in the volume
print("Volumetric interpolated point tags:")
print(solid_with_interpolated_tags.GetPointData().GetArray('InterpolatedTags'))

# =============================================================================
# 5. NEAREST-TAG ROUNDING UTILITY
# =============================================================================
class NearestRounder:
    """Utility class for rounding numerical values to the nearest allowed anatomical tag."""
    
    def __init__(self, allowed_values):
        self.allowed_values = sorted(allowed_values)
        
    def round(self, value):
        """Round a single value to the closest allowed tag."""
        return min(self.allowed_values, key=lambda x: abs(x - value))
        
    def round_array(self, values):
        """Round an array/list of values."""
        return [self.round(x) for x in values]
        
    def get_allowed_range(self):
        """Return the minimum and maximum allowed tag values."""
        return min(self.allowed_values), max(self.allowed_values)

# Instantiate rounder with the expected anatomical region identifiers
# 11: LA body, 13: LAA, 21: LSPV, 23: LIPV, 25: RSPV, 27: RIPV
tag_rounder = NearestRounder([11, 13, 21, 23, 25, 27])

# =============================================================================
# 6. MAP INTERPOLATED POINT TAGS BACK TO CELL TAGS
# =============================================================================
def points_to_elems_volume_weighted(mesh, point_tag_name="InterpolatedTags", elem_tag_name="data", tag_name="elemTag"):
    """
    Map interpolated point tags back to cell (element) tags.
    For each element, the tag is assigned as the MAXIMUM value among its nodes,
    followed by rounding to the nearest valid anatomical tag.
    """
    point_tags = vtk_to_numpy(mesh.GetPointData().GetArray(point_tag_name))
    elem_tags = np.zeros(mesh.GetNumberOfCells(), dtype=np.float64)
    
    for elem_id in range(mesh.GetNumberOfCells()):
        cell = mesh.GetCell(elem_id)
        num_points = cell.GetNumberOfPoints()
        
        # Collect point tags for this element
        elem_point_vals = []
        for i in range(num_points):
            point_id = cell.GetPointId(i)
            elem_point_vals.append(point_tags[point_id])
            
        # Assign the maximum point tag to the element
        elem_tags[elem_id] = max(elem_point_vals)
        
    # Round interpolated values to the nearest valid anatomical tag
    elem_tags_rounded = np.array(tag_rounder.round_array(elem_tags), dtype=int)
    
    # Convert to VTK array and attach to cell data
    elem_tags_array = numpy_to_vtk(elem_tags_rounded)
    elem_tags_array.SetName(tag_name)
    
    mesh.GetCellData().AddArray(elem_tags_array)
    # Clean up temporary point data array
    mesh.GetPointData().RemoveArray(point_tag_name)
    
    return mesh

# Apply point-to-cell mapping and tag rounding
final_solid = points_to_elems_volume_weighted(
    solid_with_interpolated_tags,
    point_tag_name="InterpolatedTags",
    elem_tag_name="data",
    tag_name="elemTag"
)

# Set the new cell tag array as the active scalar field for ParaView/VTK visualization
final_solid.GetCellData().SetActiveScalars("elemTag")

# Extract and verify the final cell tags
final_tags = vtk_to_numpy(final_solid.GetCellData().GetArray('elemTag'))
print(f"\nFinal volumetric cell tags (first/last 10): {final_tags[:10]} ... {final_tags[-10:]}")

# =============================================================================
# 7. SAVE PROCESSED VOLUMETRIC MESH
# =============================================================================
writer = vtk.vtkUnstructuredGridWriter()
writer.SetFileName('Shell_Test_solid_Labels.vtk')
writer.SetInputData(final_solid)
writer.Write()

print("Successfully saved processed volumetric mesh to 'Shell_Test_solid_Labels.vtk'")
print("Next steps: The mesh is now ready for electrophysiological simulation or further conversion via Meshtool.")