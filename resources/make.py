from sys import argv
from sys import path as spath

spath.append("./resources/CircuitMPY/")
import circuitmpy

try:
    circuitmpy.compile_mpy("cptoml.py", "cptoml.mpy", optim=3)
except OSError:
    print("Compilation error, exiting")
    exit(1)
