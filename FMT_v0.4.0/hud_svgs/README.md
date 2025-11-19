# HUD SVG Components

This directory contains minimal SVG designs for the HUD components in the FDS Mesh Tools project.

## Components

1. `orientation_cube.svg` - Minimal wireframe cube with directional indicators (60x60px)
2. `select_icon.svg` - Minimal icon for Select mode (24x24px)
3. `pan_icon.svg` - Minimal icon for Pan mode (24x24px)
4. `orbit_icon.svg` - Minimal icon for Orbit mode (24x24px)
5. `zoom_icon.svg` - Minimal icon for Zoom mode (24x24px)
6. `selection_overlay.svg` - Semi-transparent design for selection rectangle

## Integration Instructions

### Orientation Cube Widget

To integrate the new orientation cube SVG:

1. Replace the existing PyQt6-based drawing code in `orientation_cube_widget.py` with SVG rendering:
   ```python
   from PyQt6.QtSvgWidgets import QSvgWidget
   
   class OrientationCubeWidget(QSvgWidget):
       def __init__(self, parent=None):
           super().__init__(parent)
           self.load("hud_svgs/orientation_cube.svg")
           self.setFixedSize(60, 60)
   ```

2. Update the widget size to match the SVG dimensions (60x60px)

3. For dynamic highlighting of the current orientation, create multiple SVG variants or use SVG manipulation:
   ```python
   # Example of changing highlight
   def set_orientation(self, orientation):
       if orientation == 'front':
           self.load("hud_svgs/orientation_cube_front.svg")
       # ... other orientations
   ```

### Toolbar Buttons

To integrate the toolbar button icons:

1. Replace the text-based buttons in `fds_3d_viewer.py` with icon-based buttons:
   ```python
   from PyQt6.QtGui import QIcon
   
   # For each button, replace text with icons:
   self.select_button = QToolButton()
   self.select_button.setIcon(QIcon("hud_svgs/select_icon.svg"))
   self.select_button.setIconSize(QSize(24, 24))
   self.select_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
   ```

2. Adjust button sizes to match the 24x24px icons

3. Update the CSS styling to accommodate icon-only buttons:
   ```css
   QToolButton {
       border: 1px solid #8f8f91;
       border-radius: 4px;
       background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                         stop: 0 #f6f7fa, stop: 1 #dadbde);
       width: 32px;
       height: 32px;
       padding: 4px;
   }
   ```

### Selection Overlay

To integrate the selection overlay:

1. Replace the existing `OverlayWidget` paintEvent method in `fds_3d_viewer.py`:
   ```python
   from PyQt6.QtSvgWidgets import QSvgWidget
   
   class OverlayWidget(QSvgWidget):
       def __init__(self, parent=None):
           super().__init__(parent)
           self.load("hud_svgs/selection_overlay.svg")
           self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
           
       def set_drag_rectangle(self, rect):
           if rect is not None:
               x1, y1, x2, y2 = rect
               width = abs(x2 - x1)
               height = abs(y2 - y1)
               self.setGeometry(min(x1, x2), min(y1, y2), width, height)
               self.show()
           else:
               self.hide()
   ```

2. Ensure the overlay remains semi-transparent and non-blocking

## Design Principles

All SVGs follow these design principles:
- Minimal visual footprint
- Clean, simple lines
- Limited color palette (primarily grayscale with accent colors)
- Consistent sizing and styling
- Optimized for clarity at small sizes
- SVG 1.1 compatibility for broad support

## Customization

To customize the appearance:
1. Modify the SVG files directly with a text editor or vector graphics editor
2. Adjust colors by changing the hex values
3. Modify stroke widths for bolder or subtler lines
4. Change opacities for different transparency effects

## Troubleshooting

If SVGs don't display correctly:
1. Ensure the file paths are correct relative to your executable
2. Check that PyQt6 SVG support is installed
3. Verify SVG files are valid by opening them in a browser
4. Consider converting to PNG if SVG support is problematic