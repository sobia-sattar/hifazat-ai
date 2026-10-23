"""Compatibility entry point; train current baselines then freeze test evaluation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.training.train_baselines import main
from src.evaluation.evaluate import main as evaluate
if __name__ == '__main__':
    main()
    evaluate()
