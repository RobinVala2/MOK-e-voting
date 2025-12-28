"""
This script wraps the Hyperion e-voting protocol and replaces the classical
DSA signatures with post-quantum ML-DSA signatures.

Usage:
    python pqc_hyperion_wrapper.py <num_voters> <num_tellers> <threshold> [-maxv <max_vote>]

The wrapper:
1. Imports the PQC primitives (ML-DSA)
2. Patches Hyperion's primitives module to use ML-DSA instead of DSA
3. Runs the Hyperion protocol with PQC signatures
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
hyperion_dir = os.path.join(project_root, 'hyperion')
sys.path.insert(0, hyperion_dir)
sys.path.insert(0, project_root)

import multiprocessing
try:
    multiprocessing.set_start_method('fork')
except RuntimeError:
    pass

from client.pqc_primitives import MLDSA

import primitives

# Store the original DSA class for reference
_OriginalDSA = primitives.DSA
primitives.DSA = MLDSA

print("[PQC] ML-DSA-65 enabled - replacing ECDSA signatures")
print()

if __name__ == "__main__":
    main_path = os.path.join(hyperion_dir, 'main.py')
    with open(main_path, 'r') as f:
        main_code = f.read()
    exec(compile(main_code, main_path, 'exec'))
