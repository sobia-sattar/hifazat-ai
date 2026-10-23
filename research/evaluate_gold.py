"""Only genuinely external multilabel annotations are evaluated."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.evaluation.external import main
if __name__ == '__main__':
    main()
