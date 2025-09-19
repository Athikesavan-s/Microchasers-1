import cv2
import numpy as np
import os

def detect_microplastics(image_path):
    """
    Detects microplastics in an image, extracts their features, and annotates the image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        tuple: A tuple containing:
            - list: A list of dictionaries, where each dictionary represents a
                    detection and contains 'x', 'y', 'size', 'shape', and 'color'.
            - str: The path to the output image with detections drawn on it.
    """
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return [], None

    # Read the image
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        print(f"Could not read image from {image_path}")
        return [], None

    output_image = image.copy()

    # Convert image to HSV color space for better color thresholding
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Apply bilateral filter to reduce noise while preserving edges
    bilateral = cv2.bilateralFilter(image, 9, 75, 75)
    
    # Convert to grayscale for additional processing
    gray = cv2.cvtColor(bilateral, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding to handle varying lighting conditions
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                 cv2.THRESH_BINARY_INV, 11, 2)
    
    # Define multiple color ranges to catch different types of microplastics
    color_ranges = [
        # Bright/white particles
        (np.array([0, 0, 150]), np.array([180, 30, 255])),
        # Colored particles
        (np.array([0, 50, 50]), np.array([180, 255, 255])),
    ]
    
    # Combine masks from different color ranges
    mask = np.zeros(gray.shape, dtype=np.uint8)
    for lower, upper in color_ranges:
        color_mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.bitwise_or(mask, color_mask)
    
    # Apply morphological operations to clean up the mask
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detections = []
    for contour in contours:
        # Filter out contours based on area and perimeter
        area = cv2.contourArea(contour)
        if area < 50 or area > 10000:  # Adjust these thresholds based on your images
            continue
            
        # Calculate solidity to filter out noise
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            continue
        solidity = float(area) / hull_area
        if solidity < 0.1:  # Filter very irregular shapes that might be noise
            continue

        # --- Feature Extraction ---

        # 1. Location (centroid)
        M = cv2.moments(contour)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # 2. Size (area)
        size = cv2.contourArea(contour)

        # 3. Shape classification
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * (size / (perimeter * perimeter))
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h

        shape = "fragment"
        if circularity > 0.8:
            shape = "bead"
        elif aspect_ratio > 3 or aspect_ratio < 0.3:
            shape = "fiber"

        # 4. Color
        mask_i = np.zeros(image.shape[:2], dtype="uint8")
        cv2.drawContours(mask_i, [contour], -1, 255, -1)
        mean_color_bgr = cv2.mean(image, mask=mask_i)
        # Convert BGR to a hex string for easier display
        mean_color_hex = '#%02x%02x%02x' % (int(mean_color_bgr[2]), int(mean_color_bgr[1]), int(mean_color_bgr[0]))


        detections.append({
            'x_coordinate': cx,
            'y_coordinate': cy,
            'size': size,
            'shape': shape,
            'color': mean_color_hex
        })

        # --- Annotation ---
        # Draw contour with color based on shape
        color_map = {
            'bead': (255, 0, 0),    # Blue for beads
            'fiber': (0, 0, 255),   # Red for fibers
            'fragment': (0, 255, 0)  # Green for fragments
        }
        contour_color = color_map.get(shape, (0, 255, 0))
        cv2.drawContours(output_image, [contour], -1, contour_color, 2)
        
        # Draw a marker at the centroid
        cv2.drawMarker(output_image, (cx, cy), contour_color, 
                      markerType=cv2.MARKER_CROSS, markerSize=10, thickness=2)
        
        # Add labels with more information
        label = f"{shape} ({int(size)}px)"
        # Create a dark background for text for better visibility
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(output_image, (cx - 2, cy - text_h - 10), 
                     (cx + text_w + 2, cy - 2), (0, 0, 0), -1)
        cv2.putText(output_image, label, (cx, cy - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)


    # Save the output image
    directory, filename = os.path.split(image_path)
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}_processed{ext}"
    output_path = os.path.join(directory, output_filename)
    cv2.imwrite(output_path, output_image)

    return detections, output_path
