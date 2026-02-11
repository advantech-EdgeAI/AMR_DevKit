#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pointcloud_downsample_node

def main():
    pointcloud_downsample_node.main()

if __name__=="__main__":
    main()
