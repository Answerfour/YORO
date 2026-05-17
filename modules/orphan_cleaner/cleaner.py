"""Orphan File Cleaner Core Logic"""
import os
import shutil
from typing import List, Set, Tuple, Dict
from core.file_operator import FileOperator
from datetime import datetime


class OrphanCleaner:
    """Orphan file cleaner"""
    
    def __init__(self, folder1_path: str, folder2_path: str, pairing_mode: str = "name"):
        self.folder1_path = folder1_path
        self.folder2_path = folder2_path
        self.pairing_mode = pairing_mode
        self.folder1_files: List[Tuple[str, str, str]] = []
        self.folder2_files: List[Tuple[str, str, str]] = []
    
    def load_files(self):
        """Load files from both folders"""
        self.folder1_files = FileOperator.get_image_files(self.folder1_path)
        self.folder2_files = FileOperator.get_txt_files(self.folder2_path)
    
    def analyze(self) -> Dict:
        """Analyze file pairing status
        
        Returns:
            Dictionary containing paired and orphan file information
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
        """Delete orphan files
        
        Args:
            orphan1: Set of orphan image names
            orphan2: Set of orphan TXT names
        
        Returns:
            (deleted_count, log_messages)
        """
        deleted_count = 0
        logs = []
        
        for name in orphan1:
            for file_path, file_name, ext in self.folder1_files:
                if file_name == name:
                    try:
                        os.remove(file_path)
                        logs.append(f"Deleted image: {file_name}{ext}")
                        deleted_count += 1
                    except Exception as e:
                        logs.append(f"Failed to delete {file_name}: {e}")
                    break
        
        for name in orphan2:
            for file_path, file_name, ext in self.folder2_files:
                if file_name == name:
                    try:
                        os.remove(file_path)
                        logs.append(f"Deleted TXT: {file_name}{ext}")
                        deleted_count += 1
                    except Exception as e:
                        logs.append(f"Failed to delete {file_name}: {e}")
                    break
        
        return deleted_count, logs
    
    def move_orphans(self, orphan1: Set[str], orphan2: Set[str], backup_folder: str) -> Tuple[int, List[str]]:
        """Move orphan files to backup folder
        
        Args:
            orphan1: Set of orphan image names
            orphan2: Set of orphan TXT names
            backup_folder: Backup destination folder
        
        Returns:
            (moved_count, log_messages)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_folder, f"orphans_backup_{timestamp}")
        os.makedirs(backup_path, exist_ok=True)
        
        moved_count = 0
        logs = [f"Backup directory: {backup_path}"]
        
        for name in orphan1:
            for file_path, file_name, ext in self.folder1_files:
                if file_name == name:
                    try:
                        dest_path = os.path.join(backup_path, f"{file_name}{ext}")
                        shutil.move(file_path, dest_path)
                        logs.append(f"Moved image: {file_name}{ext}")
                        moved_count += 1
                    except Exception as e:
                        logs.append(f"Failed to move {file_name}: {e}")
                    break
        
        for name in orphan2:
            for file_path, file_name, ext in self.folder2_files:
                if file_name == name:
                    try:
                        dest_path = os.path.join(backup_path, f"{file_name}{ext}")
                        shutil.move(file_path, dest_path)
                        logs.append(f"Moved TXT: {file_name}{ext}")
                        moved_count += 1
                    except Exception as e:
                        logs.append(f"Failed to move {file_name}: {e}")
                    break
        
        return moved_count, logs