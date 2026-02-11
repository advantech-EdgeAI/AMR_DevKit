#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import camera_resize_node

def main():
    camera_resize_node.main()

if __name__=="__main__":
    main()
