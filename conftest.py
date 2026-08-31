# pytest — რეპოს ძირი sys.path-ზე, რომ `tools.*` იმპორტირებადი იყოს.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
