import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog
from FDS_Mesh_Parser import parse_fds_meshes
from FDS_Mesh_Viewer_3D import FDSMeshViewer3D


class FDSMeshViewerTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FDS Mesh Viewer 3D - Test Application")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create 3D viewer
        self.viewer = FDSMeshViewer3D()
        layout.addWidget(self.viewer)
        
        # Create load button
        self.load_button = QPushButton("Load FDS File")
        self.load_button.clicked.connect(self.load_fds_file)
        layout.addWidget(self.load_button)
        
    def load_fds_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open FDS File", "", "FDS Files (*.fds);;All Files (*)"
        )
        
        if file_path:
            try:
                # Parse meshes from FDS file
                meshes = parse_fds_meshes(file_path)
                print(f"Loaded {len(meshes)} meshes from {file_path}")
                
                # Load meshes into 3D viewer
                self.viewer.load_mesh_data(meshes)
                
                print("Meshes loaded into 3D viewer successfully")
            except Exception as e:
                print(f"Error loading FDS file: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FDSMeshViewerTestApp()
    window.show()
    sys.exit(app.exec())