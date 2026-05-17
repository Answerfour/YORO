"""File Operation Utilities - Provide common file operation functions"""
import os
import glob
import shutil
from typing import List, Tuple, Optional
from pathlib import Path


class FileOperator:
    """Common file operations class"""
    
    @staticmethod
    def get_files_by_extension(folder_path: str, extensions: List[str], recursive: bool = False) -> List[str]:
        """Get list of files with specified extensions
        
        Args:
            folder_path: Folder path
            extensions: List of extensions, e.g. ['.txt', '.jpg']
            recursive: Whether to search subfolders recursively
        
        Returns:
            List of file paths
        """
        files = []
        extensions_lower = [ext.lower() if ext.startswith('.') else f".{ext.lower()}" for ext in extensions]
        
        if recursive:
            for root, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    ext = Path(filename).suffix.lower()
                    if ext in extensions_lower:
                        files.append(os.path.join(root, filename))
        else:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    ext = Path(filename).suffix.lower()
                    if ext in extensions_lower:
                        files.append(file_path)
        
        return files
    
    @staticmethod
    def get_image_files(folder_path: str, recursive: bool = False) -> List[Tuple[str, str, str]]:
        """Get all image files
        
        Returns:
            List of tuples: (full_path, filename_without_extension, extension)
        """
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
        files = FileOperator.get_files_by_extension(folder_path, image_extensions, recursive)
        
        result = []
        for file_path in files:
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            result.append((file_path, name, ext.lower()))
        
        return result
    
    @staticmethod
    def get_txt_files(folder_path: str, recursive: bool = False) -> List[Tuple[str, str, str]]:
        """Get all TXT files
        
        Returns:
            List of tuples: (full_path, filename_without_extension, extension)
        """
        txt_extensions = ['.txt']
        files = FileOperator.get_files_by_extension(folder_path, txt_extensions, recursive)
        
        result = []
        for file_path in files:
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            result.append((file_path, name, ext.lower()))
        
        return result
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """Ensure directory exists, create if it doesn't"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def safe_delete_file(file_path: str) -> Tuple[bool, str]:
        """Safely delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True, ""
            return False, "File does not exist"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def safe_move_file(src: str, dst: str, overwrite: bool = False) -> Tuple[bool, str]:
        """Safely move a file"""
        try:
            if not overwrite and os.path.exists(dst):
                return False, "Destination file already exists"
            
            FileOperator.ensure_directory(os.path.dirname(dst))
            shutil.move(src, dst)
            return True, ""
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def safe_copy_file(src: str, dst: str, overwrite: bool = False) -> Tuple[bool, str]:
        """Safely copy a file"""
        try:
            if not overwrite and os.path.exists(dst):
                return False, "Destination file already exists"
            
            FileOperator.ensure_directory(os.path.dirname(dst))
            shutil.copy2(src, dst)
            return True, ""
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    @staticmethod
    def test_directory_writable(path: str) -> Tuple[bool, str]:
        """Test if directory is writable"""
        try:
            test_file = os.path.join(path, "_write_test.tmp")
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True, ""
        except Exception as e:
            return False, str(e)