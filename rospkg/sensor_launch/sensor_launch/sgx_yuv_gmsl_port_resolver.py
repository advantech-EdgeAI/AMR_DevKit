#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sgx_yuv_gmsl_port_resolver_node

def main():
    sgx_yuv_gmsl_port_resolver_node.main()

if __name__=="__main__":
    main()
