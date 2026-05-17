"""YOLO Annotation Statistics Core Logic"""
import os
import glob
from typing import Dict, List, Tuple
from config.schema import ClassMappingConfig


class YOLOCounter:
    """YOLO annotation counter"""
    
    def __init__(self, config: ClassMappingConfig):
        self.config = config
        self.counts: Dict[int, int] = {}
        self.warnings: List[str] = []
    
    def count_in_folder(self, folder_path: str) -> Tuple[Dict[int, int], List[str]]:
        """Count occurrences of each class in all txt files within a folder
        
        Args:
            folder_path: Path to the folder
        
        Returns:
            (class_count_dict, warning_messages)
        """
        self.counts = {cls_id: 0 for cls_id in self.config.mapping.keys()}
        self.warnings = []
        
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        if not txt_files:
            self.warnings.append("No txt files found in the current folder")
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
                                        f"{os.path.basename(file)} line {line_num} contains unknown class {cls}"
                                    )
                            except ValueError:
                                self.warnings.append(
                                    f"{os.path.basename(file)} line {line_num} format error: {line}"
                                )
            except Exception as e:
                self.warnings.append(f"Failed to read file {os.path.basename(file)}: {e}")
        
        return self.counts, self.warnings
    
    def get_total(self) -> int:
        """Get total object count"""
        return sum(self.counts.values())
    
    def get_results_list(self) -> List[Tuple[int, str, int]]:
        """Get results list
        
        Returns:
            List elements are (class_id, class_name, count)
        """
        results = []
        for cls_id in sorted(self.counts.keys()):
            name = self.config.mapping.get(cls_id, f"unknown_class({cls_id})")
            num = self.counts[cls_id]
            results.append((cls_id, name, num))
        return results