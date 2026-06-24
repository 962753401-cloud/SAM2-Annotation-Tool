"""Simple test script to check if the application can start"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("Testing imports...")

# Test basic imports
try:
    from PyQt6.QtWidgets import QApplication, QMainWindow
    print("[OK] PyQt6 imported successfully")
except Exception as e:
    print(f"[FAIL] PyQt6 import failed: {e}")
    sys.exit(1)

# Test config loader
try:
    from src.utils.config_loader import ConfigLoader
    config = ConfigLoader()
    print(f"[OK] Config loaded, model path: {config.get('model.path')}")
except Exception as e:
    print(f"[FAIL] Config loader failed: {e}")

# Test core modules
try:
    from src.core.annotation_data import Annotation, ImageAnnotation
    ann = Annotation(class_name="test")
    print(f"[OK] Annotation created: {ann.class_name}")
except Exception as e:
    print(f"[FAIL] Annotation data failed: {e}")

try:
    from src.core.image_manager import ImageManager
    print("[OK] ImageManager imported")
except Exception as e:
    print(f"[FAIL] ImageManager failed: {e}")

try:
    from src.core.project_manager import ProjectManager
    print("[OK] ProjectManager imported")
except Exception as e:
    print(f"[FAIL] ProjectManager failed: {e}")

# Test GUI modules
try:
    from src.gui.canvas_widget import CanvasWidget
    print("[OK] CanvasWidget imported")
except Exception as e:
    print(f"[FAIL] CanvasWidget failed: {e}")

try:
    from src.gui.image_list import ImageList
    print("[OK] ImageList imported")
except Exception as e:
    print(f"[FAIL] ImageList failed: {e}")

try:
    from src.gui.layer_list import LayerList
    print("[OK] LayerList imported")
except Exception as e:
    print(f"[FAIL] LayerList failed: {e}")

# Test exporters
try:
    from src.exporters.voc_exporter import VOCExporter
    from src.exporters.coco_exporter import COCOExporter
    print("[OK] Exporters imported")
except Exception as e:
    print(f"[FAIL] Exporters failed: {e}")

print("\nAll basic tests completed!")
print("Starting GUI test...")

# Try to create a simple window
try:
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("SAM2 Annotation Tool Test")
    window.resize(800, 600)
    window.show()
    print("[OK] Basic window created successfully")
    print("Close the window to continue...")
    # app.exec()  # Uncomment to run the actual window
except Exception as e:
    print(f"[FAIL] Window creation failed: {e}")

print("\nTest complete!")