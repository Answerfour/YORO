"""孤立文件清理核心逻辑"""
import os
import shutil
from typing import List, Set, Tuple, Dict
from core.file_operator import FileOperator
from datetime import datetime


class OrphanCleaner:
    """孤立文件清理器"""
    
    def __init__(self, folder1_path: str, folder2_path: str, pairing_mode: str = "name"):
        self.folder1_path = folder1_path
        self.folder2_path = folder2_path
        self.pairing_mode = pairing_mode
        self.folder1_files: List[Tuple[str, str, str]] = []
        self.folder2_files: List[Tuple[str, str, str]] = []
    
    def load_files(self):
        """加载两个文件夹的文件"""
        self.folder1_files = FileOperator.get_image_files(self.folder1_path)
        self.folder2_files = FileOperator.get_txt_files(self.folder2_path)
    
    def analyze(self) -> Dict:
        """分析文件配对情况
        
        Returns:
            包含配对和孤立文件信息的字典
        """
        folder1_names = set([f[1] for f in self.folder1_files])
        folder2_names = set([f[1] for f in self.folder2_files])
        
        if self.pairing_mode == "name":
            paired = folder1_names & folder2_names
            orphan1 = folder1_names - folder2_names
            orphan2 = folder2_names - folder1_names
        else:
            min_len = min(len(self.folder1_files), len(self.folder2_files))
            paired = set([f"Pair_{i + 1}" for i in range(min_len)])
            orphan1 = set([f"Orphan_{i + 1}" for i in range(len(self.folder1_files) - min_len)])
            orphan2 = set([f"Orphan_{i + 1}" for i in range(len(self.folder2_files) - min_len)])
        
        return {
            'paired_count': len(paired),
            'orphan1_count': len(orphan1),
            'orphan2_count': len(orphan2),
            'paired': paired,
            'orphan1': orphan1,
            'orphan2': orphan2,
            'folder1_names': folder1_names,
            'folder2_names': folder2_names
        }
    
    def delete_orphans(self, orphan1: Set[str], orphan2: Set[str]) -> Tuple[int, List[str]]:
        """删除孤立文件
        
        Args:
            orphan1: 孤立图片名称集合
            orphan2: 孤立TXT名称集合
        
        Returns:
            (删除数量, 日志消息列表)
        """
        deleted_count = 0
        logs = []
        
        for name in orphan1:
            for file_path, file_name, ext in self.folder1_files:
                if file_name == name:
                    try:
                        os.remove(file_path)
                        logs.append(f"已删除图片: {file_name}{ext}")
                        deleted_count += 1
                    except Exception as e:
                        logs.append(f"删除失败 {file_name}: {e}")
                    break
        
        for name in orphan2:
            for file_path, file_name, ext in self.folder2_files:
                if file_name == name:
                    try:
                        os.remove(file_path)
                        logs.append(f"已删除TXT: {file_name}{ext}")
                        deleted_count += 1
                    except Exception as e:
                        logs.append(f"删除失败 {file_name}: {e}")
                    break
        
        return deleted_count, logs
    
    def move_orphans(self, orphan1: Set[str], orphan2: Set[str], backup_folder: str) -> Tuple[int, List[str]]:
        """移动孤立文件到备份文件夹
        
        Args:
            orphan1: 孤立图片名称集合
            orphan2: 孤立TXT名称集合
            backup_folder: 备份目标文件夹
        
        Returns:
            (移动数量, 日志消息列表)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_folder, f"orphans_backup_{timestamp}")
        os.makedirs(backup_path, exist_ok=True)
        
        moved_count = 0
        logs = [f"备份目录: {backup_path}"]
        
        for name in orphan1:
            for file_path, file_name, ext in self.folder1_files:
                if file_name == name:
                    try:
                        dest_path = os.path.join(backup_path, f"{file_name}{ext}")
                        shutil.move(file_path, dest_path)
                        logs.append(f"已移动图片: {file_name}{ext}")
                        moved_count += 1
                    except Exception as e:
                        logs.append(f"移动失败 {file_name}: {e}")
                    break
        
        for name in orphan2:
            for file_path, file_name, ext in self.folder2_files:
                if file_name == name:
                    try:
                        dest_path = os.path.join(backup_path, f"{file_name}{ext}")
                        shutil.move(file_path, dest_path)
                        logs.append(f"已移动TXT: {file_name}{ext}")
                        moved_count += 1
                    except Exception as e:
                        logs.append(f"移动失败 {file_name}: {e}")
                    break
        
        return moved_count, logs
