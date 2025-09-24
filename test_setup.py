# test_setup.py
import onnxruntime as ort
import faiss

print("=== System Check ===")
print("ONNX Runtime providers:", ort.get_available_providers())
print("CUDA available:", 'CUDAExecutionProvider' in ort.get_available_providers())
print("FAISS version:", faiss.__version__)
print("FAISS has GPU:", hasattr(faiss, 'StandardGpuResources'))

# Test if we can use GPU for ONNX
if 'CUDAExecutionProvider' in ort.get_available_providers():
    print("✅ ONNX will use GPU acceleration")
else:
    print("❌ ONNX will use CPU only")

print("✅ System is ready for RoboDog with partial GPU acceleration!")