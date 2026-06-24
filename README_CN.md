# SAM2 标注工具

> **中文** | [English](./README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![SAM2](https://img.shields.io/badge/Engine-SAM2-red.svg)](https://github.com/facebookresearch/sam2)

基于 Meta SAM2（Segment Anything Model 2）的智能图像分割标注工具。点击即分割，零样本标注任意物体。

## 功能特性

### 智能分割
- **点击分割** —— 左键点击目标区域，SAM2 自动生成分割边界
- **框选分割** —— 拖拽矩形框触发分割
- **多边形绘制** —— 连续点击手动标注复杂边界，右键闭合

### 标注管理
- 标注列表实时显示，支持选择、删除、可见性切换
- 为每个标注添加自定义文本描述
- 12 种预设类别，支持层级分类（动物/车辆/建筑等）
- 顶点拖拽微调边界，右键菜单插入/删除顶点

### 质量评估
- 内置质量评分体系：综合评分、边界平滑度、顶点密度
- SAM2 置信度自动记录（平均 >94%）
- 可配置顶点密度（低/中/高）

### 数据导出
- **COCO JSON** —— 通用目标检测/分割训练
- **Pascal VOC XML** —— 传统 CV 任务兼容
- 导出包含质量指标和置信度等扩展字段

## 快速开始

### 环境要求

| 配置 | 最低要求 | 推荐 |
|------|---------|------|
| Python | 3.10+ | 3.12+ |
| 内存 | 8GB | 16GB+ |
| GPU | 无（CPU 可用） | NVIDIA 8GB+ |

### 安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/SAM2-Annotation-Tool.git
cd SAM2-Annotation-Tool

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 配置模型

编辑 `config.yaml`，设置 SAM2 模型路径：

```yaml
model:
  path: "models/sam2_hiera_tiny.pt"
  config_path: "models/sam2_hiera_t.yaml"
  device: "cuda"  # 无 GPU 改为 "cpu"
```

模型下载：从 [SAM2 官方仓库](https://github.com/facebookresearch/sam2) 获取 `sam2_hiera_tiny.pt` 权重文件。

### 启动

```bash
python main.py
```

## 使用流程

```
打开图片文件夹 -> 选择标注工具 -> 点击/框选目标 -> SAM2 自动分割
                                                    |
导出 COCO/VOC <- 确认标注（添加文本） <- 微调边界（拖拽顶点）
```

**快捷键**
- `Ctrl+O` 打开文件夹
- `Ctrl+S` 保存项目
- `Delete` 删除选中标注
- 鼠标滚轮缩放画布

## 技术架构

```
+---------------------------------------------+
|         用户界面层 (PyQt6)                   |
|   ImageList | CanvasWidget | LayerList       |
+---------------------------------------------+
|         业务逻辑层                           |
|   MainWindow | ImageManager | ProjectManager |
+---------------------------------------------+
|         核心引擎层                           |
|            SAM2Engine                        |
|   (PyTorch + SAM2 + OpenCV)                  |
+---------------------------------------------+
|         数据层                               |
|   Annotation | COCOExporter | VOCExporter    |
+---------------------------------------------+
```

## 项目结构

```
SAM2-Annotation-Tool/
+-- main.py                 # 应用入口
+-- config.yaml             # 配置文件
+-- requirements.txt        # 依赖清单
+-- src/
|   +-- core/
|   |   +-- sam2_engine.py     # SAM2 分割引擎
|   |   +-- annotation_data.py # 数据模型
|   |   +-- image_manager.py   # 图片管理
|   |   +-- project_manager.py # 项目管理
|   +-- gui/
|   |   +-- main_window.py     # 主窗口
|   |   +-- canvas_widget.py   # 画布控件
|   |   +-- layer_list.py      # 标注面板
|   |   +-- image_list.py      # 图片列表
|   |   +-- tool_bar.py        # 工具栏
|   +-- exporters/
|   |   +-- coco_exporter.py   # COCO 导出
|   |   +-- voc_exporter.py    # VOC 导出
|   +-- utils/
|       +-- config_loader.py   # 配置加载
|       +-- file_utils.py      # 文件工具
|       +-- image_utils.py     # 图像工具
+-- tests/
+-- docs/
```

## 质量评估指标

工具为每个标注计算质量评分：

```
quality_score = 0.5 * confidence + 0.3 * density_score + 0.2 * smoothness
```

| 指标 | 范围 | 说明 |
|------|------|------|
| quality_score | 0-1 | 综合质量评分 |
| boundary_smoothness | 0-1 | 边界平滑度 |
| vertex_count | 整数 | 多边形顶点数量 |
| vertex_density | 0-20 | 顶点密度（每100px边长） |
| confidence | 0-1 | SAM2 模型置信度 |

## 竞品对比

| 特性 | SAM2 Annotation Tool | LabelImg | LabelMe | CVAT |
|------|---------------------|----------|---------|------|
| 智能分割 | SAM2 驱动 | 手动 | 手动 | 需配置 |
| 零样本标注 | 支持 | 不支持 | 不支持 | 不支持 |
| 质量评估 | 内置 | 无 | 无 | 基础 |
| 顶点密度控制 | 可配置 | 无 | 无 | 无 |
| 本地运行 | 支持 | 支持 | 支持 | 需部署 |
| 学习成本 | 低 | 低 | 中 | 高 |

## 依赖

- PyQt6 >= 6.0.0
- PyTorch >= 2.0.0
- SAM2 >= 0.4.0
- OpenCV >= 4.8.0
- Pillow >= 10.0.0
- NumPy >= 1.24.0
- PyYAML >= 6.0

## 文档

- [产品介绍文档](./docs/PRODUCT_INTRODUCTION.md)
- [技术架构文档](./docs/TECHNICAL_ARCHITECTURE.md)

## 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解贡献指南。

## 许可证

MIT License —— 详见 [LICENSE](./LICENSE)

## 致谢

- [Meta SAM2](https://github.com/facebookresearch/sam2) —— 驱动本工具的分割模型
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) —— GUI 框架
- [OpenCV](https://opencv.org/) —— 图像处理
