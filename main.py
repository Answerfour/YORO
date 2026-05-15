#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YOLO训练工具集合 - 程序入口

使用方法:
    python main.py

或者双击运行此文件
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import main

if __name__ == "__main__":
    main()
