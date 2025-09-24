# test_opencv.py
import cv2
import numpy as np

# Test if OpenCV GUI works
try:
    # Create a test image
    test_image = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.putText(test_image, "OpenCV Test", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Try to display it
    cv2.imshow("Test Window", test_image)
    print("✅ OpenCV GUI is working!")
    print("Press any key to close the window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
except Exception as e:
    print(f"❌ OpenCV GUI error: {e}")