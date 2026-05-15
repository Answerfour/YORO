"""自然排序工具 - 处理文件名中的数字部分排序"""
import re
from typing import List


def natural_sort_key(filename: str) -> List:
    """自然排序键函数，处理文件名中的数字部分
    
    例如:
        'file1.txt' -> ['file', 1, '.txt']
        'file10.txt' -> ['file', 10, '.txt']
        'file2.txt' -> ['file', 2, '.txt']
    
    Returns:
        排序键列表
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', filename)]


def natural_sort(files: List[str]) -> List[str]:
    """对文件列表进行自然排序
    
    Args:
        files: 文件名列表
    
    Returns:
        排序后的文件列表
    """
    return sorted(files, key=natural_sort_key)


def get_sorted_files(folder_path: str, extensions: List[str]) -> List[str]:
    """获取文件夹中指定扩展名的文件并自然排序
    
    Args:
        folder_path: 文件夹路径
        extensions: 扩展名列表，如 ['.txt', '.jpg']
    
    Returns:
        排序后的文件路径列表
    """
    import os
    
    files = []
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(file)
            if ext.lower() in [e.lower() for e in extensions]:
                files.append(file)
    
    return [os.path.join(folder_path, f) for f in natural_sort(files)]
