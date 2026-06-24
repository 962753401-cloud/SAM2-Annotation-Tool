# SAM2 Annotation Tool

> [中文](./README_CN.md) | **English**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![SAM2](https://img.shields.io/badge/Engine-SAM2-red.svg)](https://github.com/facebookresearch/sam2)

An intelligent image segmentation annotation tool powered by Meta SAM2 (Segment Anything Model 2). Click to segment, zero-shot annotation of any object.

## Features

### Smart Segmentation
- **Click Segmentation** -- Left-click on a target area, SAM2 automatically generates segmentation boundaries
- **Box Segmentation** -- Drag a rectangle to trigger segmentation
- **Polygon Drawing** -- Click continuously to manually annotate complex boundaries, right-click to close

### Annotation Management
- Real-time annotation list with select, delete, and visibility toggle
- Add custom text descriptions to each annotation
- 12 preset categories with hierarchical classification (animals/vehicles/buildings, etc.)
- Drag vertices to fine-tune boundaries, right-click menu to insert/delete vertices

### Quality Assessment
- Built-in quality scoring system: comprehensive score, boundary smoothness, vertex density
- SAM2 confidence automatically recorded (average >94%)
- Configurable vertex density (low/medium/high)

### Data Export
- **COCO JSON** -- Universal object detection/segmentation training
- **Pascal VOC XML** -- Traditional CV task compatibility
- Exports include quality metrics and confidence extension fields

## Quick Start

### Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python    | 3.10+   | 3.12+       |
| Memory    | 8 GB    | 16 GB+      |
| GPU       | None (CPU works) | NVIDIA 8 GB+ |

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/SAM2-Annotation-Tool.git
cd SAM2-Annotation-Tool

# Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configure the Model

Edit `config.yaml` to set the SAM2 model path:

```yaml
model:
  path: "models/sam2_hiera_tiny.pt"
  config_path: "models/sam2_hiera_t.yaml"
  device: "cuda"  # use "cpu" if no GPU
```

Download model weights from the [SAM2 official repository](https://github.com/facebookresearch/sam2).

### Launch

```bash
python main.py
```

## Usage Workflow

```
Open image folder -> Select tool -> Click/box target -> SAM2 auto-segment
                                                          |
Export COCO/VOC <- Confirm annotation (add text) <- Fine-tune boundary (drag vertices)
```

**Keyboard Shortcuts**
- `Ctrl+O` Open folder
- `Ctrl+S` Save project
- `Delete` Delete selected annotation
- Mouse wheel Zoom canvas

## Technical Architecture

```
+---------------------------------------------+
|         UI Layer (PyQt6)                    |
|   ImageList | CanvasWidget | LayerList      |
+---------------------------------------------+
|         Business Logic Layer                |
|   MainWindow | ImageManager | ProjectManager|
+---------------------------------------------+
|         Core Engine Layer                   |
|            SAM2Engine                       |
|   (PyTorch + SAM2 + OpenCV)                 |
+---------------------------------------------+
|         Data Layer                          |
|   Annotation | COCOExporter | VOCExporter   |
+---------------------------------------------+
```

## Project Structure

```
SAM2-Annotation-Tool/
+-- main.py                 # Application entry point
+-- config.yaml             # Configuration
+-- requirements.txt        # Dependencies
+-- src/
|   +-- core/
|   |   +-- sam2_engine.py     # SAM2 segmentation engine
|   |   +-- annotation_data.py # Data models
|   |   +-- image_manager.py   # Image management
|   |   +-- project_manager.py # Project management
|   +-- gui/
|   |   +-- main_window.py     # Main window
|   |   +-- canvas_widget.py   # Canvas widget
|   |   +-- layer_list.py      # Annotation panel
|   |   +-- image_list.py      # Image list
|   |   +-- tool_bar.py        # Toolbar
|   +-- exporters/
|   |   +-- coco_exporter.py   # COCO export
|   |   +-- voc_exporter.py    # VOC export
|   +-- utils/
|       +-- config_loader.py   # Config loader
|       +-- file_utils.py      # File utilities
|       +-- image_utils.py     # Image utilities
+-- tests/
+-- docs/
```

## Quality Metrics

The tool computes a quality score for each annotation:

```
quality_score = 0.5 * confidence + 0.3 * density_score + 0.2 * smoothness
```

| Metric               | Range  | Description                        |
|----------------------|--------|------------------------------------|
| quality_score        | 0--1   | Comprehensive quality score        |
| boundary_smoothness  | 0--1   | Boundary smoothness                |
| vertex_count         | int    | Number of polygon vertices         |
| vertex_density       | 0--20  | Vertex density (per 100px perimeter)|
| confidence           | 0--1   | SAM2 model confidence              |

## Comparison

| Feature           | SAM2 Annotation Tool | LabelImg | LabelMe | CVAT |
|-------------------|---------------------|----------|---------|------|
| Smart segmentation| SAM2-driven         | Manual   | Manual  | Requires config |
| Zero-shot         | Yes                 | No       | No      | No   |
| Quality metrics   | Built-in            | None     | None    | Basic |
| Vertex density    | Configurable        | No       | No      | No   |
| Local execution   | Yes                 | Yes      | Yes     | Requires deploy |
| Learning curve    | Low                 | Low      | Medium  | High |

## Dependencies

- PyQt6 >= 6.0.0
- PyTorch >= 2.0.0
- SAM2 >= 0.4.0
- OpenCV >= 4.8.0
- Pillow >= 10.0.0
- NumPy >= 1.24.0
- PyYAML >= 6.0

## Documentation

- [Product Introduction (Chinese)](./docs/PRODUCT_INTRODUCTION.md)
- [Technical Architecture (Chinese)](./docs/TECHNICAL_ARCHITECTURE.md)

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT License -- see [LICENSE](./LICENSE) for details.

## Acknowledgments

- [Meta SAM2](https://github.com/facebookresearch/sam2) -- The segmentation model powering this tool
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) -- GUI framework
- [OpenCV](https://opencv.org/) -- Image processing
