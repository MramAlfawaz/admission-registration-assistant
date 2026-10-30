"""Fix every source of randomness to one seed (Development Standards rule 1.2)."""
import random


def set_seed(seed):
    """Seed Python, NumPy and PyTorch, including CUDA when present.

    Args:
        seed: the integer seed from configuration.
    """
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
