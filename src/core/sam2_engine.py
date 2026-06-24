"""SAM2 Inference Engine for Image Segmentation"""

import os
import numpy as np
import torch
from typing import List, Tuple, Optional
from pathlib import Path
import cv2


class SAM2Engine:
    """SAM2模型推理引擎封装"""

    def __init__(self, model_path: str, config_path: Optional[str] = None, device: str = "cuda"):
        self.model_path = model_path
        self.config_path = config_path
        self.device = device if torch.cuda.is_available() else "cpu"
        self.predictor = None
        self.current_image = None
        self.is_loaded = False

    def load_model(self) -> bool:
        """加载SAM2模型"""
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor

            # Get config file path
            model_dir = Path(self.model_path).parent

            # Find config file (sam2_hiera_t.yaml or similar)
            if self.config_path and os.path.exists(self.config_path):
                config_file = self.config_path
            else:
                # Look for yaml config in model directory
                yaml_files = list(model_dir.glob("*.yaml"))
                if yaml_files:
                    config_file = str(yaml_files[0])
                else:
                    # Use default config for sam2-hiera-tiny
                    config_file = "configs/sam2/sam2_hiera_t.yaml"
                    # Try to find in sam2 package
                    try:
                        import sam2
                        sam2_dir = Path(sam2.__file__).parent
                        config_file = str(sam2_dir / "configs" / "sam2" / "sam2_hiera_t.yaml")
                    except:
                        pass

            print(f"Loading SAM2 model...")
            print(f"Config: {config_file}")
            print(f"Checkpoint: {self.model_path}")
            print(f"Device: {self.device}")

            # Build SAM2 model
            sam2_model = build_sam2(
                config_file,
                self.model_path,
                device=self.device
            )

            # Create predictor
            self.predictor = SAM2ImagePredictor(sam2_model)
            self.is_loaded = True
            print("SAM2 model loaded successfully!")
            return True

        except Exception as e:
            print(f"Failed to load SAM2 model: {e}")

            # Fallback: try loading from pretrained
            try:
                from sam2.sam2_image_predictor import SAM2ImagePredictor

                print("Trying to load from pretrained checkpoint...")
                self.predictor = SAM2ImagePredictor.from_pretrained("sam2-hiera-tiny")
                self.device = "cpu"  # from_pretrained usually loads to cpu
                self.is_loaded = True
                print("SAM2 model loaded from pretrained!")
                return True
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                self.is_loaded = False
                return False

    def set_image(self, image: np.ndarray) -> bool:
        """设置当前要处理的图像"""
        if not self.is_loaded:
            print("Model not loaded")
            return False

        try:
            self.current_image = image.copy()
            self.predictor.set_image(image)
            return True

        except Exception as e:
            print(f"Failed to set image: {e}")
            return False

    def predict_from_points(self, points: List[List[int]], labels: Optional[List[int]] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """基于点点击的分割预测"""
        if not self.is_loaded or self.current_image is None:
            return None, None, None

        if labels is None:
            labels = [1] * len(points)

        try:
            point_coords = np.array(points)
            point_labels = np.array(labels)

            masks, scores, logits = self.predictor.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                multimask_output=True
            )

            return masks, scores, logits

        except Exception as e:
            print(f"Point prediction failed: {e}")
            return None, None, None

    def predict_from_box(self, box: List[int]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """基于边界框的分割预测"""
        if not self.is_loaded or self.current_image is None:
            return None, None, None

        try:
            box_array = np.array(box)

            masks, scores, logits = self.predictor.predict(
                box=box_array,
                multimask_output=True
            )

            return masks, scores, logits

        except Exception as e:
            print(f"Box prediction failed: {e}")
            return None, None, None

    def get_best_mask(self, masks: np.ndarray, scores: np.ndarray) -> np.ndarray:
        """根据分数选择最佳掩码"""
        if masks is None or scores is None:
            return None

        best_idx = np.argmax(scores)
        return masks[best_idx]

    def mask_to_polygon(self, mask: np.ndarray, epsilon_factor: float = 0.005) -> List[List[int]]:
        """将掩码转换为多边形坐标

        Args:
            mask: 二值掩码
            epsilon_factor: 多边形近似因子，越小顶点越多
                            0.01 → 约13顶点（低密度）
                            0.005 → 约25-50顶点（中密度，推荐）
                            0.002 → 约50-100顶点（高密度）

        Returns:
            多边形顶点列表 [[x,y], [x,y], ...]
        """
        if mask is None:
            print("[DEBUG mask_to_polygon] mask is None")
            return []

        print(f"[DEBUG mask_to_polygon] mask shape: {mask.shape}, dtype: {mask.dtype}")
        print(f"[DEBUG mask_to_polygon] mask min: {mask.min()}, max: {mask.max()}, mean: {mask.mean()}")

        binary_mask = (mask > 0.5).astype(np.uint8)
        print(f"[DEBUG mask_to_polygon] binary_mask nonzero count: {np.count_nonzero(binary_mask)}")

        contours, _ = cv2.findContours(
            binary_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        print(f"[DEBUG mask_to_polygon] contours found: {len(contours)}")

        if not contours:
            return []

        largest_contour = max(contours, key=cv2.contourArea)
        print(f"[DEBUG mask_to_polygon] largest contour area: {cv2.contourArea(largest_contour)}")

        # 使用可配置的epsilon值
        epsilon = epsilon_factor * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        # 顶点数量限制，防止性能问题
        max_vertices = 100
        if len(approx) > max_vertices:
            # 逐步增加epsilon直到顶点数满足要求
            adjusted_epsilon = epsilon_factor
            while len(approx) > max_vertices and adjusted_epsilon < 0.02:
                adjusted_epsilon *= 1.5
                epsilon = adjusted_epsilon * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        polygon = [[int(p[0][0]), int(p[0][1])] for p in approx]

        print(f"[DEBUG mask_to_polygon] final polygon points: {len(polygon)}")

        return polygon

    def mask_to_bbox(self, mask: np.ndarray) -> List[int]:
        """从掩码提取边界框"""
        if mask is None:
            return [0, 0, 0, 0]

        binary_mask = (mask > 0.5).astype(np.uint8)
        coords = np.where(binary_mask > 0)

        if len(coords[0]) == 0:
            return [0, 0, 0, 0]

        y_min, y_max = coords[0].min(), coords[0].max()
        x_min, x_max = coords[1].min(), coords[1].max()

        return [int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)]

    def release(self):
        """释放资源"""
        self.current_image = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()