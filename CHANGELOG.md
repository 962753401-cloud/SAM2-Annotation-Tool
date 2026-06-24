# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06

### Added
- SAM2-powered intelligent segmentation (point-click and box-select).
- Manual polygon drawing mode.
- 12 preset annotation classes with hierarchical supercategories.
- Vertex-level boundary fine-tuning (drag, add, delete vertices).
- Built-in quality metrics: quality_score, boundary_smoothness, vertex_density.
- COCO JSON and Pascal VOC XML export with quality metadata.
- Dark-theme PyQt6 interface with image list, canvas, and annotation panel.
- Undo/redo history, zoom, and fit-to-window.
- Configuration via config.yaml (model path, polygon density, quality thresholds).
- Unit tests for canvas widget, quality metrics, and config loader.

### Known Limitations
- SAM2 model weights must be downloaded separately.
- Video frame annotation is planned for a future release.
