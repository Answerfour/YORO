"""文件操作工具 - 提供通用文件操作功能"""
import os
import glob
import shutil
from typing import List, Tuple, Optional
from pathlib import Path


class FileOperator:
    """通用文件操作类"""
    
    @staticmethod
    def get_files_by_extension(folder_path: str, extensions: List[str], recursive: bool = False) -> List[str]:
        """获取指定扩展名的文件列表
        
        Args:
            folder_path: 文件夹路径
            extensions: 扩展名列表，如 ['.txt', '.jpg']
            recursive: 是否递归搜索子文件夹
        
        Returns:
            文件路径列表
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
        """获取所有图片文件
        
        Returns:
            列表元素为 (完整路径, 文件名不含扩展名, 扩展名)
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
        """获取所有TXT文件
        
        Returns:
            列表元素为 (完整路径, 文件名不含扩展名, 扩展名)
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
        """确保目录存在，不存在则创建"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def safe_delete_file(file_path: str) -> Tuple[bool, str]:
        """安全删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True, ""
            return False, "文件不存在"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def safe_move_file(src: str, dst: str, overwrite: bool = False) -> Tuple[bool, str]:
        """安全移动文件"""
        try:
            if not overwrite and os.path.exists(dst):
                return False, "目标文件已存在"
            
            FileOperator.ensure_directory(os.path.dirname(dst))
            shutil.move(src, dst)
            return True, ""
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def safe_copy_file(src: str, dst: str, overwrite: bool = False) -> Tuple[bool, str]:
        """安全复制文件"""
        try:
            if not overwrite and os.path.exists(dst):
                return False, "目标文件已存在"
            
            FileOperator.ensure_directory(os.path.dirname(dst))
            shutil.copy2(src, dst)
            return True, ""
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    @staticmethod
    def test_directory_writable(path: str) -> Tuple[bool, str]:
        """测试目录是否可写"""
        try:
            test_file = os.path.join(path, "_write_test.tmp")
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True, ""
        except Exception as e:
            return False, str(e)
