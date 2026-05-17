"""File Renamer Core Logic"""
import os
import re
from typing import List, Tuple, Dict
from core.natural_sort import natural_sort_key
from core.file_operator import FileOperator


class FileRenamer:
    """File renamer"""
    
    def __init__(self, folder_path: str, config: 'RenamerConfig'):
        self.folder_path = folder_path
        self.config = config
        self.current_files: List[str] = []
        self.preview_new_names: List[str] = []
    
    def load_files(self) -> List[str]:
        """Load file list"""
        if self.config.file_type == "txt":
            extensions = ['.txt']
        else:
            extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        
        files = FileOperator.get_files_by_extension(self.folder_path, extensions)
        self.current_files = sorted(files, key=lambda f: natural_sort_key(os.path.basename(f)))
        return self.current_files
    
    def generate_preview(self) -> List[Tuple[str, str]]:
        """Generate rename preview
        
        Returns:
            List of tuples: (old_filename, new_filename)
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
        """Execute rename operation
        
        Returns:
            (success_list, failed_list)
            Each element is (old_filename, new_filename) or (old_filename, new_filename, error_message)
        """
        success = []
        failed = []
        log_lines = []
        
        for old, new in zip(self.current_files, self.preview_new_names):
            old_path = os.path.join(self.folder_path, old)
            new_path = os.path.join(self.folder_path, new)
            
            if os.path.exists(new_path) and new_path != old_path:
                msg = "Destination file exists, skipping"
                failed.append((old, new, msg))
                log_lines.append(f"✗ {old} -> {new}  [Failed: {msg}]")
                continue
            
            try:
                os.rename(old_path, new_path)
                success.append((old, new))
                log_lines.append(f"✓ {old} -> {new}")
            except Exception as e:
                failed.append((old, new, str(e)))
                log_lines.append(f"✗ {old} -> {new}  [Error: {e}]")
        
        if log_lines:
            log_file = os.path.join(self.folder_path, 'rename_log.txt')
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("File rename log\n")
                f.write("=" * 60 + "\n")
                f.write("\n".join(log_lines))
        
        self.current_files = []
        self.preview_new_names = []
        
        return success, failed
    
    def get_file_count(self) -> int:
        return len(self.current_files)