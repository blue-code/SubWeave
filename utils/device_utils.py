"""
Device Detection Utilities
Detects available GPU devices for ML acceleration on macOS, CUDA, etc.
"""
import platform
import logging
from typing import Optional


def get_optimal_device() -> str:
    """
    Detect the best available device for ML tasks.

    Returns:
        Device string: "mps" (macOS GPU), "cuda" (NVIDIA GPU), or "cpu"
    """
    # Check for macOS Metal Performance Shaders (Apple Silicon GPU)
    if platform.system() == "Darwin":  # macOS
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                logging.info("Detected Apple Silicon GPU (MPS) - using GPU acceleration")
                return "mps"
        except ImportError:
            pass
        except Exception as e:
            logging.warning(f"Error checking MPS availability: {e}")

    # Check for NVIDIA CUDA GPU
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            logging.info(f"Detected CUDA GPU: {device_name} - using GPU acceleration")
            return "cuda"
    except ImportError:
        pass
    except Exception as e:
        logging.warning(f"Error checking CUDA availability: {e}")

    # Fallback to CPU
    logging.info("No GPU detected - using CPU")
    return "cpu"


def get_ctranslate2_device() -> str:
    """
    Get the optimal device for CTranslate2.

    CTranslate2 supports: "cpu", "cuda", "auto"
    Note: CTranslate2 does not natively support MPS, so we use CPU for macOS

    Returns:
        Device string for CTranslate2
    """
    # Check for NVIDIA CUDA GPU
    try:
        import torch
        if torch.cuda.is_available():
            logging.info("CTranslate2 using CUDA")
            return "cuda"
    except ImportError:
        pass
    except Exception as e:
        logging.warning(f"Error checking CUDA for CTranslate2: {e}")

    # CTranslate2 doesn't support MPS, use CPU
    if platform.system() == "Darwin":
        logging.info("CTranslate2 using CPU (MPS not supported by CTranslate2)")
        return "cpu"

    # Use auto detection for other platforms
    return "auto"


def check_gpu_available() -> bool:
    """
    Check if any GPU acceleration is available.

    Returns:
        True if GPU is available, False otherwise
    """
    device = get_optimal_device()
    return device in ["mps", "cuda"]


def get_device_info() -> dict:
    """
    Get detailed information about available devices.

    Returns:
        Dictionary with device information
    """
    info = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "optimal_device": get_optimal_device(),
        "mps_available": False,
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_devices": []
    }

    # Check MPS
    if platform.system() == "Darwin":
        try:
            import torch
            if hasattr(torch.backends, 'mps'):
                info["mps_available"] = torch.backends.mps.is_available()
                if info["mps_available"]:
                    info["mps_built"] = torch.backends.mps.is_built()
        except ImportError:
            pass
        except Exception as e:
            logging.warning(f"Error getting MPS info: {e}")

    # Check CUDA
    try:
        import torch
        info["cuda_available"] = torch.cuda.is_available()
        if info["cuda_available"]:
            info["cuda_device_count"] = torch.cuda.device_count()
            info["cuda_devices"] = [
                {
                    "id": i,
                    "name": torch.cuda.get_device_name(i),
                    "memory_total": torch.cuda.get_device_properties(i).total_memory
                }
                for i in range(torch.cuda.device_count())
            ]
    except ImportError:
        pass
    except Exception as e:
        logging.warning(f"Error getting CUDA info: {e}")

    return info


def log_device_info():
    """Log detailed device information."""
    info = get_device_info()

    logging.info("=" * 60)
    logging.info("Device Information:")
    logging.info(f"  Platform: {info['platform']} ({info['machine']})")
    logging.info(f"  Optimal Device: {info['optimal_device']}")

    if info["mps_available"]:
        logging.info("  Apple Silicon GPU (MPS): Available")

    if info["cuda_available"]:
        logging.info(f"  CUDA GPUs: {info['cuda_device_count']} device(s)")
        for device in info["cuda_devices"]:
            memory_gb = device["memory_total"] / (1024**3)
            logging.info(f"    - {device['name']} ({memory_gb:.1f} GB)")

    if not info["mps_available"] and not info["cuda_available"]:
        logging.info("  GPU Acceleration: Not available (using CPU)")

    logging.info("=" * 60)
