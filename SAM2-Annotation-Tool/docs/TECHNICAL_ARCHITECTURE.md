# SAM2 Annotation Tool 技术架构文档

## 文档概述

| 属性 | 值 |
|------|-----|
| 文档类型 | 技术架构设计文档 |
| 适用版本 | v1.0.0 |
| 目标读者 | 开发工程师、架构师、技术决策者 |
| 更新日期 | 2026年4月22日 |

---

## 1. 技术栈总览

### 1.1 核心技术栈

| 层级 | 技术选型 | 版本要求 | 选型理由 |
|------|---------|---------|---------|
| **UI框架** | PyQt6 | >=6.0.0 | 跨平台GUI、信号槽机制、丰富控件生态 |
| **深度学习** | PyTorch | >=2.0.0 | SAM2官方支持、CUDA优化、动态图特性 |
| **分割模型** | SAM2 | >=0.4.0 | Meta最新分割模型、零样本能力强 |
| **图像处理** | OpenCV | >=4.8.0 | 高效图像操作、轮廓提取、Mask处理 |
| **数据序列化** | YAML/JSON | - | 配置管理灵活、COCO标准格式 |
| **测试框架** | pytest | >=9.0 | 插件丰富、断言简洁、覆盖率支持 |

### 1.2 技术栈依赖关系

```
┌─────────────────────────────────────────────────────────┐
│                    应用层                                │
│                      PyQt6                               │
├─────────────────────────────────────────────────────────┤
│                    业务层                                │
│         Annotation Data + Project Manager               │
├─────────────────────────────────────────────────────────┤
│                    引擎层                                │
│      SAM2Engine (PyTorch + SAM2 + OpenCV)               │
├─────────────────────────────────────────────────────────┤
│                    基础层                                │
│           NumPy + Pillow + YAML Parser                  │
└─────────────────────────────────────────────────────────┘
```

### 1.3 运行环境

```yaml
# requirements.txt 核心依赖
PyQt6>=6.0.0        # GUI框架
torch>=2.0.0        # 深度学习后端
sam2>=0.4.0         # 分割模型
opencv-python>=4.8.0  # 图像处理
pillow>=10.0.0      # 图像IO
numpy>=1.24.0       # 数值计算
pyyaml>=6.0         # 配置解析
transformers>=4.40.0  # 模型辅助
pytest>=9.0         # 测试框架
```

---

## 2. 系统架构设计

### 2.1 四层架构模型

本项目采用**分层架构设计**，实现关注点分离：

