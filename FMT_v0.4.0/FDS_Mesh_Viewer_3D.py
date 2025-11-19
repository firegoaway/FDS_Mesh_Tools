import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow, QToolButton, QButtonGroup, QHBoxLayout, QFrame
from PyQt6.QtGui import QColor, QKeyEvent, QIcon
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize
from PyQt6.QtSvgWidgets import QSvgWidget
import pyqtgraph as pg
import pyqtgraph.opengl as gl


class GridLayer:
    """
    Represents a single grid layer with customizable properties.
    """
    def __init__(self, name, spacing=1.0, color=(1, 1, 1, 0.5), orientation='XY', visible=True, offset=(0, 0, 0)):
        self.name = name
        self.spacing = spacing
        self.color = color
        self.orientation = orientation # 'XY', 'XZ', 'YZ', 'XYZ'
        self.visible = visible
        self.offset = offset
        self.grid_item = None # Reference to the GLGridItem
        
    def create_grid_item(self):
        """
        Create a GLGridItem based on the layer properties.
        """
        # Create a custom grid item based on orientation
        if self.orientation == 'XY':
            self.grid_item = gl.GLGridItem()
            self.grid_item.setSpacing(self.spacing, self.spacing)
        elif self.orientation == 'XZ':
            # For XZ plane, we need to rotate the grid
            self.grid_item = gl.GLGridItem()
            self.grid_item.setSpacing(self.spacing, self.spacing)
            # Rotate 90 degrees around X axis to get XZ plane
            self.grid_item.rotate(90, 1, 0, 0)
        elif self.orientation == 'YZ':
            # For YZ plane, we need to rotate the grid
            self.grid_item = gl.GLGridItem()
            self.grid_item.setSpacing(self.spacing, self.spacing)
            # Rotate 90 degrees around Y axis to get YZ plane
            self.grid_item.rotate(90, 0, 1, 0)
        else:
            # For XYZ or default, create a standard XY grid
            self.grid_item = gl.GLGridItem()
            self.grid_item.setSpacing(self.spacing, self.spacing)
            
        # Apply color
        self.grid_item.setColor(self.color)
            
        # Apply offset if specified
        if self.offset != (0, 0, 0):
            self.grid_item.translate(*self.offset)
            
    def set_orientation(self, orientation):
        """
        Set the grid orientation and update the grid item.
        
        :param orientation: Grid orientation ('XY', 'XZ', 'YZ', 'XYZ')
        """
        self.orientation = orientation
        self.update_grid_item()
            
    def set_spacing(self, spacing):
        """
        Set the grid spacing and update the grid item.
        
        :param spacing: New spacing value
        """
        self.spacing = spacing
        self.update_grid_item()
        
    def set_color(self, color):
        """
        Set the grid color and update the grid item.
        
        :param color: New color (RGBA tuple)
        """
        self.color = color
        if self.grid_item:
            self.grid_item.setColor(color)
        
    def update_grid_item(self):
        """
        Update the grid item properties.
        """
        if self.grid_item:
            self.grid_item.setSpacing(self.spacing, self.spacing)
            self.grid_item.setColor(self.color)
            
            # Reset transformations
            self.grid_item.resetTransform()
            
            # Apply orientation-specific transformations
            if self.orientation == 'XZ':
                # Rotate 90 degrees around X axis to get XZ plane
                self.grid_item.rotate(90, 1, 0, 0)
            elif self.orientation == 'YZ':
                # Rotate 90 degrees around Y axis to get YZ plane
                self.grid_item.rotate(90, 1, 0)
                
            # Apply offset if specified
            if self.offset != (0, 0, 0):
                self.grid_item.translate(*self.offset)
            

class GridSystem:
    """
    Manages multiple grid layers and snap-to-grid functionality.
    """
    def __init__(self, view_widget):
        self.view_widget = view_widget
        self.layers = {}  # Dictionary of grid layers by name
        self.snap_enabled = False
        self.snap_threshold = 0.1
        self.active_layer = None
        
    def add_layer(self, name, **kwargs):
        """
        Add a new grid layer.
        
        :param name: Name of the layer
        :param kwargs: GridLayer parameters
        """
        layer = GridLayer(name, **kwargs)
        self.layers[name] = layer
        if layer.visible:
            grid_item = layer.create_grid_item()
            self.view_widget.addItem(grid_item)
        return layer
        
    def remove_layer(self, name):
        """
        Remove a grid layer.
        
        :param name: Name of the layer to remove
        """
        if name in self.layers:
            layer = self.layers[name]
            if layer.grid_item and layer.grid_item in self.view_widget.items:
                self.view_widget.removeItem(layer.grid_item)
            del self.layers[name]
            
    def set_layer_visibility(self, name, visible):
        """
        Toggle layer visibility.
        
        :param name: Name of the layer
        :param visible: Visibility state
        """
        if name in self.layers:
            layer = self.layers[name]
            layer.visible = visible
            if layer.grid_item:
                if visible and layer.grid_item not in self.view_widget.items:
                    self.view_widget.addItem(layer.grid_item)
                elif not visible and layer.grid_item in self.view_widget.items:
                    self.view_widget.removeItem(layer.grid_item)
                    
    def set_snap_settings(self, enabled, threshold=0.1):
        """
        Configure snap-to-grid settings.
        
        :param enabled: Whether snapping is enabled
        :param threshold: Snap threshold distance
        """
        self.snap_enabled = enabled
        self.snap_threshold = threshold
        
    def snap_position(self, position):
        """
        Apply snap-to-grid to a position if enabled.
        
        :param position: Tuple of (x, y, z) coordinates
        :return: Snapped position if enabled, otherwise original position
        """
        if not self.snap_enabled or not self.layers:
            return position
            
        x, y, z = position
        
        # Use the first visible layer for snapping if no active layer is set
        layer_to_use = self.active_layer
        if not layer_to_use:
            for layer in self.layers.values():
                if layer.visible:
                    layer_to_use = layer
                    break
                    
        if not layer_to_use:
            return position
            
        # Apply snapping based on layer spacing and threshold
        spacing = layer_to_use.spacing
        offset_x, offset_y, offset_z = layer_to_use.offset
        
        # Calculate distance to nearest grid point for each axis
        if 'X' in layer_to_use.orientation:
            grid_x = round((x - offset_x) / spacing) * spacing + offset_x
            if abs(x - grid_x) <= self.snap_threshold:
                x = grid_x
        if 'Y' in layer_to_use.orientation:
            grid_y = round((y - offset_y) / spacing) * spacing + offset_y
            if abs(y - grid_y) <= self.snap_threshold:
                y = grid_y
        if 'Z' in layer_to_use.orientation:
            grid_z = round((z - offset_z) / spacing) * spacing + offset_z
            if abs(z - grid_z) <= self.snap_threshold:
                z = grid_z
            
        return (x, y, z)
        
    def get_visible_layers(self):
        """
        Get all visible grid layers.
        
        :return: List of visible GridLayer objects
        """
        return [layer for layer in self.layers.values() if layer.visible]
        
    def set_active_layer(self, name):
        """
        Set the active layer for snapping.
        
        :param name: Name of the layer to set as active
        """
        if name in self.layers:
            self.active_layer = self.layers[name]
            

