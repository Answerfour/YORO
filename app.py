"""YOLO训练工具集合 - 主程序入口"""
import tkinter as tk
from tkinter import ttk
from modules.frame_extractor.gui import FrameExtractorGUI
from modules.file_renamer.gui import FileRenamerGUI
from modules.orphan_cleaner.gui import OrphanCleanerGUI
from modules.yolo_stats.gui import YOLOStatsGUI
from ui.theme import Theme


class YOLOToolsApp:
    """YOLO工具集主应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO训练工具集合")
        self.root.geometry("1000x800")
        
        Theme.apply_default_style()
        
        self._create_menu()
        self._create_ui()
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.frame_extractor = FrameExtractorGUI(notebook)
        notebook.add(self.frame_extractor, text="📹 视频切帧")
        
        self.file_renamer = FileRenamerGUI(notebook)
        notebook.add(self.file_renamer, text="📝 文件重命名")
        
        self.orphan_cleaner = OrphanCleanerGUI(notebook)
        notebook.add(self.orphan_cleaner, text="🧹 孤立文件清理")
        
        self.yolo_stats = YOLOStatsGUI(notebook)
        notebook.add(self.yolo_stats, text="📊 YOLO统计")
    
    def _show_about(self):
        from tkinter import messagebox
        messagebox.showinfo(
            "关于",
            "YOLO训练工具集合\n\n"
            "版本: 2.0 (模块化重构版)\n\n"
            "包含功能:\n"
            "• 视频切帧工具\n"
            "• 批量文件重命名\n"
            "• 孤立文件清理\n"
            "• YOLO标注统计\n\n"
            "基于分层架构设计，模块化开发"
        )


def main():
    root = tk.Tk()
    app = YOLOToolsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
