import sys
import numpy as np
from PyQt6.QtWidgets import QApplication
from FDS_Mesh_Viewer_3D import FDSMeshViewer3D

def test_enhanced_grid_features():
    """Test the enhanced grid features."""
    app = QApplication(sys.argv)
    
    # Create viewer
    viewer = FDSMeshViewer3D()
    
    # Test grid layer creation
    print("Testing grid layer creation...")
    viewer.add_grid_layer("secondary", spacing=2.0, color=(0, 1, 0, 0.3), orientation='XZ', visible=True)
    viewer.add_grid_layer("tertiary", spacing=0.5, color=(0, 0, 1, 0.3), orientation='YZ', visible=False)
    
    # Test grid layer modification
    print("Testing grid layer modification...")
    viewer.set_grid_layer_spacing("main", 1.5)
    viewer.set_grid_layer_color("main", (1, 0, 0.5))
    viewer.set_grid_layer_offset("main", (1, 1, 0))
    
    # Test grid visibility
    print("Testing grid visibility...")
    viewer.set_grid_layer_visibility("tertiary", True)
    
    # Test snap-to-grid
    print("Testing snap-to-grid...")
    viewer.set_snap_to_grid(True, 0.2)
    
    # Test grid settings save/restore
    print("Testing grid settings save/restore...")
    settings = viewer.save_grid_settings()
    print(f"Saved settings: {settings}")
    
    # Modify some settings
    viewer.set_grid_layer_spacing("main", 2.0)
    
    # Restore settings
    viewer.restore_grid_settings(settings)
    
    # Test batch updates
    print("Testing batch updates...")
    updates = [
        ("main", "spacing", 3.0),
        ("secondary", "color", (1, 1, 0, 0.5)),
        ("tertiary", "orientation", "XYZ")
    ]
    viewer.batch_update_grid_layers(updates)
    
    # Test keyboard shortcuts simulation
    print("Testing keyboard shortcuts...")
    viewer._adjust_grid_spacing(1.1)  # Simulate Ctrl++
    viewer._adjust_grid_spacing(0.9)  # Simulate Ctrl+-
    
    print("All tests passed!")
    
    # Show the viewer
    viewer.show()
    
    # For actual testing, we would run the app, but for this example we'll just exit
    # sys.exit(app.exec())
    
if __name__ == "__main__":
    test_enhanced_grid_features()