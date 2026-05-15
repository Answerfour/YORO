"""文件重命名核心逻辑"""
import os
import re
from typing import List, Tuple, Dict
from core.natural_sort import natural_sort_key
from core.file_operator import FileOperator


class FileRenamer:
    """文件重命名器"""
    
    def __init__(self, folder_path: str, config: 'RenamerConfig'):
        self.folder_path = folder_path
        self.config = config
        self.current_files: List[str] = []
        self.preview_new_names: List[str] = []
    
    def load_files(self) -> List[str]:
        """加载文件列表"""
        if self.config.file_type == "txt":
            extensions = ['.txt']
        else:
            extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        
        files = FileOperator.get_files_by_extension(self.folder_path, extensions)
        self.current_files = sorted(files, key=lambda f: natural_sort_key(os.path.basename(f)))
        return self.current_files
    
    def generate_preview(self) -> List[Tuple[str, str]]:
        """生成重命名预览
        
        Returns:
            列表元素为 (原文件名, 新文件名)
        """
        self.preview_new_names = []
        preview_list = []
        
        start = self.config.start_number
        width = self.config.digit_width
        
        for idx, file_path in enumerate(self.current_files, start=start):
            old_name = os.path.basename(file_path)
            _, ext = os.path.splitext(old_name)
            new_name = f"{str(idx).zfill(width)}{ext.lower()}"
            self.preview_new_names.append(new_name)
            preview_list.append((old_name, new_name))
        
        return preview_list
    
    def execute_rename(self) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str, str]]]:
        """执行重命名操作
        
        Returns:
            (成功列表, 失败列表)
            每个元素为 (原文件名, 新文件名) 或 (原文件名, 新文件名, 错误信息)
        """
        success = []
        failed = []
        log_lines = []
        
        for old, new in zip(self.current_files, self.preview_new_names):
            old_path = os.path.join(self.folder_path, old)
            new_path = os.path.join(self.folder_path, new)
            
            if os.path.exists(new_path) and new_path != old_path:
                msg = "目标文件已存在，跳过"
                failed.append((old, new, msg))
                log_lines.append(f"✗ {old} -> {new}  [失败：{msg}]")
                continue
            
            try:
                os.rename(old_path, new_path)
                success.append((old, new))
                log_lines.append(f"✓ {old} -> {new}")
            except Exception as e:
                failed.append((old, new, str(e)))
                log_lines.append(f"✗ {old} -> {new}  [错误：{e}]")
        
        if log_lines:
            log_file = os.path.join(self.folder_path, 'rename_log.txt')
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("文件重命名记录\n")
                f.write("=" * 60 + "\n")
                f.write("\n".join(log_lines))
        
        self.current_files = []
        self.preview_new_names = []
        
        return success, failed
    
    def get_file_count(self) -> int:
        return len(self.current_files)
