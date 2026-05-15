"""YOLO标注统计核心逻辑"""
import os
import glob
from typing import Dict, List, Tuple
from config.schema import ClassMappingConfig


class YOLOCounter:
    """YOLO标注统计器"""
    
    def __init__(self, config: ClassMappingConfig):
        self.config = config
        self.counts: Dict[int, int] = {}
        self.warnings: List[str] = []
    
    def count_in_folder(self, folder_path: str) -> Tuple[Dict[int, int], List[str]]:
        """统计文件夹内所有txt文件中各类别的出现次数
        
        Args:
            folder_path: 文件夹路径
        
        Returns:
            (类别计数字典, 警告信息列表)
        """
        self.counts = {cls_id: 0 for cls_id in self.config.mapping.keys()}
        self.warnings = []
        
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        if not txt_files:
            self.warnings.append("当前文件夹下没有找到 txt 文件")
            return self.counts, self.warnings
        
        for file in txt_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split()
                        if len(parts) >= 1:
                            try:
                                cls = int(float(parts[0]))
                                if cls in self.counts:
                                    self.counts[cls] += 1
                                else:
                                    self.warnings.append(
                                        f"{os.path.basename(file)} 第{line_num}行 包含未知类别 {cls}"
                                    )
                            except ValueError:
                                self.warnings.append(
                                    f"{os.path.basename(file)} 第{line_num}行 格式错误: {line}"
                                )
            except Exception as e:
                self.warnings.append(f"读取文件 {os.path.basename(file)} 失败: {e}")
        
        return self.counts, self.warnings
    
    def get_total(self) -> int:
        """获取总目标数量"""
        return sum(self.counts.values())
    
    def get_results_list(self) -> List[Tuple[int, str, int]]:
        """获取结果列表
        
        Returns:
            列表元素为 (类别ID, 类别名称, 数量)
        """
        results = []
        for cls_id in sorted(self.counts.keys()):
            name = self.config.mapping.get(cls_id, f"未知类别({cls_id})")
            num = self.counts[cls_id]
            results.append((cls_id, name, num))
        return results
