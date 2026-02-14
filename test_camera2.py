import cv2

print("Testing camera with different backends...\n")

backends = [
    (cv2.CAP_DSHOW, "DirectShow"),
    (cv2.CAP_MSMF, "Media Foundation"),
    (cv2.CAP_ANY, "Auto")
]

for backend_id, backend_name in backends:
    print(f"=== Testing {backend_name} backend ===")
    for i in range(3):
        print(f"Trying camera index {i}...")
        camera = cv2.VideoCapture(i, backend_id)
        
        if camera.isOpened():
            # Set resolution
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            ret, frame = camera.read()
            if ret and frame is not None:
                print(f"✓✓✓ SUCCESS! Camera {i} with {backend_name} works!")
                print(f"Frame shape: {frame.shape}")
                cv2.imshow(f'Working Camera - Index {i} - {backend_name}', frame)
                print("Press any key to close...")
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                camera.release()
                print(f"\n*** USE: Camera index {i} with backend {backend_name} ***\n")
                break
            else:
                print(f"✗ Cannot capture frame")
            camera.release()
        else:
            print(f"✗ Cannot open")
    print()