```
┌──────────────────────────────────────────────────────────────────┐
│                         Presentation Layer                        │
│                           (表现层)                                │
│  ┌────────────┬─────────────────┬──────────────────┬───────────┐ │
│  │ MainWindow │  CanvasWidget   │    LayerList     │ ImageList │ │
│  │  (主窗口)   │   (画布控件)     │   (标注面板)     │ (图片列表) │ │
│  └────────────┴─────────────────┴──────────────────┴───────────┘ │
│                              ↓ Signal/Slot                        │
├──────────────────────────────────────────────────────────────────┤
│                         Business Logic Layer                      │
│                           (业务逻辑层)                            │
│  ┌────────────────┬─────────────────┬──────────────────────────┐ │
│  │ ProjectManager │   ImageManager  │   AnnotationController   │ │
│  │   (项目管理)    │    (图片管理)    │      (标注控制)          │ │
│  └────────────────┴─────────────────┴──────────────────────────┘ │
│                              ↓ API Call                           │
├──────────────────────────────────────────────────────────────────┤
│                           Engine Layer                            │
│                            (引擎层)                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      SAM2Engine                              │ │
│  │  ┌──────────────┬──────────────────┬───────────────────────┐│ │
│  │  │ Model Loader │ Inference Engine │  Geometry Processor   ││ │
│  │  │  (模型加载)   │   (推理引擎)      │     (几何处理)        ││ │
│  │  └──────────────┴──────────────────┴───────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              ↓ Data Access                        │
├──────────────────────────────────────────────────────────────────┤
│                           Data Layer                              │
│                            (数据层)                               │
│  ┌────────────┬──────────────────┬─────────────────────────────┐ │
│  │ Annotation │ ImageAnnotation  │     AnnotationProject       │ │
│  │  (标注)     │  (图像标注集)     │        (项目)              │ │
│  └────────────┴──────────────────┴─────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Exporters                                 │ │
│  │  ┌──────────────────┬──────────────────────────────────────┐│ │
│  │  │   COCOExporter   │           VOCExporter                ││ │
│  │  └──────────────────┴──────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 各层职责定义

#### 表现层 (Presentation Layer)

| 组件 | 职责 | 关键特性 |
|------|------|---------|
| `MainWindow` | 应用入口、窗口布局、菜单管理 | QMainWindow派生、信号槽连接中心 |
| `CanvasWidget` | 图像显示、交互绘制、标注渲染 | QPainter绘制、鼠标事件处理、历史记录 |
| `LayerList` | 标注列表、编辑面板、导出控制 | QListWidget、文本输入、确认流程 |
| `ImageList` | 图片浏览、批量加载 | 文件列表、缩略图预览 |

#### 业务逻辑层 (Business Logic Layer)

| 组件 | 职责 | 关键特性 |
|------|------|---------|
| `ProjectManager` | 项目生命周期管理 | 创建/加载/保存/导出协调 |
| `ImageManager` | 图片加载与导航 | 批量加载、索引管理、尺寸获取 |
| `AnnotationController` | 标注CRUD操作 | 隐式嵌入MainWindow中 |

#### 引擎层 (Engine Layer)

| 组件 | 职责 | 关键特性 |
|------|------|---------|
| `SAM2Engine` | SAM2模型推理封装 | 模型加载、图像编码、Mask预测、几何转换 |

#### 数据层 (Data Layer)

| 组件 | 职责 | 关键特性 |
|------|------|---------|
| `Annotation` | 单个标注数据实体 | @dataclass、质量指标、序列化 |
| `ImageAnnotation` | 单图标注集合 | 标注列表管理、增删改查 |
| `AnnotationProject` | 整体项目数据 | 图片集合、类别定义、项目持久化 |
| `Exporters` | 格式转换输出 | COCO/VOC标准格式生成 |

### 2.3 架构设计原则

| 原则 | 实现方式 |
|------|---------|
| **单一职责** | 每个类只负责一个明确的功能域 |
| **开闭原则** | Exporter通过BaseExporter抽象，支持扩展新格式 |
| **依赖倒置** | 业务层不直接依赖UI，通过Signal/Slot解耦 |
| **接口隔离** | 各Manager提供最小化API接口 |
| **数据驱动** | Annotation使用@dataclass，自动属性管理 |

---

## 3. 核心模块技术实现

### 3.1 SAM2Engine 分割引擎

#### 模块职责
封装SAM2模型推理全流程，提供统一的分割API。

#### 核心API设计

```python
class SAM2Engine:
    """SAM2模型推理引擎封装"""
    
    # 生命周期管理
    def load_model(self) -> bool                    # 模型加载
    def set_image(self, image: np.ndarray) -> bool  # 图像编码
    
    # 推理接口
    def predict_from_points(self, points) -> Tuple  # 点点击分割
    def predict_from_box(self, box) -> Tuple        # 框选分割
    
    # 结果处理
    def get_best_mask(self, masks, scores) -> np.ndarray  # 最佳Mask选择
    def mask_to_polygon(self, mask, epsilon=0.005) -> List  # Mask→Polygon转换
    def mask_to_bbox(self, mask) -> List[int]              # Mask→BBox提取
    
    # 资源管理
    def release(self)                               # 释放GPU资源
```

#### 技术实现要点

**1. 模型加载策略**
```python
def load_model(self) -> bool:
    # 主路径：build_sam2 + checkpoint
    sam2_model = build_sam2(config_file, checkpoint, device=device)
    
    # 备用路径：from_pretrained（网络下载）
    self.predictor = SAM2ImagePredictor.from_pretrained("sam2-hiera-tiny")
    
    # 设备自适应：CUDA优先，CPU fallback
    self.device = device if torch.cuda.is_available() else "cpu"
```

**2. 多边形近似算法**
```python
def mask_to_polygon(self, mask, epsilon_factor=0.005):
    # 二值化
    binary_mask = (mask > 0.5).astype(np.uint8)
    
    # 轮廓提取
    contours = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Douglas-Peucker近似（可配置精度）
    epsilon = epsilon_factor * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    # 顶点限制（性能保护）
    max_vertices = 100
    if len(approx) > max_vertices:
        # 动态调整epsilon直到满足限制
        ...
