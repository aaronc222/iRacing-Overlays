import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shared.tires import build_tires
if __name__ == '__main__':
    build_tires(Path(__file__).resolve().parent,'guysmiley222 - Tire Temp and Pressure - retro','8332606b-e0d6-4ef9-9866-3912a63bf4ea','43d91d5d-582e-40fb-b77f-1efcf9277aee',retro=True)