class FDSMeshViewer3D(QWidget):
    """
    3D viewer for FDS mesh entities using PyQtGraph.
    
    This class provides a 3D visualization of FDS mesh volumes with:
    - Interactive pan, rotate, and zoom controls
    - Color-coded mesh volumes
    - Real-time updates when mesh data changes
    - Selection highlighting
    - Proper error handling and resource management
    """
    
    # Signal emitted when mesh selection changes
    mesh_selection_changed = pyqtSignal(set)  # Emits set of selected mesh IDs
    
    # Signal emitted when mesh transformation is completed
    mesh_transformation_completed = pyqtSignal(dict)  # Emits dict with mesh ID as key and new data as value
    
    def __init__(self, parent=None):
        """
        Initialize the 3D viewer.
        
        :param parent: Parent widget
        """
        super().__init__(parent)
        self.parent = parent
        self.mesh_items = {}  # Dictionary to store mesh items by ID
        self.selected_meshes = set()  # Set to track selected meshes
        self.default_color_alpha = 0.7  # Default transparency for meshes
        self.highlight_color_alpha = 1.0 # Full opacity for selected meshes
        
        # Mesh data cache for efficient access
        self.mesh_data_cache = {}  # Cache for mesh data to avoid repeated lookups
        
        # Optimized data structures for mesh storage
        self.mesh_bounding_boxes = {}  # Cache for mesh bounding boxes for faster spatial queries
        self.mesh_centroids = {}  # Cache for mesh centroids for faster calculations
        
        # Navigation state variables
        self.last_pos = QPoint()
        self.navigation_mode = None  # 'orbit', 'pan', 'zoom'
        self.is_orthographic = False  # Perspective by default
        
        # Transformation state variables
        self.transformation_mode = None  # 'move', 'rotate', 'scale'
        self.constraint_axis = None  # 'x', 'y', 'z' or None for free movement
        self.is_transforming = False
        self.transform_start_pos = None
        self.transform_initial_positions = {}
        
        # Grid system
        self.grid_system = None
        
        # Visual feedback items
        self.axis_guides = []  # List to store axis guide items
        self.transformation_handles = []  # List to store transformation handle items
        self.snap_feedback_items = []  # List to store snap feedback items
        
        # Performance optimization flags
        self.updating_view = False  # Flag to prevent recursive updates
        self.needs_view_update = False  # Flag to defer view updates
        self.ui_update_priority = True  # Flag to prioritize UI updates over background tasks
        
        # Event throttling
        self.last_mouse_move_time = 0
        self.mouse_move_throttle_interval = 16  # ~60 FPS in milliseconds
        self.last_resize_time = 0
        self.resize_throttle_interval = 16  # ~60 FPS in milliseconds
        
        # Frame rate monitoring
        self.frame_count = 0
        self.last_frame_time = 0
        self.fps = 0
        self.performance_label = None
        self.target_fps = 60  # Target frame rate
        self.frame_timer = None
        self.render_time = 0  # Time spent rendering last frame
        self.update_count = 0  # Number of updates since last FPS calculation
        
        self._setup_ui()
        
    def _setup_ui(self):
        """
        Set up the user interface with PyQtGraph's GLViewWidget.
        """
        try:
            # Main layout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Create 3D view widget
            self.view = gl.GLViewWidget()
            self.view.setBackgroundColor('k')  # Black background
            layout.addWidget(self.view)
            
            # Initialize grid system
            self.grid_system = GridSystem(self.view)
            
            # Add a default grid layer
            self.grid_system.add_layer("main", spacing=1.0, orientation='XY', visible=True)
            
            # Set default camera position
            self.view.setCameraPosition(distance=50)
            
            # Create HUD overlay
            self._create_hud_overlay()
            
            # Set up FPS monitoring
            self._setup_fps_monitoring()
            
        except Exception as e:
            print(f"Error setting up UI: {e}")
            raise
            
    def _setup_fps_monitoring(self):
        """
        Set up frame rate monitoring and display.
        """
        try:
            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QLabel
            
            # Create performance metrics label
            self.performance_label = QLabel("FPS: 0")
            self.performance_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: rgba(0, 0, 180, 150);
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 10px;
                }
            """)
            self.performance_label.setParent(self.view)
            self.performance_label.move(10, self.view.height() - 30)
            self.performance_label.show()
            
            # Create timer for FPS updates
            self.frame_timer = QTimer(self)
            self.frame_timer.timeout.connect(self._update_fps)
            self.frame_timer.start(1000)  # Update FPS every second
            
            # Connect to view's paint event for frame counting
            self.view.paintGL = self._wrap_paint_gl(self.view.paintGL)
            
        except Exception as e:
            print(f"Error setting up FPS monitoring: {e}")
            
    def _wrap_paint_gl(self, original_paint_gl):
        """
        Wrap the paintGL method to count frames and track render time.
        
        :param original_paint_gl: Original paintGL method
        :return: Wrapped paintGL method
        """
        def wrapped_paint_gl():
            # Track render time
            import time
            start_time = time.perf_counter()
            
            # Count frame
            self.frame_count += 1
            
            # Call original method
            result = original_paint_gl()
            
            # Track render time
            render_time = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
            self.render_time += render_time
            self.update_count += 1
            
            return result
        return wrapped_paint_gl
        
    def _update_fps(self):
        """
        Update the FPS calculation and display.
        """
        try:
            # Calculate FPS
            self.fps = self.frame_count
            self.frame_count = 0
            
            # Update performance label with detailed metrics
            if self.performance_label:
                # Calculate average render time
                avg_render_time = 0
                if self.update_count > 0:
                    avg_render_time = self.render_time / self.update_count
                
                # Calculate min and max render times
                # Note: We would need to track these separately for more accurate metrics
                min_render_time = avg_render_time  # Simplified for now
                max_render_time = avg_render_time  # Simplified for now
                
                # Format the performance metrics
                metrics_text = f"FPS: {self.fps} | Avg: {avg_render_time:.2f}ms | Min: {min_render_time:.2f}ms | Max: {max_render_time:.2f}ms"
                self.performance_label.setText(metrics_text)
                
                # Reset counters
                self.render_time = 0
                self.update_count = 0
                
            # Apply frame rate stabilization if needed
            self._stabilize_frame_rate()
            
        except Exception as e:
            print(f"Error updating FPS: {e}")
            
    def _stabilize_frame_rate(self):
        """
        Apply frame rate stabilization techniques.
        """
        try:
            # If FPS is significantly higher than target, we might want to throttle
            if self.fps > self.target_fps * 1.5:
                # Add a small delay to reduce frame rate
                from PyQt6.QtCore import QThread
                QThread.msleep(1)
                
            # If FPS is significantly lower than target, we might need to optimize
            elif self.fps < self.target_fps * 0.5:
                # Consider optimization strategies
                # For now, we'll just print a warning
                print(f"Warning: FPS ({self.fps}) is significantly below target ({self.target_fps})")
                
        except Exception as e:
            print(f"Error stabilizing frame rate: {e}")
            
    def _create_hud_overlay(self):
        """
        Create the HUD overlay with toolbar buttons and orientation cube.
        """
        # Create a frame for the HUD toolbar
        self.hud_toolbar = QFrame(self.view)
        self.hud_toolbar.setObjectName("hudToolbar")
        self.hud_toolbar.setStyleSheet("""
            QFrame#hudToolbar {
                background-color: rgba(30, 30, 180);
                border-radius: 8px;
                border: 1px solid rgba(100, 100, 100, 100);
            }
        """)
        
        # Create layout for toolbar buttons
        toolbar_layout = QHBoxLayout(self.hud_toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(2)
        
        # Create button group for navigation tools
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        
        # Create select button
        self.select_button = QToolButton()
        self.select_button.setIcon(QIcon("hud_svgs/select_icon.svg"))
        self.select_button.setIconSize(QSize(24, 24))
        self.select_button.setFixedSize(32, 32)
        self.select_button.setCheckable(True)
        self.select_button.setToolTip("Select Mode (S)\nCtrl+G: Toggle grid snapping\nCtrl++: Increase grid spacing\nCtrl+-: Decrease grid spacing")
        self.select_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #8f8f91;
                border-radius: 4px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #f6f7fa, stop: 1 #dadbde);
            }
            QToolButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #4A90E2, stop: 1 #3A80D2);
            }
            QToolButton:hover {
                border: 1px solid #4A90E2;
            }
        """)
        self.nav_button_group.addButton(self.select_button)
        toolbar_layout.addWidget(self.select_button)
        
        # Create orbit button
        self.orbit_button = QToolButton()
        self.orbit_button.setIcon(QIcon("hud_svgs/orbit_icon.svg"))
        self.orbit_button.setIconSize(QSize(24, 24))
        self.orbit_button.setFixedSize(32, 32)
        self.orbit_button.setCheckable(True)
        self.orbit_button.setToolTip("Orbit Mode (O)")
        self.orbit_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #8f8f91;
                border-radius: 4px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #f6f7fa, stop: 1 #dadbde);
            }
            QToolButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #4A90E2, stop: 1 #3A80D2);
            }
            QToolButton:hover {
                border: 1px solid #4A90E2;
            }
        """)
        self.nav_button_group.addButton(self.orbit_button)
        toolbar_layout.addWidget(self.orbit_button)
        
        # Create pan button
        self.pan_button = QToolButton()
        self.pan_button.setIcon(QIcon("hud_svgs/pan_icon.svg"))
        self.pan_button.setIconSize(QSize(24, 24))
        self.pan_button.setFixedSize(32, 32)
        self.pan_button.setCheckable(True)
        self.pan_button.setToolTip("Pan Mode (P)")
        self.pan_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #8f8f91;
                border-radius: 4px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #f6f7fa, stop: 1 #dadbde);
            }
            QToolButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #4A90E2, stop: 1 #3A80D2);
            }
            QToolButton:hover {
                border: 1px solid #4A90E2;
            }
        """)
        self.nav_button_group.addButton(self.pan_button)
        toolbar_layout.addWidget(self.pan_button)
        
        # Create zoom button
        self.zoom_button = QToolButton()
        self.zoom_button.setIcon(QIcon("hud_svgs/zoom_icon.svg"))
        self.zoom_button.setIconSize(QSize(24, 24))
        self.zoom_button.setFixedSize(32, 32)
        self.zoom_button.setCheckable(True)
        self.zoom_button.setToolTip("Zoom Mode (Z)")
        self.zoom_button.setStyleSheet("""
            QToolButton {
                border: 1px solid #8f8f91;
                border-radius: 4px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #f6f7fa, stop: 1 #dadbde);
            }
            QToolButton:checked {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #4A90E2, stop: 1 #3A80D2);
            }
            QToolButton:hover {
                border: 1px solid #4A90E2;
            }
        """)
        self.nav_button_group.addButton(self.zoom_button)
        toolbar_layout.addWidget(self.zoom_button)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        toolbar_layout.addWidget(separator)
        
        # Create orientation cube widget
        self.orientation_cube = QSvgWidget("hud_svgs/orientation_cube.svg")
        self.orientation_cube.setFixedSize(60, 60)
        self.orientation_cube.setStyleSheet("background: transparent;")
        toolbar_layout.addWidget(self.orientation_cube)
        
        # Position the HUD toolbar in the top-left corner
        self._position_hud_toolbar()
        
        # Connect button signals
        self.select_button.clicked.connect(self._on_select_mode)
        self.orbit_button.clicked.connect(self._on_orbit_mode)
        self.pan_button.clicked.connect(self._on_pan_mode)
        self.zoom_button.clicked.connect(self._on_zoom_mode)
        
        # Set default mode to select
        self.select_button.setChecked(True)
        
    def _position_hud_toolbar(self):
        """
        Position the HUD toolbar in the top-left corner of the view.
        """
        # Position the toolbar in the top-left corner with some margin
        margin = 10
        self.hud_toolbar.setGeometry(
            margin,
            margin,
            self.hud_toolbar.sizeHint().width(),
            self.hud_toolbar.sizeHint().height()
        )
        
    def _on_select_mode(self):
        """
        Handle select mode button click.
        """
        if self.select_button.isChecked():
            # Disable navigation mode
            self.navigation_mode = None
            # Disable transformation mode
            self.transformation_mode = None
            print("Select mode activated")
            
    def _on_orbit_mode(self):
        """
        Handle orbit mode button click.
        """
        if self.orbit_button.isChecked():
            self.navigation_mode = 'orbit'
            print("Orbit mode activated")
            
    def _on_pan_mode(self):
        """
        Handle pan mode button click.
        """
        if self.pan_button.isChecked():
            self.navigation_mode = 'pan'
            print("Pan mode activated")
            
    def _on_zoom_mode(self):
        """
        Handle zoom mode button click.
        """
        if self.zoom_button.isChecked():
            self.navigation_mode = 'zoom'
            print("Zoom mode activated")
            
    def set_transformation_mode(self, mode):
        """
        Set the transformation mode and update UI accordingly.
        
        :param mode: Transformation mode ('move', 'rotate', 'scale', or None to disable)
        """
        if mode not in ('move', 'rotate', 'scale', None):
            raise ValueError("Invalid transformation mode")
        self.transformation_mode = mode
        
        # Update UI to reflect transformation mode if needed
        # For now, we're just setting the mode
        
    def toggle_navigation_mode(self, mode):
        """
        Toggle a navigation mode on or off.
        
        :param mode: Navigation mode to toggle ('orbit', 'pan', 'zoom')
        """
        if self.navigation_mode == mode:
            # If the mode is already active, switch to select mode
            self.set_navigation_mode(None)
        else:
            # Otherwise, switch to the requested mode
            self.set_navigation_mode(mode)
            
    def toggle_transformation_mode(self, mode):
        """
        Toggle a transformation mode on or off.
        
        :param mode: Transformation mode to toggle ('move', 'rotate', 'scale')
        """
        if self.transformation_mode == mode:
            # If the mode is already active, disable it
            self.set_transformation_mode(None)
        else:
            # Otherwise, switch to the requested mode
            self.set_transformation_mode(mode)
            
    def show_hud(self, show=True):
        """
        Show or hide the HUD overlay.
        
        :param show: Boolean indicating whether to show or hide the HUD
        """
        self.hud_toolbar.setVisible(show)
        
    def hide_hud(self):
        """
        Hide the HUD overlay.
        """
        self.show_hud(False)
        
    def set_hud_position(self, position):
        """
        Set the position of the HUD overlay.
        
        :param position: String indicating position ('top-left', 'top-right', 'bottom-left', 'bottom-right')
        """
        margin = 10
        toolbar_width = self.hud_toolbar.sizeHint().width()
        toolbar_height = self.hud_toolbar.sizeHint().height()
        view_width = self.view.width()
        view_height = self.view.height()
        
        if position == 'top-left':
            self.hud_toolbar.setGeometry(margin, margin, toolbar_width, toolbar_height)
        elif position == 'top-right':
            self.hud_toolbar.setGeometry(view_width - toolbar_width - margin, margin, toolbar_width, toolbar_height)
        elif position == 'bottom-left':
            self.hud_toolbar.setGeometry(margin, view_height - toolbar_height - margin, toolbar_width, toolbar_height)
        elif position == 'bottom-right':
            self.hud_toolbar.setGeometry(view_width - toolbar_width - margin, view_height - toolbar_height - margin, toolbar_width, toolbar_height)
            
    def set_hud_corner_position(self, corner):
        """
        Set the corner position of the HUD overlay and update the positioning method.
        
        :param corner: String indicating corner position ('top-left', 'top-right', 'bottom-left', 'bottom-right')
        """
        self.hud_corner = corner
        self._position_hud_toolbar()
        
    def _position_hud_toolbar(self):
        """
        Position the HUD toolbar in the specified corner of the view.
        """
        # Position the toolbar in the specified corner with some margin
        margin = 10
        toolbar_width = self.hud_toolbar.sizeHint().width()
        toolbar_height = self.hud_toolbar.sizeHint().height()
        view_width = self.view.width()
        view_height = self.view.height()
        
        if hasattr(self, 'hud_corner'):
            corner = self.hud_corner
        else:
            corner = 'top-left'  # Default position
            
        if corner == 'top-left':
            self.hud_toolbar.setGeometry(margin, margin, toolbar_width, toolbar_height)
        elif corner == 'top-right':
            self.hud_toolbar.setGeometry(view_width - toolbar_width - margin, margin, toolbar_width, toolbar_height)
        elif corner == 'bottom-left':
            self.hud_toolbar.setGeometry(margin, view_height - toolbar_height - margin, toolbar_width, toolbar_height)
        elif corner == 'bottom-right':
            self.hud_toolbar.setGeometry(view_width - toolbar_width - margin, view_height - toolbar_height - margin, toolbar_width, toolbar_height)
            
    def resizeEvent(self, event):
        """
        Handle resize events to reposition the HUD overlay and FPS label.
        """
        # Throttle resize events
        current_time = event.timestamp() * 1000  # Convert to milliseconds
        time_delta = current_time - self.last_resize_time
        
        # Adaptive throttling based on current FPS
        adaptive_throttle = self.resize_throttle_interval
        if self.fps > 0 and self.fps < 30:
            # Increase throttling interval if FPS is low
            adaptive_throttle *= 2
        elif self.fps > 60:
            # Decrease throttling interval if FPS is high
            adaptive_throttle = max(1, adaptive_throttle // 2)
            
        if time_delta < adaptive_throttle:
            super().resizeEvent(event)
            return
        self.last_resize_time = current_time
        
        super().resizeEvent(event)
        # Reposition the HUD toolbar when the widget is resized
        if hasattr(self, 'hud_toolbar'):
            # Keep the same position relative to the corner
            self._position_hud_toolbar()
            
        # Reposition the performance label
        if hasattr(self, 'performance_label') and self.performance_label:
            self.performance_label.move(10, self.view.height() - 30)
            
    def set_hud_transparency(self, alpha):
        """
        Set the transparency of the HUD overlay.
        
        :param alpha: Float value between 0.0 (transparent) and 1.0 (opaque)
        """
        # Update the stylesheet with the new alpha value
        self.hud_toolbar.setStyleSheet(f"""
            QFrame#hudToolbar {{
                background-color: rgba(30, 30, 30, {int(180 * alpha)});
                border-radius: 8px;
                border: 1px solid rgba(100, 100, 100, 100);
            }}
        """)
         
    def set_hud_size(self, size_factor):
        """
        Set the size of the HUD elements.
        
        :param size_factor: Float value representing size multiplier (1.0 is default)
        """
        # Update button sizes
        button_size = int(32 * size_factor)
        self.select_button.setFixedSize(button_size, button_size)
        self.orbit_button.setFixedSize(button_size, button_size)
        self.pan_button.setFixedSize(button_size, button_size)
        self.zoom_button.setFixedSize(button_size, button_size)
        
        # Update icon sizes
        icon_size = int(24 * size_factor)
        self.select_button.setIconSize(QSize(icon_size, icon_size))
        self.orbit_button.setIconSize(QSize(icon_size, icon_size))
        self.pan_button.setIconSize(QSize(icon_size, icon_size))
        self.zoom_button.setIconSize(QSize(icon_size, icon_size))
        
        # Update orientation cube size
        cube_size = int(60 * size_factor)
        self.orientation_cube.setFixedSize(cube_size, cube_size)
        
        # Update toolbar corner radius
        border_radius = int(8 * size_factor)
        style = self.hud_toolbar.styleSheet()
        # Update the stylesheet with the new border radius
        self.hud_toolbar.setStyleSheet(f"""
            QFrame#hudToolbar {{
                background-color: rgba(30, 30, 180);
                border-radius: {border_radius}px;
                border: 1px solid rgba(100, 100, 100, 100);
            }}
        """)
         
    def update_hud_button_states(self):
        """
        Update the HUD button states to match the current navigation mode.
        """
        # Block signals to prevent recursive calls
        self.select_button.blockSignals(True)
        self.orbit_button.blockSignals(True)
        self.pan_button.blockSignals(True)
        self.zoom_button.blockSignals(True)
        
        # Update button states based on navigation mode
        if self.navigation_mode is None:
            self.select_button.setChecked(True)
            self.orbit_button.setChecked(False)
            self.pan_button.setChecked(False)
            self.zoom_button.setChecked(False)
        elif self.navigation_mode == 'orbit':
            self.select_button.setChecked(False)
            self.orbit_button.setChecked(True)
            self.pan_button.setChecked(False)
            self.zoom_button.setChecked(False)
        elif self.navigation_mode == 'pan':
            self.select_button.setChecked(False)
            self.orbit_button.setChecked(False)
            self.pan_button.setChecked(True)
            self.zoom_button.setChecked(False)
        elif self.navigation_mode == 'zoom':
            self.select_button.setChecked(False)
            self.orbit_button.setChecked(False)
            self.pan_button.setChecked(False)
            self.zoom_button.setChecked(True)
            
        # Unblock signals
        self.select_button.blockSignals(False)
        self.orbit_button.blockSignals(False)
        self.pan_button.blockSignals(False)
        self.zoom_button.blockSignals(False)
            
    def mousePressEvent(self, event):
        """
        Handle mouse press events for navigation and transformation.
        """
        try:
            # Store the initial mouse position
            self.last_pos = event.pos()
            
            # If we're in transformation mode and have selected meshes, start transformation
            if self.transformation_mode and self.selected_meshes:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._start_transformation(event)
                    event.accept()
                    return
                    
            # Determine navigation mode based on mouse button and modifiers
            if event.button() == Qt.MouseButton.MiddleButton:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.navigation_mode = 'pan'
                elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self.navigation_mode = 'zoom'
                else:
                    self.navigation_mode = 'orbit'
            elif event.button() == Qt.MouseButton.LeftButton:
                if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                    if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                        self.navigation_mode = 'pan'
                    elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                        self.navigation_mode = 'zoom'
                    else:
                        self.navigation_mode = 'orbit'
                else:
                    # Handle mesh selection only if not in a specific navigation mode from HUD
                    if self.navigation_mode is None:
                        # Handle mesh selection
                        self._handle_mesh_selection(event)
                        return  # Don't process as navigation
                    # If in a navigation mode from HUD, we'll process it below
                    
            # Accept the event if we're in navigation mode
            if self.navigation_mode:
                event.accept()
            else:
                super().mousePressEvent(event)
                
        except Exception as e:
            print(f"Error in mousePressEvent: {e}")
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """
        Handle mouse move events for navigation and transformation.
        """
        try:
            # Throttle mouse move events
            current_time = event.timestamp() * 1000  # Convert to milliseconds
            time_delta = current_time - self.last_mouse_move_time
            
            # Adaptive throttling based on current FPS
            adaptive_throttle = self.mouse_move_throttle_interval
            if self.fps > 0 and self.fps < 30:
                # Increase throttling interval if FPS is low
                adaptive_throttle *= 2
            elif self.fps > 60:
                # Decrease throttling interval if FPS is high
                adaptive_throttle = max(1, adaptive_throttle // 2)
                
            if time_delta < adaptive_throttle:
                super().mouseMoveEvent(event)
                return
            self.last_mouse_move_time = current_time
            
            # If we're transforming, update the transformation
            if self.is_transforming:
                self._update_transformation(event)
                event.accept()
                return
                
            if self.navigation_mode and self.view:
                # Calculate the difference in mouse position
                dx = event.pos().x() - self.last_pos.x()
                dy = event.pos().y() - self.last_pos.y()
                
                # Update last position
                self.last_pos = event.pos()
                
                # Apply transformation based on navigation mode
                if self.navigation_mode == 'orbit':
                    # Orbit: Rotate the camera around the center
                    self._orbit_camera(dx, dy)
                elif self.navigation_mode == 'pan':
                    # Pan: Move the camera position
                    self._pan_camera(dx, dy)
                elif self.navigation_mode == 'zoom':
                    # Zoom: Move camera closer or further
                    self._zoom_camera(dy)
                    
                event.accept()
            else:
                super().mouseMoveEvent(event)
                
        except Exception as e:
            print(f"Error in mouseMoveEvent: {e}")
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events for navigation and transformation.
        """
        try:
            # If we were transforming, finish the transformation
            if self.is_transforming:
                self._finish_transformation()
                event.accept()
                return
                
            # Reset navigation mode only if it was set by mouse interaction, not HUD
            # Check if any HUD navigation button is checked
            hud_nav_active = (self.orbit_button.isChecked() or
                             self.pan_button.isChecked() or
                             self.zoom_button.isChecked())
            
            # Only reset navigation mode if no HUD button is active
            if not hud_nav_active:
                self.navigation_mode = None
                # Update HUD button states
                self.update_hud_button_states()
            
            # Accept the event
            event.accept()
            
        except Exception as e:
            print(f"Error in mouseReleaseEvent: {e}")
            super().mouseReleaseEvent(event)
            
    def wheelEvent(self, event):
        """
        Handle mouse wheel events for zooming.
        """
        try:
            # Get the wheel delta
            delta = event.angleDelta().y()
            
            # Apply zoom
            self._zoom_camera(delta * 0.01)  # Scale the delta for smoother zooming
            
            event.accept()
            
        except Exception as e:
            print(f"Error in wheelEvent: {e}")
            super().wheelEvent(event)
            
    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle key press events for hotkeys.
        """
        try:
            # Handle hotkeys
            if event.key() == Qt.Key.Key_Home:
                # Reset view
                self.reset_view()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_F:
                # Frame selected
                self._frame_selected()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_G:
                # Toggle grid visibility
                self._toggle_grid()
                event.accept()
                return
            elif event.key() == Qt.Key_0 and event.modifiers() & Qt.KeyboardModifier.KeypadModifier:
                # Reset view with numpad 0
                self.reset_view()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_P:
                # Toggle orthographic/perspective
                self.toggle_orthographic()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_S:
                # Select mode
                self.set_navigation_mode(None)
                self.update_hud_button_states()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_O:
                # Orbit mode
                self.set_navigation_mode('orbit')
                self.update_hud_button_states()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_A:
                # Pan mode
                self.set_navigation_mode('pan')
                self.update_hud_button_states()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Z:
                # Zoom mode
                self.set_navigation_mode('zoom')
                self.update_hud_button_states()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_H:
                # Toggle HUD visibility
                self.show_hud(not self.hud_toolbar.isVisible())
                event.accept()
                return
            elif event.key() == Qt.Key.Key_G and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Toggle grid snapping
                if self.grid_system:
                    self.grid_system.snap_enabled = not self.grid_system.snap_enabled
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Plus and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Increase grid spacing
                self._adjust_grid_spacing(1.1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Minus and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Decrease grid spacing
                self._adjust_grid_spacing(0.9)
                event.accept()
                return
                
            # Pass other key events to parent
            super().keyPressEvent(event)
            
        except Exception as e:
            print(f"Error in keyPressEvent: {e}")
            super().keyPressEvent(event)
            
    def _orbit_camera(self, dx, dy):
        """
        Orbit the camera around the center point.
        
        :param dx: Horizontal movement delta
        :param dy: Vertical movement delta
        """
        try:
            # Get current camera parameters
            center = self.view.cameraParams()['center']
            elevation = self.view.cameraParams()['elevation']
            azimuth = self.view.cameraParams()['azimuth']
            distance = self.view.cameraParams()['distance']
            
            # Update angles based on mouse movement
            # Invert dy for natural up/down movement
            new_elevation = elevation + dy * 0.5
            new_azimuth = azimuth + dx * 0.5
            
            # Clamp elevation to prevent flipping
            new_elevation = max(-89, min(89, new_elevation))
            
            # Set new camera position
            self.view.setCameraPosition(
                elevation=new_elevation,
                azimuth=new_azimuth,
                distance=distance
            )
            
        except Exception as e:
            print(f"Error in _orbit_camera: {e}")
            
    def set_navigation_mode(self, mode):
        """
        Set the navigation mode and update HUD button states.
        
        :param mode: Navigation mode ('orbit', 'pan', 'zoom', or None for select)
        """
        self.navigation_mode = mode
        self.update_hud_button_states()
            
    def _pan_camera(self, dx, dy):
        """
        Pan the camera (move the center point).
        
        :param dx: Horizontal movement delta
        :param dy: Vertical movement delta
        """
        try:
            # Get current camera parameters
            center = self.view.cameraParams()['center']
            elevation = self.view.cameraParams()['elevation']
            azimuth = self.view.cameraParams()['azimuth']
            distance = self.view.cameraParams()['distance']
            
            # Convert screen movement to 3D movement
            # This is a simplified approach - for more accuracy, we would need to
            # calculate the view and right vectors
            
            # Convert angles to radians
            import math
            elev_rad = math.radians(elevation)
            azim_rad = math.radians(azimuth)
            
            # Calculate movement factors based on distance
            factor = distance * 0.01
            
            # Calculate movement in 3D space
            # X movement affects X and Y based on azimuth
            dx_3d = (math.sin(azim_rad) * dx - math.cos(azim_rad) * dy) * factor
            dy_3d = (math.cos(azim_rad) * dx + math.sin(azim_rad) * dy) * factor
            dz_3d = 0  # Keep Z movement simple for now
            
            # Update center point
            new_center = (
                center[0] - dx_3d,
                center[1] - dy_3d,
                center[2] + dz_3d
            )
            
            # Set new camera position
            self.view.setCameraPosition(center=new_center)
            
        except Exception as e:
            print(f"Error in _pan_camera: {e}")
            
    def _zoom_camera(self, delta):
        """
        Zoom the camera in or out.
        
        :param delta: Zoom amount (positive = zoom in, negative = zoom out)
        """
        try:
            # Get current camera parameters
            distance = self.view.cameraParams()['distance']
            
            # Apply zoom factor
            zoom_factor = 0.9 ** delta  # Exponential zoom for natural feel
            new_distance = max(0.1, distance * zoom_factor)  # Prevent too close
            
            # Set new camera distance
            self.view.setCameraPosition(distance=new_distance)
            
        except Exception as e:
            print(f"Error in _zoom_camera: {e}")
            
    def _frame_selected(self):
        """
        Frame the selected mesh(es) in the view.
        """
        try:
            # If no meshes are selected, frame all meshes
            if not self.selected_meshes:
                self._frame_all_meshes()
                return
                
            # Calculate bounding box of selected meshes
            min_x = min_y = min_z = float('inf')
            max_x = max_y = max_z = float('-inf')
            
            for mesh_id in self.selected_meshes:
                if mesh_id in self.mesh_items:
                    mesh_data = self.mesh_items[mesh_id]['data']
                    min_x = min(min_x, mesh_data['xmin'])
                    max_x = max(max_x, mesh_data['xmax'])
                    min_y = min(min_y, mesh_data['ymin'])
                    max_y = max(max_y, mesh_data['ymax'])
                    min_z = min(min_z, mesh_data['zmin'])
                    max_z = max(max_z, mesh_data['zmax'])
                    
            # Calculate center and size of bounding box
            center = ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
            size = max(max_x - min_x, max_y - min_y, max_z - min_z)
            
            # Set camera to frame the selection
            self.view.setCameraPosition(
                center=center,
                distance=size * 1.5  # Add some padding
            )
            
        except Exception as e:
            print(f"Error in _frame_selected: {e}")
            
    def _frame_all_meshes(self):
        """
        Frame all meshes in the view.
        """
        try:
            # Check if we have meshes
            if not self.mesh_items:
                return
                
            # Calculate bounding box of all meshes
            min_x = min_y = min_z = float('inf')
            max_x = max_y = max_z = float('-inf')
            
            for mesh_data in self.mesh_items.values():
                data = mesh_data['data']
                min_x = min(min_x, data['xmin'])
                max_x = max(max_x, data['xmax'])
                min_y = min(min_y, data['ymin'])
                max_y = max(max_y, data['ymax'])
                min_z = min(min_z, data['zmin'])
                max_z = max(max_z, data['zmax'])
                
            # Calculate center and size of bounding box
            center = ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
            size = max(max_x - min_x, max_y - min_y, max_z - min_z)
            
            # Set camera to frame all meshes
            self.view.setCameraPosition(
                center=center,
                distance=size * 1.5  # Add some padding
            )
            
        except Exception as e:
            print(f"Error in _frame_all_meshes: {e}")
            
    def _toggle_grid(self):
        """
        Toggle the visibility of the reference grid.
        """
        try:
            # Toggle visibility of the main grid layer
            if self.grid_system:
                layers = self.grid_system.get_visible_layers()
                if layers:
                    # Toggle the first visible layer
                    layer = layers[0]
                    self.grid_system.set_layer_visibility(layer.name, False)
                else:
                    # If no visible layers, make the main layer visible
                    self.grid_system.set_layer_visibility("main", True)
            
        except Exception as e:
            print(f"Error in _toggle_grid: {e}")
            
    def _handle_mesh_selection(self, event):
        """
        Handle mesh selection based on mouse click.
        
        :param event: Mouse event
        """
        try:
            # Get mouse position
            pos = event.pos()
            
            # Convert screen coordinates to 3D ray
            # This is a simplified approach using the camera parameters
            camera_params = self.view.cameraParams()
            center = camera_params['center']
            elevation = camera_params['elevation']
            azimuth = camera_params['azimuth']
            distance = camera_params['distance']
            
            # Calculate ray direction based on camera orientation
            import math
            elev_rad = math.radians(elevation)
            azim_rad = math.radians(azimuth)
            
            # Calculate camera position
            cam_x = center[0] + distance * math.cos(elev_rad) * math.cos(azim_rad)
            cam_y = center[1] + distance * math.cos(elev_rad) * math.sin(azim_rad)
            cam_z = center[2] + distance * math.sin(elev_rad)
            
            # For a full implementation, we would need to do 3D picking
            # Since that's complex with PyQtGraph, we'll implement a simplified version
            # that selects the mesh closest to the camera ray through the mouse position
            
            # Find the mesh closest to the camera position as a simple heuristic
            closest_mesh_id = None
            min_distance = float('inf')
            
            for mesh_id, mesh_data in self.mesh_items.items():
                mesh = mesh_data['data']
                # Calculate mesh center
                mesh_center_x = (mesh['xmin'] + mesh['xmax']) / 2
                mesh_center_y = (mesh['ymin'] + mesh['ymax']) / 2
                mesh_center_z = (mesh['zmin'] + mesh['zmax']) / 2
                
                # Calculate distance from camera to mesh center
                dist = math.sqrt(
                    (cam_x - mesh_center_x)**2 +
                    (cam_y - mesh_center_y)**2 +
                    (cam_z - mesh_center_z)**2
                )
                
                if dist < min_distance:
                    min_distance = dist
                    closest_mesh_id = mesh_id
            
            if closest_mesh_id:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    # Toggle selection
                    if closest_mesh_id in self.selected_meshes:
                        self.deselect_mesh(closest_mesh_id)
                    else:
                        self.select_mesh(closest_mesh_id)
                else:
                    # Clear previous selection and select this mesh
                    self.clear_selection()
                    self.select_mesh(closest_mesh_id)
            
        except Exception as e:
            print(f"Error in _handle_mesh_selection: {e}")
            
    def load_mesh_data(self, meshes):
        """
        Load mesh data and render as 3D boxes.
        
        :param meshes: List of mesh dictionaries with keys:
                      'id', 'i', 'j', 'k', 'xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax'
        """
        try:
            # Validate input
            if not isinstance(meshes, (list, tuple)):
                raise TypeError("Meshes must be a list or tuple")
            
            # Clear existing mesh items
            self.clear_meshes()
            
            # Add each mesh to the view
            for mesh in meshes:
                if not isinstance(mesh, dict):
                    print(f"Warning: Skipping invalid mesh data: {mesh}")
                    continue
                self.add_mesh(mesh)
                
            # Update the view
            self.update_view()
            
        except Exception as e:
            print(f"Error loading mesh data: {e}")
            raise
            
    def add_mesh(self, mesh):
        """
        Add a single mesh to the 3D view.
        
        :param mesh: Dictionary with mesh data
        """
        try:
            # Validate mesh data
            required_keys = ['id', 'xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']
            for key in required_keys:
                if key not in mesh:
                    raise ValueError(f"Missing required key '{key}' in mesh data")
            
            mesh_id = mesh['id']
            
            # Check if mesh already exists
            if mesh_id in self.mesh_items:
                print(f"Warning: Mesh with ID '{mesh_id}' already exists. Updating instead.")
                self.update_mesh(mesh_id, mesh)
                return
            
            # Convert FDS mesh data to 3D box vertices and faces
            vertices, faces = self._convert_mesh_to_box(mesh)
            
            # Generate a color for this mesh
            color = self._generate_mesh_color(mesh_id)
            
            # Create mesh item
            mesh_item = gl.GLMeshItem(
                vertexes=vertices,
                faces=faces,
                color=color,
                smooth=False,
                drawEdges=True,
                edgeColor=(1, 1, 1, 1)  # White edges
            )
            
            # Add to view
            self.view.addItem(mesh_item)
            
            # Store reference
            self.mesh_items[mesh_id] = {
                'item': mesh_item,
                'data': mesh.copy(), # Store a copy of the original data
                'color': color,
                'is_selected': False
            }
            
            # Populate optimized data structures
            self._update_mesh_optimized_data(mesh_id, mesh)
            
        except Exception as e:
            print(f"Error adding mesh {mesh.get('id', 'unknown')}: {e}")
            raise
            
    def remove_mesh(self, mesh_id):
        """
        Remove a mesh from the 3D view.
        
        :param mesh_id: ID of the mesh to remove
        """
        try:
            if mesh_id in self.mesh_items:
                mesh_data = self.mesh_items[mesh_id]
                mesh_item = mesh_data['item']
                if mesh_item:
                    self.view.removeItem(mesh_item)
                del self.mesh_items[mesh_id]
                
                # Remove from selection if selected
                if mesh_id in self.selected_meshes:
                    self.selected_meshes.discard(mesh_id)
                    
        except Exception as e:
            print(f"Error removing mesh {mesh_id}: {e}")
            raise
            
    def clear_meshes(self):
        """
        Remove all meshes from the 3D view.
        """
        try:
            # Create a copy of the keys to avoid modifying dict during iteration
            mesh_ids = list(self.mesh_items.keys())
            
            # Remove all meshes
            for mesh_id in mesh_ids:
                self.remove_mesh(mesh_id)
                
            # Clear selection
            self.selected_meshes.clear()
            
        except Exception as e:
            print(f"Error clearing meshes: {e}")
            raise
            
    def remove_mesh(self, mesh_id):
        """
        Remove a mesh from the 3D view.
        
        :param mesh_id: ID of the mesh to remove
        """
        try:
            if mesh_id in self.mesh_items:
                mesh_data = self.mesh_items[mesh_id]
                mesh_item = mesh_data['item']
                if mesh_item:
                    self.view.removeItem(mesh_item)
                del self.mesh_items[mesh_id]
                
                # Remove from selection if selected
                if mesh_id in self.selected_meshes:
                    self.selected_meshes.discard(mesh_id)
                    
        except Exception as e:
            print(f"Error removing mesh {mesh_id}: {e}")
            raise
            
    def update_mesh(self, mesh_id, new_mesh_data):
        """
        Update an existing mesh with new data.
        
        :param mesh_id: ID of the mesh to update
        :param new_mesh_data: New mesh data dictionary
        """
        try:
            # Validate input
            if not isinstance(new_mesh_data, dict):
                raise TypeError("New mesh data must be a dictionary")
                
            # Check if mesh exists
            if mesh_id not in self.mesh_items:
                # If mesh doesn't exist, add it
                new_mesh_data['id'] = mesh_id
                self.add_mesh(new_mesh_data)
                return
            
            # Remove the old mesh
            self.remove_mesh(mesh_id)
            
            # Add the updated mesh
            new_mesh_data['id'] = mesh_id
            self.add_mesh(new_mesh_data)
            
        except Exception as e:
            print(f"Error updating mesh {mesh_id}: {e}")
            raise
            
    def select_mesh(self, mesh_id):
        """
        Select a mesh and highlight it.
        
        :param mesh_id: ID of the mesh to select
        """
        try:
            if mesh_id not in self.mesh_items:
                print(f"Warning: Mesh with ID '{mesh_id}' not found")
                return
                
            # Add to selection
            self.selected_meshes.add(mesh_id)
            
            # Update mesh appearance
            mesh_data = self.mesh_items[mesh_id]
            mesh_item = mesh_data['item']
            
            # Store original color and set highlight color
            original_color = mesh_data['color']
            # Use a more distinct highlight color (bright yellow with full opacity)
            highlight_color = (1.0, 1.0, 0.0, 1.0)  # Bright yellow
            
            mesh_item.setColor(highlight_color)
            mesh_data['is_selected'] = True
            
            # Add a visual indicator for selection (e.g., change edge color)
            mesh_item.setEdgeColor((1, 1, 0, 1))  # Yellow edges for selected mesh
            
            # Emit selection changed signal
            self.mesh_selection_changed.emit(self.selected_meshes.copy())
            
        except Exception as e:
            print(f"Error selecting mesh {mesh_id}: {e}")
            raise
            
    def deselect_mesh(self, mesh_id):
        """
        Deselect a mesh and remove highlight.
        
        :param mesh_id: ID of the mesh to deselect
        """
        try:
            if mesh_id not in self.mesh_items:
                print(f"Warning: Mesh with ID '{mesh_id}' not found")
                return
                
            # Remove from selection
            self.selected_meshes.discard(mesh_id)
            
            # Update mesh appearance
            mesh_data = self.mesh_items[mesh_id]
            mesh_item = mesh_data['item']
            original_color = mesh_data['color']
            
            mesh_item.setColor(original_color)
            mesh_item.setEdgeColor((1, 1, 1, 1))  # Restore default white edges
            mesh_data['is_selected'] = False
            
            # Emit selection changed signal
            self.mesh_selection_changed.emit(self.selected_meshes.copy())
            
        except Exception as e:
            print(f"Error deselecting mesh {mesh_id}: {e}")
            raise
            
    def clear_selection(self):
        """
        Clear all mesh selections.
        """
        try:
            # Create a copy to avoid modifying set during iteration
            selected_meshes = self.selected_meshes.copy()
            
            # Deselect all selected meshes
            for mesh_id in selected_meshes:
                self.deselect_mesh(mesh_id)
                
            # Emit selection changed signal (in case all meshes were already deselected)
            self.mesh_selection_changed.emit(self.selected_meshes.copy())
                
        except Exception as e:
            print(f"Error clearing selection: {e}")
            raise
            
    def get_selected_meshes(self):
        """
        Get the IDs of all selected meshes.
        
        :return: Set of selected mesh IDs
        """
        return self.selected_meshes.copy()
        
    def get_selected_mesh_data(self):
        """
        Get detailed data for all selected meshes.
        
        :return: List of dictionaries containing mesh data for selected meshes
        """
        selected_data = []
        for mesh_id in self.selected_meshes:
            # Check cache first
            if mesh_id in self.mesh_data_cache:
                mesh_data = self.mesh_data_cache[mesh_id].copy()
                mesh_data['id'] = mesh_id
                selected_data.append(mesh_data)
            elif mesh_id in self.mesh_items:
                mesh_data = self.mesh_items[mesh_id]['data'].copy()
                mesh_data['id'] = mesh_id
                # Add to cache
                self.mesh_data_cache[mesh_id] = mesh_data.copy()
                selected_data.append(mesh_data)
        return selected_data
        
    def _cache_mesh_data(self, mesh_id, mesh_data):
        """
        Cache mesh data for efficient access.
        
        :param mesh_id: ID of the mesh
        :param mesh_data: Mesh data to cache
        """
        self.mesh_data_cache[mesh_id] = mesh_data.copy()
        
    def _invalidate_mesh_data_cache(self, mesh_id):
        """
        Invalidate cached mesh data.
        
        :param mesh_id: ID of the mesh
        """
        if mesh_id in self.mesh_data_cache:
            del self.mesh_data_cache[mesh_id]
            
        # Also invalidate optimized data structures
        if mesh_id in self.mesh_bounding_boxes:
            del self.mesh_bounding_boxes[mesh_id]
        if mesh_id in self.mesh_centroids:
            del self.mesh_centroids[mesh_id]
            
    def _update_mesh_optimized_data(self, mesh_id, mesh_data):
        """
        Update optimized data structures for a mesh.
        
        :param mesh_id: ID of the mesh
        :param mesh_data: Mesh data dictionary
        """
        try:
            # Update bounding box cache
            bbox = (
                mesh_data['xmin'], mesh_data['ymin'], mesh_data['zmin'],
                mesh_data['xmax'], mesh_data['ymax'], mesh_data['zmax']
            )
            self.mesh_bounding_boxes[mesh_id] = bbox
            
            # Update centroid cache
            centroid = (
                (mesh_data['xmin'] + mesh_data['xmax']) / 2,
                (mesh_data['ymin'] + mesh_data['ymax']) / 2,
                (mesh_data['zmin'] + mesh_data['zmax']) / 2
            )
            self.mesh_centroids[mesh_id] = centroid
            
        except Exception as e:
            print(f"Error updating optimized data for mesh {mesh_id}: {e}")
        
    def _convert_mesh_to_box(self, mesh):
        """
        Convert FDS mesh data to vertices and faces for a 3D box.
        
        :param mesh: Dictionary with mesh data
        :return: Tuple of (vertices, faces)
        """
        try:
            # Extract coordinates
            xmin = float(mesh['xmin'])
            xmax = float(mesh['xmax'])
            ymin = float(mesh['ymin'])
            ymax = float(mesh['ymax'])
            zmin = float(mesh['zmin'])
            zmax = float(mesh['zmax'])
            
            # Validate coordinates
            if xmin >= xmax or ymin >= ymax or zmin >= zmax:
                raise ValueError("Invalid mesh coordinates: min values must be less than max values")
            
            # Define the 8 vertices of the box
            vertices = np.array([
                [xmin, ymin, zmin], # 0
                [xmax, ymin, zmin], # 1
                [xmax, ymax, zmin], # 2
                [xmin, ymax, zmin], # 3
                [xmin, ymin, zmax], # 4
                [xmax, ymin, zmax], # 5
                [xmax, ymax, zmax], # 6
                [xmin, ymax, zmax] # 7
            ], dtype=np.float32)
            
            # Define the 12 triangular faces (2 triangles per box face)
            faces = np.array([
                # Bottom face (z = zmin)
                [0, 1, 2], [0, 2, 3],
                # Top face (z = zmax)
                [4, 7, 6], [4, 6, 5],
                # Front face (y = ymin)
                [0, 4, 5], [0, 5, 1],
                # Back face (y = ymax)
                [2, 6, 7], [2, 7, 3],
                # Left face (x = xmin)
                [0, 3, 7], [0, 7, 4],
                # Right face (x = xmax)
                [1, 5, 6], [1, 6, 2]
            ], dtype=np.uint32)
            
            return vertices, faces
            
        except Exception as e:
            print(f"Error converting mesh to box: {e}")
            raise
            
    def _optimize_mesh_rendering(self):
        """
        Apply performance optimizations to mesh rendering.
        """
        try:
            # Disable auto-rendering during bulk operations
            self.view.setUpdatesEnabled(False)
            
            # Re-enable updates when done
            self.view.setUpdatesEnabled(True)
            
        except Exception as e:
            print(f"Error optimizing mesh rendering: {e}")
            
    def _optimize_grid_rendering(self):
        """
        Apply performance optimizations to grid rendering.
        """
        try:
            if not self.grid_system:
                return
                
            # Temporarily hide all grid layers during updates
            layer_visibility = {}
            items_to_remove = []
            for name, layer in self.grid_system.layers.items():
                layer_visibility[name] = layer.visible
                if layer.visible and layer.grid_item:
                    items_to_remove.append(layer.grid_item)
                    
            # Batch remove items for better performance
            for item in items_to_remove:
                self.view.removeItem(item)
                
            # Perform grid updates
            for layer in self.grid_system.layers.values():
                layer.update_grid_item()
                
            # Process UI events to keep the interface responsive
            self._process_ui_events()
                
            # Restore grid layer visibility
            items_to_add = []
            for name, visible in layer_visibility.items():
                if visible:
                    layer = self.grid_system.layers[name]
                    if layer.grid_item:
                        items_to_add.append(layer.grid_item)
                        
            # Batch add items for better performance
            for item in items_to_add:
                if item not in self.view.items:
                    self.view.addItem(item)
                        
        except Exception as e:
            print(f"Error optimizing grid rendering: {e}")
            # Restore grid items even if there was an error
            for layer in self.grid_system.layers.values():
                if layer.visible and layer.grid_item and layer.grid_item not in self.view.items:
                    self.view.addItem(layer.grid_item)
            
    def _batch_update_meshes(self, mesh_updates):
        """
        Update multiple meshes in a batch for better performance.
        
        :param mesh_updates: List of (mesh_id, new_mesh_data) tuples
        """
        try:
            # Disable view updates during batch operation
            self.view.setUpdatesEnabled(False)
            
            # Perform all updates
            for mesh_id, new_mesh_data in mesh_updates:
                self.update_mesh(mesh_id, new_mesh_data)
                
            # Re-enable updates and refresh view
            self.view.setUpdatesEnabled(True)
            self.view.update()
            
        except Exception as e:
            print(f"Error in batch update: {e}")
            # Make sure to re-enable updates even on error
            self.view.setUpdatesEnabled(True)
            raise
            
    def _generate_mesh_color(self, mesh_id):
        """
        Generate a distinct color for a mesh based on its ID.
        
        :param mesh_id: ID of the mesh
        :return: RGBA color tuple
        """
        try:
            # Simple hash-based color generation for consistent colors
            hash_value = hash(str(mesh_id))
            
            # Use different parts of the hash for RGB values
            r = ((hash_value & 0xFF00) >> 16) / 255.0
            g = ((hash_value & 0x00FF00) >> 8) / 25.0
            b = (hash_value & 0x0000FF) / 255.0
            
            # Ensure colors aren't too dark for visibility
            r = max(0.3, r)
            g = max(0.3, g)
            b = max(0.3, b)
            
            # Add some transparency
            return (r, g, b, self.default_color_alpha)
            
        except Exception as e:
            print(f"Error generating color for mesh {mesh_id}: {e}")
            # Return a default color
            return (0.5, 0.5, 1.0, self.default_color_alpha)  # Light blue default
            
    def update_view(self):
        """
        Update the 3D view, e.g., after adding/removing meshes.
        Implements deferred updates for better performance.
        """
        try:
            # If we're already updating, mark that we need another update
            if self.updating_view:
                self.needs_view_update = True
                return
                
            # Set updating flag
            self.updating_view = True
            
            # Perform the update
            self.view.update()
            
            # Reset flags
            self.updating_view = False
            
            # If another update was requested during this update, do it now
            if self.needs_view_update:
                self.needs_view_update = False
                self.update_view()
            
        except Exception as e:
            print(f"Error updating view: {e}")
            # Reset flags even on error
            self.updating_view = False
            self.needs_view_update = False
            raise
            
    def reset_view(self):
        """
        Reset the camera view to default position.
        """
        try:
            # Reset to perspective mode by default
            if self.is_orthographic:
                self.toggle_orthographic()  # This will switch back to perspective
                
            # Set default camera position
            self.view.setCameraPosition(distance=50)
            
        except Exception as e:
            print(f"Error resetting view: {e}")
            raise
            
    def toggle_orthographic(self):
        """
        Toggle between orthographic and perspective projection.
        This is an approximation since PyQtGraph doesn't directly support orthographic projection.
        """
        try:
            # Toggle the flag
            self.is_orthographic = not self.is_orthographic
            
            # Update the projection
            if self.is_orthographic:
                # Approximate orthographic view by moving the camera far away
                # and zooming in, which reduces the perspective effect
                camera_params = self.view.cameraParams()
                distance = camera_params['distance']
                
                # Move camera further away and zoom in to reduce perspective effect
                self.view.setCameraPosition(distance=distance * 100)
                print("Orthographic mode approximated")
            else:
                # Return to normal perspective view
                camera_params = self.view.cameraParams()
                distance = camera_params['distance']
                
                # Move camera closer to restore perspective effect
                self.view.setCameraPosition(distance=distance / 100)
                print("Perspective mode restored")
            
        except Exception as e:
            print(f"Error toggling orthographic mode: {e}")
            
    def set_background_color(self, color):
        """
        Set the background color of the 3D view.
        
        :param color: Color name or hex code
        """
        try:
            self.view.setBackgroundColor(color)
            
        except Exception as e:
            print(f"Error setting background color: {e}")
            raise
            
    def set_grid_visible(self, visible):
        """
        Show or hide the reference grid.
        
        :param visible: Boolean indicating whether grid should be visible
        """
        try:
            if self.grid_system:
                # Set visibility for all layers
                for layer_name in self.grid_system.layers:
                    self.grid_system.set_layer_visibility(layer_name, visible)
                    
        except Exception as e:
            print(f"Error setting grid visibility: {e}")
            raise
            
    def closeEvent(self, event):
        """
        Handle cleanup when the widget is closed.
        
        :param event: Close event
        """
        try:
            # Clean up resources
            self.clear_meshes()
            
            # Remove visual feedback items
            self._remove_axis_guides()
            self._remove_transformation_handles()
            self._remove_snap_feedback()
            
            # Clean up performance monitoring
            if self.frame_timer:
                self.frame_timer.stop()
                self.frame_timer = None
                
            # Clean up performance label
            if self.performance_label:
                self.performance_label.setParent(None)
                self.performance_label = None
                
            # Call parent implementation
            super().closeEvent(event)
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Still call parent implementation to ensure proper closing
            super().closeEvent(event)
            
    def _cleanup_opengl_resources(self):
        """
        Clean up OpenGL resources.
        """
        try:
            # Clean up mesh items
            for mesh_id in list(self.mesh_items.keys()):
                mesh_data = self.mesh_items[mesh_id]
                mesh_item = mesh_data['item']
                if mesh_item:
                    # Remove from view
                    self.view.removeItem(mesh_item)
                    # Clear references
                    mesh_data['item'] = None
                    
            # Clean up grid items
            if self.grid_system:
                for layer in self.grid_system.layers.values():
                    if layer.grid_item:
                        self.view.removeItem(layer.grid_item)
                        layer.grid_item = None
                        
            # Clean up visual feedback items
            self._remove_axis_guides()
            self._remove_transformation_handles()
            self._remove_snap_feedback()
            
            # Clean up performance label
            if self.performance_label:
                self.performance_label.setParent(None)
                self.performance_label = None
                
            # Clear optimized data structures
            self.mesh_bounding_boxes.clear()
            self.mesh_centroids.clear()
            self.mesh_data_cache.clear()
            
            # Clear mesh items dictionary
            self.mesh_items.clear()
            self.selected_meshes.clear()
            
        except Exception as e:
            print(f"Error cleaning up OpenGL resources: {e}")


    def _start_transformation(self, event):
        """
        Start a transformation operation on selected meshes.
        
        :param event: Mouse event
        """
        if not self.selected_meshes:
            return
            
        self.is_transforming = True
        self.transform_start_pos = event.pos()
        
        # Store initial positions of selected meshes
        self.transform_initial_positions = {}
        for mesh_id in self.selected_meshes:
            if mesh_id in self.mesh_items:
                mesh_data = self.mesh_items[mesh_id]['data']
                self.transform_initial_positions[mesh_id] = {
                    'xmin': mesh_data['xmin'],
                    'xmax': mesh_data['xmax'],
                    'ymin': mesh_data['ymin'],
                    'ymax': mesh_data['ymax'],
                    'zmin': mesh_data['zmin'],
                    'zmax': mesh_data['zmax']
                }
                
        # Create visual feedback
        # Calculate center of selected meshes for placing guides
        if self.selected_meshes:
            first_mesh_id = next(iter(self.selected_meshes))
            first_mesh_data = self.mesh_items[first_mesh_id]['data']
            center_x = (first_mesh_data['xmin'] + first_mesh_data['xmax']) / 2
            center_y = (first_mesh_data['ymin'] + first_mesh_data['ymax']) / 2
            center_z = (first_mesh_data['zmin'] + first_mesh_data['zmax']) / 2
            self._create_axis_guides((center_x, center_y, center_z))
            self._create_transformation_handles((center_x, center_y, center_z))
    
    def _update_transformation(self, event):
        """
        Update a transformation operation based on mouse movement.
        
        :param event: Mouse event
        """
        if not self.is_transforming or not self.selected_meshes:
            return
            
        # Calculate movement delta
        delta_x = event.pos().x() - self.transform_start_pos.x()
        delta_y = event.pos().y() - self.transform_start_pos.y()
        
        # Convert screen delta to 3D world coordinates (simplified)
        # In a full implementation, this would use the camera parameters
        # to convert screen movement to 3D movement
        movement_scale = 0.1  # Adjust this value as needed
        world_delta_x = delta_x * movement_scale
        world_delta_y = delta_y * movement_scale
        world_delta_z = 0  # For now, no Z movement in 2D screen space
        
        # Apply axis constraint if specified
        if self.constraint_axis == 'x':
            world_delta_y = 0
            world_delta_z = 0
        elif self.constraint_axis == 'y':
            world_delta_x = 0
            world_delta_z = 0
        elif self.constraint_axis == 'z':
            world_delta_x = 0
            world_delta_y = 0
            
        # Apply snap-to-grid if enabled
        if self.grid_system and self.grid_system.snap_enabled:
            # Apply snapping using the grid system
            snapped_position = self.grid_system.snap_position((world_delta_x, world_delta_y, world_delta_z))
            world_delta_x, world_delta_y, world_delta_z = snapped_position
            
            # Show snap feedback if position was snapped
            if snapped_position != (world_delta_x, world_delta_y, world_delta_z):
                self._show_snap_feedback(snapped_position)
        
        # Update positions of selected meshes
        for mesh_id in self.selected_meshes:
            if mesh_id in self.mesh_items and mesh_id in self.transform_initial_positions:
                mesh_item = self.mesh_items[mesh_id]
                initial_pos = self.transform_initial_positions[mesh_id]
                
                # Calculate new positions
                new_xmin = initial_pos['xmin'] + world_delta_x
                new_xmax = initial_pos['xmax'] + world_delta_x
                new_ymin = initial_pos['ymin'] + world_delta_y
                new_ymax = initial_pos['ymax'] + world_delta_y
                new_zmin = initial_pos['zmin'] + world_delta_z
                new_zmax = initial_pos['zmax'] + world_delta_z
                
                # Update mesh data
                mesh_item['data']['xmin'] = new_xmin
                mesh_item['data']['xmax'] = new_xmax
                mesh_item['data']['ymin'] = new_ymin
                mesh_item['data']['ymax'] = new_ymax
                mesh_item['data']['zmin'] = new_zmin
                mesh_item['data']['zmax'] = new_zmax
                
                # Update the mesh visualization
                # Process UI events to keep the interface responsive
                self._process_ui_events()
                
                self._update_mesh_visualization(mesh_id)
                
                # Invalidate cache
                self._invalidate_mesh_data_cache(mesh_id)
    
    def _finish_transformation(self):
        """
        Finish a transformation operation.
        """
        self.is_transforming = False
        self.transform_start_pos = None
        self.transform_initial_positions = {}
        
        # Prepare transformed data for signal
        transformed_data = {}
        for mesh_id in self.selected_meshes:
            if mesh_id in self.mesh_items:
                mesh_data = self.mesh_items[mesh_id]['data']
                transformed_data[mesh_id] = mesh_data.copy()
        
        # Emit transformation completed signal
        self.mesh_transformation_completed.emit(transformed_data)
        
        # Remove visual feedback
        self._remove_axis_guides()
        self._remove_transformation_handles()
        self._remove_snap_feedback()
    
    def _update_mesh_visualization(self, mesh_id):
        """
        Update the visualization of a mesh after its data has changed.
        
        :param mesh_id: ID of the mesh to update
        """
        if mesh_id not in self.mesh_items:
            return
            
        mesh_item = self.mesh_items[mesh_id]
        mesh_data = mesh_item['data']
        
        # Create new vertices and faces based on updated data
        vertices, faces = self._convert_mesh_to_box(mesh_data)
        
        # Check if the mesh item has a setMeshData method for incremental updates
        if hasattr(mesh_item['item'], 'setMeshData'):
            # Use incremental update if possible
            try:
                mesh_item['item'].setMeshData(vertexes=vertices, faces=faces)
                return
            except Exception as e:
                # If setMeshData fails, fall back to full rebuild
                print(f"Failed to update mesh incrementally: {e}")
                pass
        
        # Fallback to full rebuild if incremental update is not possible
        # Remove the old mesh item
        self.view.removeItem(mesh_item['item'])
        
        # Create new mesh item
        new_mesh_item = gl.GLMeshItem(
            vertexes=vertices,
            faces=faces,
            color=mesh_item['color'],
            smooth=False,
            drawEdges=True,
            edgeColor=(1, 1, 0, 1) if mesh_item['is_selected'] else (1, 1, 1, 1)
        )
        
        # Add to view
        self.view.addItem(new_mesh_item)
        
        # Update reference
        mesh_item['item'] = new_mesh_item
        
    def set_ui_update_priority(self, priority):
        """
        Set UI update priority.
        
        :param priority: Boolean indicating whether to prioritize UI updates
        """
        self.ui_update_priority = priority
        
    def should_prioritize_ui_updates(self):
        """
        Check if UI updates should be prioritized.
        
        :return: Boolean indicating whether to prioritize UI updates
        """
        return self.ui_update_priority
        
    def _process_ui_events(self):
        """
        Process UI events to keep the interface responsive.
        """
        if self.should_prioritize_ui_updates():
            # Process UI events to keep the interface responsive
            from PyQt6.QtCore import QCoreApplication
            # Only process pending events to avoid blocking
            QCoreApplication.processEvents()
            
    def set_transformation_mode(self, mode):
        """
        Set the transformation mode.
        
        :param mode: Transformation mode ('move', 'rotate', 'scale', or None to disable)
        """
        if mode not in ('move', 'rotate', 'scale', None):
            raise ValueError("Invalid transformation mode")
        self.transformation_mode = mode
        
    def set_constraint_axis(self, axis):
        """
        Set the constraint axis for transformations.
        
        :param axis: Constraint axis ('x', 'y', 'z', or None for free movement)
        """
        if axis not in ('x', 'y', 'z', None):
            raise ValueError("Invalid constraint axis")
        self.constraint_axis = axis
        
    def set_snap_to_grid(self, enabled, grid_size=1.0):
        """
        Enable or disable snap-to-grid functionality.
        
        :param enabled: Whether to enable snap-to-grid
        :param grid_size: Size of the grid for snapping
        """
        if self.grid_system:
            self.grid_system.set_snap_settings(enabled, grid_size)
        
    def get_transformed_mesh_data(self):
        """
        Get the current mesh data for all meshes, which can be used to update the FDS file.
        
        :return: List of dictionaries containing mesh data
        """
        mesh_data_list = []
        for mesh_id, mesh_item in self.mesh_items.items():
            mesh_data = mesh_item['data'].copy()
            mesh_data['id'] = mesh_id
            mesh_data_list.append(mesh_data)
        return mesh_data_list
        
    def add_grid_layer(self, name, spacing=1.0, color=(1, 0.5), orientation='XY', visible=True, offset=(0, 0, 0)):
        """
        Add a new grid layer.
        
        :param name: Name of the layer
        :param spacing: Grid spacing
        :param color: Grid color (RGBA)
        :param orientation: Grid orientation ('XY', 'XZ', 'YZ', 'XYZ')
        :param visible: Whether the layer is visible
        :param offset: Grid offset (x, y, z)
        """
        if self.grid_system:
            return self.grid_system.add_layer(name, spacing=spacing, color=color, orientation=orientation, visible=visible, offset=offset)
            
    def remove_grid_layer(self, name):
        """
        Remove a grid layer.
        
        :param name: Name of the layer to remove
        """
        if self.grid_system:
            self.grid_system.remove_layer(name)
            
    def set_grid_layer_visibility(self, name, visible):
        """
        Set the visibility of a grid layer.
        
        :param name: Name of the layer
        :param visible: Visibility state
        """
        if self.grid_system:
            self.grid_system.set_layer_visibility(name, visible)
            
    def set_grid_layer_spacing(self, name, spacing):
        """
        Set the spacing of a grid layer.
        
        :param name: Name of the layer
        :param spacing: New spacing value
        """
        if self.grid_system and name in self.grid_system.layers:
            layer = self.grid_system.layers[name]
            layer.spacing = spacing
            # Use optimized grid rendering
            self.optimize_grid_rendering()
            
    def set_active_grid_layer(self, name):
        """
        Set the active grid layer for snapping.
        
        :param name: Name of the layer to set as active
        """
        if self.grid_system:
            self.grid_system.set_active_layer(name)
            
    def get_grid_layers(self):
        """
        Get all grid layers.
        
        :return: Dictionary of grid layers
        """
        if self.grid_system:
            return self.grid_system.layers
        return {}
        
    def _adjust_grid_spacing(self, factor):
        """
        Adjust the spacing of all grid layers by a factor.
        
        :param factor: Multiplication factor for spacing adjustment
        """
        if not self.grid_system:
            return
            
        for layer in self.grid_system.layers.values():
            new_spacing = layer.spacing * factor
            # Ensure spacing doesn't become too small
            if new_spacing < 0.01:
                new_spacing = 0.01
            layer.spacing = new_spacing
            layer.update_grid_item()
        
    def save_grid_settings(self):
        """
        Save current grid settings to a dictionary.
        
        :return: Dictionary containing grid settings
        """
        if not self.grid_system:
            return {}
            
        settings = {
            'snap_enabled': self.grid_system.snap_enabled,
            'snap_threshold': self.grid_system.snap_threshold,
            'layers': {}
        }
        
        for name, layer in self.grid_system.layers.items():
            settings['layers'][name] = {
                'spacing': layer.spacing,
                'color': layer.color,
                'orientation': layer.orientation,
                'visible': layer.visible,
                'offset': layer.offset
            }
            
        return settings
        
    def restore_grid_settings(self, settings):
        """
        Restore grid settings from a dictionary.
        
        :param settings: Dictionary containing grid settings
        """
        if not self.grid_system or not settings:
            return
            
        # Restore snap settings
        if 'snap_enabled' in settings:
            self.grid_system.snap_enabled = settings['snap_enabled']
        if 'snap_threshold' in settings:
            self.grid_system.snap_threshold = settings['snap_threshold']
            
        # Restore layer settings
        if 'layers' in settings:
            # Remove existing layers
            layer_names = list(self.grid_system.layers.keys())
            for name in layer_names:
                self.remove_grid_layer(name)
                
            # Add new layers with saved settings
            for name, layer_settings in settings['layers'].items():
                self.add_grid_layer(
                    name,
                    spacing=layer_settings.get('spacing', 1.0),
                    color=layer_settings.get('color', (1, 1, 0.5)),
                    orientation=layer_settings.get('orientation', 'XY'),
                    visible=layer_settings.get('visible', True),
                    offset=layer_settings.get('offset', (0, 0))
                )
        
    def set_grid_layer_offset(self, name, offset):
        """
        Set the offset of a grid layer.
        
        :param name: Name of the layer
        :param offset: New offset (x, y, z tuple)
        """
        if self.grid_system and name in self.grid_system.layers:
            layer = self.grid_system.layers[name]
            layer.offset = offset
            layer.update_grid_item()
            
    def set_grid_layer_color(self, name, color):
        """
        Set the color of a grid layer.
        
        :param name: Name of the layer
        :param color: New color (RGBA tuple)
        """
        if self.grid_system and name in self.grid_system.layers:
            layer = self.grid_system.layers[name]
            layer.set_color(color)
            
    def set_grid_layer_orientation(self, name, orientation):
        """
        Set the orientation of a grid layer.
        
        :param name: Name of the layer
        :param orientation: New orientation ('XY', 'XZ', 'YZ', 'XYZ')
        """
        if self.grid_system and name in self.grid_system.layers:
            layer = self.grid_system.layers[name]
            layer.set_orientation(orientation)
            
    def batch_update_grid_layers(self, updates):
        """
        Update multiple grid layers in a batch for better performance.
        
        :param updates: List of tuples (layer_name, property, value)
        """
        if not self.grid_system:
            return
            
        try:
            # Apply optimizations during batch update
            self._optimize_grid_rendering()
            
            # Apply all updates
            for layer_name, property_name, value in updates:
                if layer_name in self.grid_system.layers:
                    layer = self.grid_system.layers[layer_name]
                    if property_name == 'spacing':
                        layer.spacing = value
                    elif property_name == 'color':
                        layer.set_color(value)
                    elif property_name == 'orientation':
                        layer.set_orientation(value)
                    elif property_name == 'visible':
                        self.set_grid_layer_visibility(layer_name, value)
                    elif property_name == 'offset':
                        layer.offset = value
                        
            # Update all grid items
            for layer in self.grid_system.layers.values():
                layer.update_grid_item()
                
        except Exception as e:
            print(f"Error in batch grid update: {e}")
            
    def optimize_grid_rendering(self):
        """
        Optimize grid rendering performance.
        """
        try:
            if not self.grid_system:
                return
                
            # Temporarily hide all grid layers during updates
            layer_visibility = {}
            items_to_remove = []
            for name, layer in self.grid_system.layers.items():
                layer_visibility[name] = layer.visible
                if layer.visible and layer.grid_item:
                    items_to_remove.append(layer.grid_item)
                    
            # Batch remove items for better performance
            for item in items_to_remove:
                self.view.removeItem(item)
                
            # Perform grid updates
            for layer in self.grid_system.layers.values():
                layer.update_grid_item()
                
            # Process UI events to keep the interface responsive
            self._process_ui_events()
                
            # Restore grid layer visibility
            items_to_add = []
            for name, visible in layer_visibility.items():
                if visible:
                    layer = self.grid_system.layers[name]
                    if layer.grid_item:
                        items_to_add.append(layer.grid_item)
                        
            # Batch add items for better performance
            for item in items_to_add:
                if item not in self.view.items:
                    self.view.addItem(item)
                        
        except Exception as e:
            print(f"Error optimizing grid rendering: {e}")
            # Restore grid items even if there was an error
            for layer in self.grid_system.layers.values():
                if layer.visible and layer.grid_item and layer.grid_item not in self.view.items:
                    self.view.addItem(layer.grid_item)
            
    def _create_axis_guides(self, position):
        """
        Create axis-aligned visual guides for transformation.
        
        :param position: Position to create the guides at (x, y, z tuple)
        """
        # Remove existing axis guides
        self._remove_axis_guides()
        
        # Create new axis guides (simple lines for now)
        x, y, z = position
        
        # X-axis guide (red)
        x_axis_vertices = np.array([[x, y, z], [x + 10, y, z]], dtype=np.float32)
        x_axis_faces = np.array([[0, 1, 1]], dtype=np.uint32)  # Line
        x_axis_item = gl.GLMeshItem(
            vertexes=x_axis_vertices,
            faces=x_axis_faces,
            color=(1, 0, 0, 1),  # Red
            smooth=False,
            drawEdges=True,
            edgeColor=(1, 0, 0, 1)
        )
        self.axis_guides.append(x_axis_item)
        self.view.addItem(x_axis_item)
        
        # Process UI events to keep the interface responsive
        self._process_ui_events()
        
        # Y-axis guide (green)
        y_axis_vertices = np.array([[x, y, z], [x, y + 10, z]], dtype=np.float32)
        y_axis_faces = np.array([[0, 1, 1]], dtype=np.uint32)  # Line
        y_axis_item = gl.GLMeshItem(
            vertexes=y_axis_vertices,
            faces=y_axis_faces,
            color=(0, 1, 0, 1),  # Green
            smooth=False,
            drawEdges=True,
            edgeColor=(0, 1, 0, 1)
        )
        self.axis_guides.append(y_axis_item)
        self.view.addItem(y_axis_item)
        
        # Process UI events to keep the interface responsive
        self._process_ui_events()
        
        # Z-axis guide (blue)
        z_axis_vertices = np.array([[x, y, z], [x, y, z + 10]], dtype=np.float32)
        z_axis_faces = np.array([[0, 1, 1]], dtype=np.uint32)  # Line
        z_axis_item = gl.GLMeshItem(
            vertexes=z_axis_vertices,
            faces=z_axis_faces,
            color=(0, 0, 1, 1),  # Blue
            smooth=False,
            drawEdges=True,
            edgeColor=(0, 0, 1, 1)
        )
        self.axis_guides.append(z_axis_item)
        self.view.addItem(z_axis_item)
        
        # Process UI events to keep the interface responsive
        self._process_ui_events()
        
    def _remove_axis_guides(self):
        """
        Remove all axis guide items from the view.
        """
        for guide_item in self.axis_guides:
            self.view.removeItem(guide_item)
        self.axis_guides = []
        
    def _create_transformation_handles(self, position):
        """
        Create transformation handles (gizmos) for intuitive manipulation.
        
        :param position: Position to create the handles at (x, y, z tuple)
        """
        # Remove existing transformation handles
        self._remove_transformation_handles()
        
        # Create new transformation handles (simple spheres for now)
        x, y, z = position
        
        # X-axis handle (red sphere)
        x_handle_vertices, x_handle_faces = self._create_sphere(x + 5, y, z, 0.5)
        x_handle_item = gl.GLMeshItem(
            vertexes=x_handle_vertices,
            faces=x_handle_faces,
            color=(1, 0, 1),  # Red
            smooth=False,
            drawEdges=True,
            edgeColor=(1, 0, 0, 1)
        )
        self.transformation_handles.append(x_handle_item)
        self.view.addItem(x_handle_item)
        
        # Y-axis handle (green sphere)
        y_handle_vertices, y_handle_faces = self._create_sphere(x, y + 5, z, 0.5)
        y_handle_item = gl.GLMeshItem(
            vertexes=y_handle_vertices,
            faces=y_handle_faces,
            color=(0, 1, 0, 1),  # Green
            smooth=False,
            drawEdges=True,
            edgeColor=(0, 1, 0, 1)
        )
        self.transformation_handles.append(y_handle_item)
        self.view.addItem(y_handle_item)
        
        # Z-axis handle (blue sphere)
        z_handle_vertices, z_handle_faces = self._create_sphere(x, y, z + 5, 0.5)
        z_handle_item = gl.GLMeshItem(
            vertexes=z_handle_vertices,
            faces=z_handle_faces,
            color=(0, 0, 1, 1),  # Blue
            smooth=False,
            drawEdges=True,
            edgeColor=(0, 0, 1, 1)
        )
        self.transformation_handles.append(z_handle_item)
        self.view.addItem(z_handle_item)
        
    def _remove_transformation_handles(self):
        """
        Remove all transformation handle items from the view.
        """
        for handle_item in self.transformation_handles:
            self.view.removeItem(handle_item)
        self.transformation_handles = []
        
    def _show_snap_feedback(self, position):
        """
        Show visual feedback when snapping occurs.
        
        :param position: Position where snapping occurred (x, y, z tuple)
        """
        # Remove existing snap feedback
        self._remove_snap_feedback()
        
        # Create a visual indicator at the snapped position
        x, y, z = position
        vertices, faces = self._create_sphere(x, y, z, 0.3, 6)
        snap_item = gl.GLMeshItem(
            vertexes=vertices,
            faces=faces,
            color=(1, 1, 0, 1),  # Yellow
            smooth=False,
            drawEdges=True,
            edgeColor=(1, 1, 0, 1)
        )
        self.snap_feedback_items.append(snap_item)
        self.view.addItem(snap_item)
        
        # Schedule removal of feedback after a short delay
        # In a real implementation, you might use a QTimer for this
        # For now, we'll just leave it until the next transformation
        
        # Process UI events to keep the interface responsive
        self._process_ui_events()
        
        # Process UI events to keep the interface responsive
        self._process_ui_events()
        
    def _remove_snap_feedback(self):
        """
        Remove all snap feedback items from the view.
        """
        for feedback_item in self.snap_feedback_items:
            self.view.removeItem(feedback_item)
        self.snap_feedback_items = []
        
    def _create_sphere(self, x, y, z, radius, segments=8):
        """
        Create vertices and faces for a sphere.
        
        :param x: X coordinate of the center
        :param y: Y coordinate of the center
        :param z: Z coordinate of the center
        :param radius: Radius of the sphere
        :param segments: Number of segments for the sphere
        :return: Tuple of (vertices, faces)
        """
        # Create vertices
        vertices = []
        faces = []
        
        # Generate vertices
        for i in range(segments + 1):
            for j in range(segments + 1):
                theta = i * np.pi / segments
                phi = j * 2 * np.pi / segments
                vx = x + radius * np.sin(theta) * np.cos(phi)
                vy = y + radius * np.sin(theta) * np.sin(phi)
                vz = z + radius * np.cos(theta)
                vertices.append([vx, vy, vz])
                
        # Generate faces
        for i in range(segments):
            for j in range(segments):
                # Calculate indices for the four vertices of a quad
                a = i * (segments + 1) + j
                b = a + 1
                c = (i + 1) * (segments + 1) + j
                d = c + 1
                
                # Create two triangles for the quad
                faces.append([a, b, c])
                faces.append([b, d, c])
                
        return np.array(vertices, dtype=np.float32), np.array(faces, dtype=np.uint32)

# Example usage and testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("FDS Mesh Viewer 3D - Test")
    main_window.resize(80, 600)
    
    # Create viewer
    viewer = FDSMeshViewer3D()
    main_window.setCentralWidget(viewer)
    
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
    viewer.load_mesh_data(sample_meshes)
    
    # Test selection
    viewer.select_mesh('Mesh1')
    
    main_window.show()
    sys.exit(app.exec())