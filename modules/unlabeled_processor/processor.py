"""无标注文件处理器核心逻辑"""
import os
import shutil
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from pathlib import Path


class UnlabeledProcessor:
    """处理无标注信息的图片与标签文件"""
    
    def __init__(self, main_folder: str):
        self.main_folder = main_folder
        self.images_folder = os.path.join(main_folder, "images")
        self.labels_folder = os.path.join(main_folder, "labels")
        self.unlabeled_folder = os.path.join(main_folder, "unlabeled_files")
        
        self.empty_labels: List[str] = []
        self.matched_images: List[str] = []
        self.processed_count = 0
        self.failed_count = 0
        self.logs: List[str] = []
        
        self._cancelled = False
    
    def validate_folders(self) -> Tuple[bool, str]:
        """验证文件夹结构"""
        if not os.path.exists(self.main_folder):
            return False, f"主文件夹不存在: {self.main_folder}"
        
        if not os.path.exists(self.images_folder):
            return False, f"images文件夹不存在: {self.images_folder}"
        
        if not os.path.exists(self.labels_folder):
            return False, f"labels文件夹不存在: {self.labels_folder}"
        
        return True, ""
    
    def find_empty_labels(self) -> List[str]:
        """查找所有空标签文件"""
        empty_labels = []
        
        if not os.path.exists(self.labels_folder):
            return empty_labels
        
        for filename in os.listdir(self.labels_folder):
            if filename.lower().endswith('.txt'):
                filepath = os.path.join(self.labels_folder, filename)
                if os.path.isfile(filepath) and os.path.getsize(filepath) == 0:
                    empty_labels.append(filename)
        
        self.empty_labels = empty_labels
        return empty_labels
    
    def find_matched_images(self, label_filename: str) -> Optional[str]:
        """找到与标签文件对应的图片"""
        base_name = os.path.splitext(label_filename)[0]
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        
        for ext in image_extensions:
            image_path = os.path.join(self.images_folder, base_name + ext)
            if os.path.exists(image_path):
                return image_path
        
        return None
    
    def get_all_matched_pairs(self) -> List[Tuple[str, str]]:
        """获取所有空标签及其对应图片的配对"""
        pairs = []
        for label_file in self.empty_labels:
            image_path = self.find_matched_images(label_file)
            if image_path:
                pairs.append((label_file, image_path))
            else:
                self.logs.append(f"警告: 未找到标签 {label_file} 对应的图片")
        
        return pairs
    
    def process_move(self) -> Tuple[int, int, List[str]]:
        """移动模式：将空标签和对应图片移动到unlabeled_files目录"""
        os.makedirs(self.unlabeled_folder, exist_ok=True)
        images_dest = os.path.join(self.unlabeled_folder, "images")
        labels_dest = os.path.join(self.unlabeled_folder, "labels")
        os.makedirs(images_dest, exist_ok=True)
        os.makedirs(labels_dest, exist_ok=True)
        
        processed = 0
        failed = 0
        logs = []
        
        for label_file in self.empty_labels:
            if self._cancelled:
                logs.append("操作已取消")
                break
            
            label_path = os.path.join(self.labels_folder, label_file)
            image_path = self.find_matched_images(label_file)
            
            try:
                dest_label = os.path.join(labels_dest, label_file)
                shutil.move(label_path, dest_label)
                logs.append(f"移动标签: {label_file}")
                
                if image_path:
                    dest_image = os.path.join(images_dest, os.path.basename(image_path))
                    shutil.move(image_path, dest_image)
                    logs.append(f"移动图片: {os.path.basename(image_path)}")
                
                processed += 1
            except Exception as e:
                logs.append(f"移动失败 {label_file}: {str(e)}")
                failed += 1
        
        return processed, failed, logs
    
    def process_delete(self) -> Tuple[int, int, List[str]]:
        """删除模式：直接删除空标签和对应图片"""
        processed = 0
        failed = 0
        logs = []
        
        for label_file in self.empty_labels:
            if self._cancelled:
                logs.append("操作已取消")
                break
            
            label_path = os.path.join(self.labels_folder, label_file)
            image_path = self.find_matched_images(label_file)
            
            try:
                os.remove(label_path)
                logs.append(f"删除标签: {label_file}")
                
                if image_path:
                    os.remove(image_path)
                    logs.append(f"删除图片: {os.path.basename(image_path)}")
                
                processed += 1
            except Exception as e:
                logs.append(f"删除失败 {label_file}: {str(e)}")
                failed += 1
        
        return processed, failed, logs
    
    def cancel(self):
        """取消操作"""
        self._cancelled = True
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled
    
    def generate_report(self, processed: int, failed: int) -> str:
        """生成处理报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = [
            f"处理时间: {timestamp}",
            f"主文件夹: {self.main_folder}",
            f"空标签文件数量: {len(self.empty_labels)}",
            f"成功处理: {processed}",
            f"处理失败: {failed}",
            "=" * 50,
            "操作日志:"
        ]
        report.extend(self.logs)
        return "\n".join(report)
    
    def save_report(self, report: str, filename: str = None):
        """保存处理报告到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unlabeled_report_{timestamp}.txt"
        
        report_path = os.path.join(self.main_folder, filename)
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            return True, report_path
        except Exception as e:
            return False, str(e)
