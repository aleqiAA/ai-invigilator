import cv2

print("Testing cameras...")

for i in range(5):
    print(f"\nTrying camera index {i}...")
    camera = cv2.VideoCapture(i)
    
    if camera.isOpened():
        print(f"✓ Camera {i} opened successfully!")
        ret, frame = camera.read()
        if ret:
            print(f"✓ Camera {i} can capture frames!")
            cv2.imshow(f'Camera {i} Test', frame)
            print("Press any key to close the window...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print(f"✗ Camera {i} cannot capture frames")
        camera.release()
    else:
        print(f"✗ Camera {i} not available")
        camera.release()

print("\nTest complete!")
