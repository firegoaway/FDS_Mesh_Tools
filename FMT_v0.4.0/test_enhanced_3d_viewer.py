import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from FDS_Mesh_Viewer_3D import FDSMeshViewer3D


class TestEnhanced3DViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Enhanced FDS Mesh Viewer 3D")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create 3D viewer
        self.viewer = FDSMeshViewer3D()
        layout.addWidget(self.viewer)
        
        # Create test buttons
        button_layout = QVBoxLayout()
        
        # Button to load sample data
        load_button = QPushButton("Load Sample Data")
        load_button.clicked.connect(self.load_sample_data)
        button_layout.addWidget(load_button)
        
        # Button to test selection
        select_button = QPushButton("Select Mesh1")
        select_button.clicked.connect(self.test_selection)
        button_layout.addWidget(select_button)
        
        # Button to test transformation mode
        transform_button = QPushButton("Enable Move Transformation")
        transform_button.clicked.connect(self.test_transformation)
        button_layout.addWidget(transform_button)
        
        # Button to test constraint axis
        constraint_button = QPushButton("Set X-Axis Constraint")
        constraint_button.clicked.connect(self.test_constraint)
        button_layout.addWidget(constraint_button)
        
        # Button to test snap-to-grid
        snap_button = QPushButton("Enable Snap-to-Grid")
        snap_button.clicked.connect(self.test_snap_to_grid)
        button_layout.addWidget(snap_button)
        
        # Button to test grid layer functionality
        grid_layer_button = QPushButton("Add Grid Layer")
        grid_layer_button.clicked.connect(self.test_add_grid_layer)
        button_layout.addWidget(grid_layer_button)
        
        # Button to test grid layer visibility
        grid_visibility_button = QPushButton("Toggle Grid Layer Visibility")
        grid_visibility_button.clicked.connect(self.test_toggle_grid_layer_visibility)
        button_layout.addWidget(grid_visibility_button)
        
        # Button to test HUD visibility
        hud_visibility_button = QPushButton("Toggle HUD Visibility")
        hud_visibility_button.clicked.connect(self.test_hud_visibility)
        button_layout.addWidget(hud_visibility_button)
        
        # Button to test HUD position
        hud_position_button = QPushButton("Cycle HUD Position")
        hud_position_button.clicked.connect(self.test_hud_position)
        button_layout.addWidget(hud_position_button)
        
        # Button to test HUD transparency
        hud_transparency_button = QPushButton("Test HUD Transparency")
        hud_transparency_button.clicked.connect(self.test_hud_transparency)
        button_layout.addWidget(hud_transparency_button)
        
        # Button to test HUD size
        hud_size_button = QPushButton("Test HUD Size")
        hud_size_button.clicked.connect(self.test_hud_size)
        button_layout.addWidget(hud_size_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.viewer.mesh_selection_changed.connect(self.on_mesh_selection_changed)
        self.viewer.mesh_transformation_completed.connect(self.on_mesh_transformation_completed)
        
        # HUD position index for cycling
        self.hud_position_index = 0
        self.transparency_level = 0
        self.size_factor = 0
        
    def load_sample_data(self):
        # Sample mesh data for testing
        sample_meshes = [
            {
                'id': 'Mesh1',
                'i': 10, 'j': 10, 'k': 10,
                'xmin': 0, 'xmax': 10,
                'ymin': 0, 'ymax': 10,
                'zmin': 0, 'zmax': 10
            },
            {
                'id': 'Mesh2',
                'i': 5, 'j': 15, 'k': 8,
                'xmin': 15, 'xmax': 20,
                'ymin': 5, 'ymax': 20,
                'zmin': 2, 'zmax': 10
            },
            {
                'id': 'Mesh3',
                'i': 20, 'j': 5, 'k': 12,
                'xmin': 25, 'xmax': 45,
                'ymin': 0, 'ymax': 5,
                'zmin': 0, 'zmax': 12
            }
        ]
        
        # Load sample data
        self.viewer.load_mesh_data(sample_meshes)
        print("Sample data loaded")
        
    def test_selection(self):
        # Test selection
        self.viewer.select_mesh('Mesh1')
        print("Mesh1 selected")
        
    def test_transformation(self):
        # Test transformation mode
        self.viewer.set_transformation_mode('move')
        print("Move transformation mode enabled")
        
    def test_constraint(self):
        # Test constraint axis
        self.viewer.set_constraint_axis('x')
        print("X-axis constraint enabled")
        
    def test_snap_to_grid(self):
        # Test snap-to-grid
        self.viewer.set_snap_to_grid(True, 1.0)
        print("Snap-to-grid enabled with grid size 1.0")
        
    def test_add_grid_layer(self):
        # Test adding a grid layer
        self.viewer.add_grid_layer("test_layer", spacing=2.0, orientation='XZ', visible=True)
        print("Added test grid layer")
        
    def test_toggle_grid_layer_visibility(self):
        # Test toggling grid layer visibility
        layers = self.viewer.get_grid_layers()
        if layers:
            layer_name = list(layers.keys())[0]
            current_visibility = layers[layer_name].visible
            self.viewer.set_grid_layer_visibility(layer_name, not current_visibility)
            print(f"Toggled visibility of grid layer {layer_name}")
        
    def test_hud_visibility(self):
        # Test HUD visibility
        self.viewer.show_hud(not self.viewer.hud_toolbar.isVisible())
        print("HUD visibility toggled")
        
    def test_hud_position(self):
        # Test HUD position cycling
        positions = ['top-left', 'top-right', 'bottom-left']
        self.hud_position_index = (self.hud_position_index + 1) % len(positions)
        position = positions[self.hud_position_index]
        self.viewer.set_hud_corner_position(position)
        print(f"HUD position set to {position}")
        
    def test_hud_transparency(self):
        # Test HUD transparency
        # Cycle through different transparency levels
        self.transparency_level = (self.transparency_level + 1) % 4
        alpha = [0.5, 0.7, 0.9, 1.0][self.transparency_level]
        self.viewer.set_hud_transparency(alpha)
        print(f"HUD transparency set to {alpha}")
        
    def test_hud_size(self):
        # Test HUD size
        # Cycle through different size factors
        self.size_factor = (self.size_factor + 1) % 4
        size = [0.7, 1.0, 1.3, 1.6][self.size_factor]
        self.viewer.set_hud_size(size)
        print(f"HUD size set to {size}")
        
    def on_mesh_selection_changed(self, selected_meshes):
        print(f"Mesh selection changed: {selected_meshes}")
        
    def on_mesh_transformation_completed(self, transformed_data):
        print(f"Mesh transformation completed: {transformed_data}")
        # Get transformed mesh data
        mesh_data = self.viewer.get_transformed_mesh_data()
        print(f"Current mesh data: {mesh_data}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestEnhanced3DViewer()
    window.show()
    sys.exit(app.exec())