```

**3. 推理性能优化**
- 多Mask输出：`multimask_output=True` 提供备选
- 置信度选择：`np.argmax(scores)` 自动选最佳
- 内存管理：`torch.cuda.empty_cache()` 及时释放

### 3.2 Annotation 数据模型

#### 数据结构设计

```python
@dataclass
class Annotation:
    """单个标注对象 - 核心数据实体"""
    
    # 基础标识
    id: int                          # 唯一标识符
    class_name: str = "object"       # 类别名称
    class_id: int = 0                # 类别ID
    
    # 分割数据
    mask: Optional[np.ndarray]       # 像素级Mask（可选）
    polygon: List[List[int]]         # 多边形顶点坐标
    bbox: List[int]                  # 边界框 [x,y,w,h]
    
    # 元数据
    confidence: float = 0.0          # SAM2置信度
    is_manual: bool = False          # 手动/自动标记
    label: str = ""                  # 文本标注内容
    color: str = "#ff0000"           # 显示颜色
    visible: bool = True             # 可见性
    locked: bool = False             # 锁定状态
    
    # 质量指标（新增）
    quality_score: float = 0.0       # 综合评分
    boundary_smoothness: float = 0.0 # 边界平滑度
    vertex_count: int = 0            # 顶点数量
    vertex_density: float = 0.0      # 顶点密度
```

#### 质量评估算法实现

```python
def calculate_quality_metrics(self, config=None) -> Dict[str, float]:
    """质量指标计算核心算法"""
    
    # 1. 周长计算（Shoelace扩展）
    perimeter = self._calculate_perimeter()
    
    # 2. 顶点密度（归一化上限20）
    vertex_density = min(20.0, vertex_count / (perimeter / 100))
    
    # 3. 边界平滑度（角度变化标准差）
    angle_changes = self._calculate_angle_changes()
    std_angles = np.std(angle_changes)
    smoothness = max(0.0, min(1.0, 1.0 - std_angles / 90.0))
    
    # 4. 综合评分（加权算法）
    quality_score = 0.5 * confidence + 0.3 * density_score + 0.2 * smoothness
```

#### 序列化支持

```python
def to_dict(self) -> Dict[str, Any]:
    """转换为字典（JSON序列化）"""
    return {
        "id": self.id,
        "polygon": self.polygon,        # 直接可序列化
        "bbox": self.bbox,
        "confidence": self.confidence,
        "quality_score": self.quality_score,
        # mask不序列化（太大）
    }

def from_dict(self, data) -> 'Annotation':
    """从字典恢复（支持向后兼容）"""
    # 新字段缺失时使用默认值
    self.quality_score = data.get("quality_score", 0.0)
