"""视频切帧核心逻辑"""
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

import os
from datetime import datetime
from typing import Optional, Callable, List, Tuple
from config.schema import FrameExtractorConfig


class FrameExtractor:
    """视频切帧器"""
    
    def __init__(self, video_path: str, config: FrameExtractorConfig, output_dir: str):
        self.video_path = video_path
        self.config = config
        self.output_dir = output_dir
        self._running = False
        self._cancel_requested = False
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._message_callback: Optional[Callable[[str, str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        self._progress_callback = callback
    
    def set_message_callback(self, callback: Callable[[str, str], None]):
        self._message_callback = callback
    
    def report_progress(self, current: int, total: int, message: str = ""):
        if self._progress_callback:
            self._progress_callback(current, total, message)
    
    def report_message(self, message: str, level: str = "info"):
        if self._message_callback:
            self._message_callback(message, level)
    
    def execute(self) -> Tuple[bool, int, List[str]]:
        """执行切帧，返回 (是否成功, 提取帧数, 错误列表)"""
        self._running = True
        self._cancel_requested = False
        errors = []
        frames_extracted = 0
        
        if not CV2_AVAILABLE:
            return False, 0, ["未安装OpenCV库，请运行: pip install opencv-python"]
        
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                return False, 0, ["无法打开视频文件"]
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if fps <= 0:
                return False, 0, ["视频帧率无效"]
            
            self.report_message(f"视频信息: 总帧数={total_frames}, 帧率={fps:.2f}")
            
            start_frame = int(self.config.start_time * fps)
            end_frame = int(self.config.end_time * fps)
            frame_interval = max(1, int(fps / self.config.sample_fps))
            
            if self.config.create_subfolder:
                video_name = os.path.splitext(os.path.basename(self.video_path))[0]
                folder_name = self.config.subfolder_name.replace("{video_name}", video_name)
                output_path = os.path.join(self.output_dir, folder_name)
            else:
                output_path = self.output_dir
            
            os.makedirs(output_path, exist_ok=True)
            self.report_message(f"输出目录: {output_path}")
            
            frame_idx = 0
            saved_idx = self.config.start_number
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_frame = start_frame
            
            total_to_process = end_frame - start_frame
            
            while current_frame <= end_frame and cap.isOpened():
                if self._cancel_requested:
                    self.report_message("用户取消操作", "warning")
                    break
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                if (current_frame - start_frame) % frame_interval == 0:
                    filename = self._generate_filename(saved_idx, current_frame / fps)
                    frame_output_path = os.path.join(output_path, filename)
                    
                    if self._save_frame(frame, frame_output_path):
                        frames_extracted += 1
                        saved_idx += 1
                        self.report_progress(frame_idx, total_to_process, f"处理帧 {current_frame}/{total_frames}")
                
                current_frame += 1
                frame_idx += 1
            
            cap.release()
            
            self.report_message(f"切帧完成: 成功提取 {frames_extracted} 帧", "success")
            
        except Exception as e:
            errors.append(str(e))
            self.report_message(f"切帧出错: {e}", "error")
        finally:
            self._running = False
        
        return len(errors) == 0, frames_extracted, errors
    
    def cancel(self):
        self._cancel_requested = True
        self.report_message("正在停止...")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def _generate_filename(self, index: int, timestamp: float) -> str:
        fmt = self.config.output_format
        digits = self.config.digit_length
        
        if self.config.naming_mode == "sequence":
            return f"{index:0{digits}d}.{fmt}"
        elif self.config.naming_mode == "custom":
            return f"{self.config.custom_prefix}_{index:0{digits}d}.{fmt}"
        else:
            dt = datetime.fromtimestamp(timestamp)
            return f"{dt.strftime(self.config.time_format)}.{fmt}"
    
    def _save_frame(self, frame, output_path: str) -> bool:
        try:
            if self.config.output_format == "jpg":
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.config.quality]
                return cv2.imwrite(output_path, frame, encode_param)
            else:
                return cv2.imwrite(output_path, frame)
        except Exception:
            return False
