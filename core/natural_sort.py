"""Natural Sort Utilities - Handle numeric sorting in filenames"""
import re
from typing import List


def natural_sort_key(filename: str) -> List:
    """Natural sort key function, handles numeric portions of filenames
    
    Example:
        'file1.txt' -> ['file', 1, '.txt']
        'file10.txt' -> ['file', 10, '.txt']
        'file2.txt' -> ['file', 2, '.txt']
    
    Returns:
        Sort key list
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', filename)]


def natural_sort(files: List[str]) -> List[str]:
    """Sort file list using natural sorting
    
    Args:
        files: List of filenames
    
    Returns:
        Sorted file list
    """
    return sorted(files, key=natural_sort_key)


def get_sorted_files(folder_path: str, extensions: List[str]) -> List[str]:
    """Get files with specified extensions from folder and sort naturally
    
    Args:
        folder_path: Folder path
        extensions: List of extensions, e.g. ['.txt', '.jpg']
    
    Returns:
        Sorted list of file paths
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