```

### 3.3 CanvasWidget 交互画布

#### 渲染架构

```python
class CanvasWidget(QWidget):
    """画布控件 - 核心交互区域"""
    
    def paintEvent(self, event):
        """绘制事件 - QPainter渲染管线"""
        painter = QPainter(self)
        try:
            # 1. 背景绘制
            painter.fillRect(self.rect(), QColor(42, 42, 42))
            
            # 2. 图像绘制（缩放适配）
            scaled_pixmap = self.pixmap.scaled(
                target_width, target_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            painter.drawPixmap(self.offset, scaled_pixmap)
            
            # 3. 标注绘制（遍历渲染）
            for annotation in self.annotations:
                self.draw_polygon_outline(painter, annotation)
                self.draw_label_text(painter, annotation)
            
            # 4. 临时绘制（正在绘制的形状）
            if self.drawing_box:
                self.draw_temp_box(painter)
        except Exception as e:
            # 异常捕获：防止崩溃
            self.draw_error_message(painter, e)
        finally:
            painter.end()
```

#### 坐标转换系统

```python
def screen_to_image(self, point: QPoint) -> Tuple[int, int]:
    """屏幕坐标 → 图像坐标"""
    x = int((point.x() - self.offset.x()) / self.scale)
    y = int((point.y() - self.offset.y()) / self.scale)
    # 边界裁剪
    x = max(0, min(x, self.pixmap.width() - 1))
    y = max(0, min(y, self.pixmap.height() - 1))
    return (x, y)

def image_to_screen(self, point: Tuple[int, int]) -> QPoint:
    """图像坐标 → 屏幕坐标"""
    return QPoint(
        int(point[0] * self.scale + self.offset.x()),
        int(point[1] * self.scale + self.offset.y())
    )
```

#### 交互事件处理

```python
def mousePressEvent(self, event):
    """鼠标按下 - 工具分发"""
    if event.button() == Qt.LeftButton:
        if self.current_tool == "point":
            # 点点击分割 → 触发SAM2
            image_pos = self.screen_to_image(pos)
            self.point_clicked.emit(image_pos)
        
        elif self.current_tool == "box":
            # 开始框选
            self.drawing_box = True
            self.box_start = pos
        
        elif self.current_tool == "edit":
            # 顶点拖拽检测
            self.check_vertex_drag(pos)
```

#### 状态管理

```python
# 显示状态
self.scale: float = 1.0           # 缩放比例
self.offset: QPoint               # 偏移量
self.min_scale: float = 0.1       # 最小缩放
self.max_scale: float = 10.0      # 最大缩放

# 交互状态
self.current_tool: str            # 当前工具
self.drawing_box: bool            # 框选状态
self.polygon_points: List         # 多边形点集
self.selected_annotation: int     # 选中ID

# 编辑状态
self.dragging_vertex: bool        # 顶点拖拽
self.drag_annotation_id: int      # 拖拽标注ID
self.drag_vertex_index: int       # 拖拽顶点索引
```

### 3.4 COCOExporter 导出器

#### 导出流程

```python
class COCOExporter(BaseExporter):
    """COCO JSON格式导出器"""
    
    def export(self, project: AnnotationProject) -> bool:
        # 1. 构建COCO结构
        coco_data = self.create_coco_structure(project)
        
        # 2. JSON序列化
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, indent=2)
        
        return True
    
    def create_coco_structure(self, project) -> Dict:
        """构建标准COCO结构"""
        return {
            "info": self.create_info(project),
            "licenses": [],
            "categories": self.create_categories(project.classes),
            "images": [...],
            "annotations": [...]
        }
```

#### COCO格式映射

| 项目数据 | COCO字段 | 转换规则 |
|---------|---------|---------|
| `polygon` | `segmentation` | Flatten: [[x1,y1,x2,y2,...]] |
| `bbox` | `bbox` | [x, y, w, h] 直接映射 |
| `class_id` | `category_id` | 直接映射 |
| `get_area()` | `area` | 计算面积 |
| `confidence` | `attributes.confidence` | 扩展字段 |
| `quality_score` | `attributes.quality_score` | 新增扩展 |

---

## 4. 数据流分析

### 4.1 标注创建数据流

```
用户点击
    │
    ▼
┌─────────────┐
│ CanvasWidget│  mousePressEvent()
│ (屏幕坐标)  │  screen_to_image()
└─────────────┘
    │ point_clicked Signal (image_pos)
    ▼
┌─────────────┐
│ MainWindow  │  on_point_clicked()
└─────────────┘
    │ SAM2Engine.set_image() (预处理)
    │ SAM2Engine.predict_from_points()
    ▼
┌─────────────┐
│ SAM2Engine  │  返回 (masks, scores, logits)
└─────────────┘
    │ get_best_mask() → mask
    │ mask_to_polygon() → polygon
    │ mask_to_bbox() → bbox
    ▼
┌─────────────┐
│ Annotation  │  创建数据对象
│ (Dataclass) │  calculate_quality_metrics()
└─────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 同步更新多个组件                       │
│ - canvas.annotations.append()       │
│ - layer_list.annotations.append()   │
│ - canvas.update() (触发重绘)         │
│ - project_manager.add_annotation()  │
└─────────────────────────────────────┘
```

### 4.2 标注确认数据流

```
用户点击"确认标注"
    │
    ▼
┌─────────────┐
│ LayerList   │  confirm_selected()
│ (UI面板)    │  ann.label = text
└─────────────┘
    │ annotation_confirmed Signal
    ▼
