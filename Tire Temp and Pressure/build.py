import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shared.tires import build_tires
if __name__ == '__main__':
    build_tires(Path(__file__).resolve().parent,'guysmiley222 - Tire Temp and Pressure','c43780b0-2a89-4e76-bf06-950c8078fde3','5a966e21-a636-4ac3-9a95-8d902c112e6a',retro=False)