┌─────────────┐
│ MainWindow  │  on_annotation_confirmed()
└─────────────┘
    │ canvas.update() → 触发重绘
    │ project_manager.update_annotation()
    ▼
┌─────────────┐
│ Project     │  数据持久化准备
│ Manager     │
└─────────────┘
```

### 4.3 数据导出流程

```
用户点击"保存COCO"
    │
    ▼
┌─────────────┐
│ LayerList   │  save_coco_requested.emit()
└─────────────┘
    │
    ▼
┌─────────────┐
│ MainWindow  │  save_coco_format()
│             │  sync_current_annotations() (同步数据)
└─────────────┘
    │
    ▼
┌─────────────┐
│ COCOExporter│  export(project)
│             │  create_coco_structure()
└─────────────┘
    │ 遍历 project.images
    │ 遍历 img_ann.annotations
    │ create_annotation_info() → COCO格式
    ▼
┌─────────────┐
│ JSON File   │  json.dump() → 保存文件
└─────────────┘
```

### 4.4 Signal/Slot 通信矩阵

| Signal | 发射者 | 接收者 | 数据类型 |
|--------|-------|-------|---------|
| `point_clicked` | CanvasWidget | MainWindow | Tuple[int,int] |
| `box_drawn` | CanvasWidget | MainWindow | Tuple[x,y,w,h] |
| `polygon_drawn` | CanvasWidget | MainWindow | List[[x,y]] |
| `annotation_selected` | CanvasWidget | LayerList | int (ID) |
| `annotation_clicked` | LayerList | MainWindow | int (ID) |
| `annotation_deleted` | LayerList | MainWindow | int (ID) |
| `annotation_confirmed` | LayerList | MainWindow | int (ID) |
| `label_changed` | LayerList | MainWindow | int, str |
| `class_changed` | LayerList | MainWindow | int, str |
| `save_coco_requested` | LayerList | MainWindow | None |
| `image_selected` | ImageList | MainWindow | str (path) |
| `tool_changed` | ToolBar | MainWindow | str |

---

## 5. 配置系统设计

### 5.1 配置层次结构

```yaml
config.yaml
├── model/           # 模型配置
│   ├── path         # SAM2模型路径
│   ├── config_path  # 模型配置文件
│   └── device       # cuda/cpu
├── polygon/         # 多边形配置 (新增)
│   ├── epsilon_factor  # 顶点密度参数
│   └── max_vertices    # 顶点上限
├── quality/         # 质量配置 (新增)
│   ├── enable_metrics  # 启用质量评估
│   └── min_vertex_density  # 最小密度
├── features/        # 功能开关 (新增)
│   ├── high_density_polygon
│   ├── quality_metrics
│   └── class_hierarchy
├── ui/              # 界面配置
│   ├── theme        # 主题
│   └── mask_opacity # Mask透明度
├── classes/         # 类别配置 (扩展)
│   ├── name
│   ├── id
│   ├── color
│   └── supercategory  # 层级
└── export/          # 导出配置
    ├── default_format
    └── output_dir
```

### 5.2 ConfigLoader API

```python
class ConfigLoader:
    """配置加载器 - 统一配置访问"""
    
    def get(self, key: str, default=None) -> Any:
        """嵌套键访问：'polygon.epsilon_factor'"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
        return value
    
    def get_polygon_config(self) -> Dict:
        """获取多边形配置"""
        return {
            'epsilon_factor': self.get('polygon.epsilon_factor', 0.005),
            'max_vertices': self.get('polygon.max_vertices', 100)
        }
    
    def get_quality_config(self) -> Dict:
        """获取质量配置"""
        return {
            'enable_metrics': self.get('quality.enable_metrics', True),
            'min_vertex_density': self.get('quality.min_vertex_density', 5)
        }
    
    def get_classes_with_hierarchy(self) -> List:
        """获取带层级类别"""
        return self.get('classes', [...])
```

### 5.3 默认配置机制

```python
def get_default_config(self) -> Dict:
    """默认配置 - 无配置文件时使用"""
    return {
        "model": {...},
        "polygon": {"epsilon_factor": 0.005, "max_vertices": 100},
        "quality": {"enable_metrics": True, "min_vertex_density": 5},
        "features": {...},
        "classes": [预设12种类别],
        ...
    }
```

---

## 6. 扩展性设计

### 6.1 Exporter 扩展机制

```python
# base_exporter.py - 抽象基类
class BaseExporter:
    """导出器基类"""
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
    
    def export(self, project: AnnotationProject) -> bool:
        raise NotImplementedError
    
    def _sanitize_filename(self, name: str) -> str:
        """通用工具方法"""
        ...

# 扩展新格式示例
class YOLOExporter(BaseExporter):
    """YOLO格式导出器"""
    def export(self, project) -> bool:
        # 实现YOLO格式转换
        for img_ann in project.images:
            for ann in img_ann.annotations:
                # YOLO格式：class_id center_x center_y width height
                ...
```

### 6.2 类别扩展

```yaml
# config.yaml 添加新类别
classes:
  - name: "new_category"
    id: 12
    color: "#custom_color"
    supercategory: "new_group"
```

### 6.3 工具扩展

```python
# CanvasWidget 支持新工具
def set_tool(self, tool: str):
    self.current_tool = tool
    if tool == "new_tool":
        self.drawing_new_shape = True
        ...

def mousePressEvent(self, event):
    if self.current_tool == "new_tool":
        # 处理新工具交互
        ...
```

---

## 7. 性能优化策略

### 7.1 GPU推理优化

| 策略 | 实现 |
|------|------|
| **批量推理** | 多点/多框合并调用 |
| **模型缓存** | 单次load_model，复用predictor |
| **内存释放** | `torch.cuda.empty_cache()` |
| **CPU Fallback** | 自动设备切换 |

### 7.2 渲染优化

| 策略 | 实现 |
|------|------|
| **按需重绘** | 只在变化时调用update() |
| **顶点限制** | max_vertices=100防止过载 |
| **缩放优化** | SmoothTransformation抗锯齿 |
| **异常捕获** | paintEvent try-except防崩溃 |

### 7.3 数据结构优化

| 策略 | 实现 |
|------|------|
| **Mask不序列化** | 只保留polygon，节省存储 |
| **引用传递** | canvas和layer_list共享同一annotations |
| **延迟计算** | 质量指标按需调用calculate |

---

## 8. 测试架构

### 8.1 测试分层

```
tests/
├── test_canvas_widget.py    # UI组件测试
│   ├── TestCanvasWidget     # 画布测试类
│   │   ├── test_draw_*      # 绘制测试
│   │   ├── test_empty_*     # 边界测试
│   │   └── test_special_*   # 特殊场景
│   └── TestAnnotationData   # 数据测试类
│
├── test_quality_metrics.py  # 质量指标测试
│   ├── TestQualityMetrics   # 质量计算测试
│   │   ├── test_basic       # 基础计算
│   │   ├── test_edge_cases  # 边界条件
│   │   ├── test_formula     # 公式验证
│   └── TestConfigLoaderQuality  # 配置测试
│
└── test_imports.py          # 导入验证测试
```

### 8.2 测试覆盖范围

| 测试类型 | 覆盖内容 |
|---------|---------|
| **功能测试** | 标注创建、绘制、导出 |
| **边界测试** | 空polygon、单点、特殊字符 |
| **兼容测试** | 旧数据加载、向后兼容 |
| **配置测试** | 配置读取、默认值 |
| **单元测试** | 各类方法独立测试 |

### 8.3 pytest配置

```bash
# 运行全部测试
pytest tests/ -v

# 运行覆盖率
pytest tests/ --cov=src --cov-report=html

# 运行特定测试
pytest tests/test_quality_metrics.py -v -k "test_perimeter"
```

---

## 9. 部署方案

### 9.1 本地部署

```bash
# 1. 环境准备
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置模型路径
# 编辑 config.yaml 中 model.path

# 4. 启动应用
python main.py
```

### 9.2 依赖清单

```
requirements.txt
├── PyQt6>=6.0.0        # GUI框架
├── torch>=2.0.0        # 深度学习
├── sam2>=0.4.0         # 分割模型
├── opencv-python>=4.8.0  # 图像处理
├── pillow>=10.0.0      # 图像IO
├── numpy>=1.24.0       # 数值计算
├── pyyaml>=6.0         # 配置解析
├── pytest>=9.0         # 测试框架
```

### 9.3 硬件要求

| 配置 | 最低 | 推荐 |
|------|------|------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| GPU | 无 | NVIDIA 8GB+ |
| 存储 | 2GB | 10GB+ |

---

## 10. 开发指南

### 10.1 代码规范

| 规范 | 说明 |
|------|------|
| **文件命名** | snake_case.py |
| **类命名** | PascalCase |
| **方法命名** | snake_case |
| **变量命名** | snake_case |
| **Signal命名** | snake_case (pyqtSignal) |
| **文档字符串** | 三引号中文描述 |

### 10.2 模块依赖规则

```
允许依赖方向：
Presentation → Business → Engine → Data

禁止依赖：
Data ← Engine ← Business ← Presentation
（下层不依赖上层）
```

### 10.3 新功能开发流程

```
1. 定义数据模型 (annotation_data.py)
2. 实现核心逻辑 (对应Manager或Engine)
3. 添加UI组件 (gui/)
4. 连接Signal/Slot (main_window.py)
5. 编写单元测试 (tests/)
6. 更新配置 (config.yaml)
7. 更新文档
```

---

## 11. 技术决策记录

### 11.1 为什么选择PyQt6？

| 因素 | PyQt6优势 |
|------|----------|
| **跨平台** | Windows/Mac/Linux统一体验 |
| **Signal/Slot** | 解耦UI与业务，事件驱动清晰 |
| **丰富控件** | QMainWindow/QWidget/QListWidget等现成可用 |
| **自定义绘制** | QPainter支持复杂渲染 |
| **生态成熟** | 文档完善、社区活跃 |

### 11.2 为什么选择SAM2？

| 因素 | SAM2优势 |
|------|----------|
| **零样本能力** | 无需预训练即可分割任意物体 |
| **点交互** | 单点触发，用户体验极佳 |
| **高精度** | 边界贴合度远超传统方法 |
| **多模态** | 支持点/框/文本多种提示 |
| **官方支持** | Meta维护，持续迭代 |

### 11.3 为什么选择dataclass？

| 因素 | dataclass优势 |
|------|---------------|
| **简洁** | 自动生成__init__、__repr__ |
| **类型安全** | 类型注解支持IDE检查 |
| **默认值** | field(default_factory)灵活配置 |
| **序列化** | asdict/to_dict简单转换 |
| **可读性** | 代码自解释，减少样板代码 |

---

## 12. 技术风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| GPU内存不足 | 推理失败 | CPU Fallback、内存释放 |
| SAM2模型加载失败 | 功能不可用 | from_pretrained备用、错误提示 |
| paintEvent异常 | 应用崩溃 | try-except捕获、错误绘制 |
| 旧数据兼容 | 加载失败 | 默认值填充、版本检测 |
| 顶点过多 | 性能下降 | max_vertices限制 |

---

## 附录

### A. 关键文件索引

| 文件 | 职责 |
|------|------|
| `main.py` | 应用入口 |
| `src/gui/main_window.py` | 主窗口逻辑 |
| `src/gui/canvas_widget.py` | 画布交互 |
| `src/gui/layer_list.py` | 标注面板 |
| `src/core/sam2_engine.py` | SAM2引擎 |
| `src/core/annotation_data.py` | 数据模型 |
| `src/core/project_manager.py` | 项目管理 |
| `src/exporters/coco_exporter.py` | COCO导出 |
| `src/utils/config_loader.py` | 配置加载 |
| `config.yaml` | 配置文件 |

### B. API速查表

```python
# SAM2Engine
engine.load_model()                        # 加载模型
engine.set_image(image)                    # 设置图像
engine.predict_from_points([[x,y]])        # 点分割
engine.predict_from_box([x1,y1,x2,y2])     # 框分割
engine.mask_to_polygon(mask, epsilon=0.005) # 转Polygon

# Annotation
ann.calculate_quality_metrics(config)     # 计算质量
ann.to_dict()                              # 序列化
ann.from_dict(data)                        # 反序列化
ann.get_area()                             # 计算面积

# ConfigLoader
config.get('polygon.epsilon_factor', 0.005)  # 获取配置
config.get_polygon_config()                 # 多边形配置
config.get_quality_config()                 # 质量配置
```

---

**文档版本**：v1.0.0  
**更新日期**：2026年4月22日  
**编写人**：技术架构团队