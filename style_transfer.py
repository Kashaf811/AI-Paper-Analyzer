import sys
import os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import cv2
from scipy.ndimage import gaussian_filter

def apply_vangogh_style(image):
    """Enhanced Van Gogh style with swirling brushstrokes and vibrant colors"""
    # Convert to OpenCV format
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Apply edge-preserving filter for painterly effect
    smooth = cv2.edgePreservingFilter(cv_image, flags=1, sigma_s=80, sigma_r=0.4)
    
    # Create texture using multiple bilateral filters
    texture1 = cv2.bilateralFilter(smooth, 15, 40, 40)
    texture2 = cv2.bilateralFilter(texture1, 15, 80, 80)
    
    # Add swirling effect using morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    swirl = cv2.morphologyEx(texture2, cv2.MORPH_CLOSE, kernel)
    
    # Enhance color saturation dramatically
    hsv = cv2.cvtColor(swirl, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = hsv[:, :, 1] * 1.6  # Increase saturation
    hsv[:, :, 2] = hsv[:, :, 2] * 1.1  # Slight brightness increase
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    
    result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    # Add brushstroke effect
    result = add_brushstroke_effect(result)
    
    # Convert back to PIL
    final_image = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    
    # Final color enhancement
    enhancer = ImageEnhance.Color(final_image)
    final_image = enhancer.enhance(1.3)
    
    enhancer = ImageEnhance.Contrast(final_image)
    final_image = enhancer.enhance(1.2)
    
    return final_image

def apply_picasso_style(image):
    """Enhanced Picasso cubist style with geometric fragmentation"""
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    h, w = cv_image.shape[:2]
    
    # Create cubist fragmentation
    result = np.zeros_like(cv_image)
    
    # Define geometric segments
    segments = [
        (0, 0, w//3, h//2),           # Top-left
        (w//3, 0, 2*w//3, h//3),      # Top-center
        (2*w//3, 0, w, h//2),         # Top-right
        (0, h//2, w//2, h),           # Bottom-left
        (w//2, h//3, w, 2*h//3),      # Center-right
        (w//4, 2*h//3, 3*w//4, h)     # Bottom-center
    ]
    
    for i, (x1, y1, x2, y2) in enumerate(segments):
        # Extract segment
        segment = cv_image[y1:y2, x1:x2]
        if segment.size > 0:
            # Apply different transformations to each segment
            if i % 3 == 0:
                # Posterize effect
                segment = segment // 64 * 64
            elif i % 3 == 1:
                # High contrast
                segment = cv2.convertScaleAbs(segment, alpha=1.5, beta=-50)
            else:
                # Color shift
                hsv = cv2.cvtColor(segment, cv2.COLOR_BGR2HSV)
                hsv[:, :, 0] = (hsv[:, :, 0] + 30) % 180  # Hue shift
                segment = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
            result[y1:y2, x1:x2] = segment
    
    # Add geometric lines
    result = add_geometric_lines(result)
    
    # Convert back to PIL
    final_image = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    
    # Enhance contrast for bold effect
    enhancer = ImageEnhance.Contrast(final_image)
    final_image = enhancer.enhance(1.4)
    
    return final_image

def apply_monet_style(image):
    """Enhanced Monet impressionist style with soft, dreamy effects"""
    # Convert to array for processing
    img_array = np.array(image).astype(np.float32)
    
    # Apply multiple gaussian blur layers for impressionist effect
    layer1 = gaussian_filter(img_array, sigma=1.5)
    layer2 = gaussian_filter(img_array, sigma=3.0)
    layer3 = gaussian_filter(img_array, sigma=0.8)
    
    # Blend layers for depth
    blended = 0.4 * layer1 + 0.3 * layer2 + 0.3 * layer3
    
    # Add color temperature adjustment (warmer tones)
    blended[:, :, 0] = np.minimum(255, blended[:, :, 0] * 1.1)  # Red
    blended[:, :, 1] = np.minimum(255, blended[:, :, 1] * 1.05) # Green
    blended[:, :, 2] = np.minimum(255, blended[:, :, 2] * 0.95) # Blue
    
    result = Image.fromarray(blended.astype(np.uint8))
    
    # Apply soft focus effect
    result = result.filter(ImageFilter.GaussianBlur(radius=0.8))
    
    # Enhance brightness for that "en plein air" look
    enhancer = ImageEnhance.Brightness(result)
    result = enhancer.enhance(1.15)
    
    # Slight color enhancement
    enhancer = ImageEnhance.Color(result)
    result = enhancer.enhance(1.1)
    
    return result

def apply_abstract_style(image):
    """Enhanced abstract style with dynamic color manipulation"""
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Apply stylization with strong parameters
    stylized = cv2.stylization(cv_image, sigma_s=200, sigma_r=0.3)
    
    # Create color posterization
    data = np.float32(stylized).reshape((-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, 8, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    posterized = centers[labels.flatten()].reshape(stylized.shape)
    
    # Add noise for texture
    noise = np.random.randint(-20, 20, posterized.shape, dtype=np.int16)
    posterized = np.clip(posterized.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Convert back to PIL
    result = Image.fromarray(cv2.cvtColor(posterized, cv2.COLOR_BGR2RGB))
    
    # Dramatic color enhancement
    enhancer = ImageEnhance.Color(result)
    result = enhancer.enhance(1.8)
    
    enhancer = ImageEnhance.Contrast(result)
    result = enhancer.enhance(1.4)
    
    return result

def apply_dali_style(image):
    """Surrealist style inspired by Salvador Dali"""
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    h, w = cv_image.shape[:2]
    
    # Create dreamlike distortion
    map_x = np.float32([[x + 15*np.sin(y/20) for x in range(w)] for y in range(h)])
    map_y = np.float32([[y + 10*np.cos(x/25) for x in range(w)] for y in range(h)])
    
    distorted = cv2.remap(cv_image, map_x, map_y, cv2.INTER_LINEAR)
    
    # Apply color manipulation for surreal effect
    hsv = cv2.cvtColor(distorted, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 0] = (hsv[:, :, 0] + 60) % 180  # Dramatic hue shift
    hsv[:, :, 1] = np.minimum(255, hsv[:, :, 1] * 1.4)  # Increase saturation
    
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    # Add edge enhancement for sharp details
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    result = cv2.addWeighted(result, 0.8, edges_colored, 0.2, 0)
    
    final_image = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    
    # Final enhancement
    enhancer = ImageEnhance.Contrast(final_image)
    final_image = enhancer.enhance(1.3)
    
    return final_image

def apply_warhol_style(image):
    """Pop art style inspired by Andy Warhol"""
    # Resize to standard pop art dimensions
    image = image.resize((300, 300), Image.LANCZOS)
    
    # Convert to high contrast
    enhancer = ImageEnhance.Contrast(image)
    high_contrast = enhancer.enhance(2.0)
    
    # Posterize for pop art effect
    posterized = ImageOps.posterize(high_contrast, 3)
    
    # Create the classic 4-panel Warhol effect
    panels = []
    colors = [
        (255, 100, 100),  # Red tint
        (100, 255, 100),  # Green tint
        (100, 100, 255),  # Blue tint
        (255, 255, 100)   # Yellow tint
    ]
    
    for color in colors:
        panel = posterized.copy()
        panel_array = np.array(panel)
        
        # Apply color tint
        panel_array = panel_array.astype(np.float32)
        panel_array[:, :, 0] = panel_array[:, :, 0] * (color[0] / 255.0)
        panel_array[:, :, 1] = panel_array[:, :, 1] * (color[1] / 255.0)
        panel_array[:, :, 2] = panel_array[:, :, 2] * (color[2] / 255.0)
        
        panels.append(Image.fromarray(panel_array.astype(np.uint8)))
    
    # Combine panels into 2x2 grid
    result = Image.new('RGB', (600, 600))
    result.paste(panels[0], (0, 0))
    result.paste(panels[1], (300, 0))
    result.paste(panels[2], (0, 300))
    result.paste(panels[3], (300, 300))
    
    return result

def apply_kandinsky_style(image):
    """Abstract expressionist style inspired by Kandinsky"""
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Create abstract shapes overlay
    h, w = cv_image.shape[:2]
    overlay = np.zeros_like(cv_image)
    
    # Add random geometric shapes
    for _ in range(20):
        # Random circles
        center = (np.random.randint(0, w), np.random.randint(0, h))
        radius = np.random.randint(10, 50)
        color = tuple(map(int, np.random.randint(0, 255, 3)))
        cv2.circle(overlay, center, radius, color, -1)
        
        # Random rectangles
        pt1 = (np.random.randint(0, w), np.random.randint(0, h))
        pt2 = (np.random.randint(pt1[0], w), np.random.randint(pt1[1], h))
        color = tuple(map(int, np.random.randint(0, 255, 3)))
        cv2.rectangle(overlay, pt1, pt2, color, -1)
    
    # Blend with original image
    result = cv2.addWeighted(cv_image, 0.6, overlay, 0.4, 0)
    
    # Apply strong color enhancement
    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.minimum(255, hsv[:, :, 1] * 1.8)  # Super high saturation
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    final_image = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    
    return final_image

def add_brushstroke_effect(cv_image):
    """Add brushstroke texture to image"""
    # Create brushstroke kernel
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(cv_image, -1, kernel)
    
    # Blend with original
    return cv2.addWeighted(cv_image, 0.7, sharpened, 0.3, 0)

def add_geometric_lines(cv_image):
    """Add geometric lines for cubist effect"""
    h, w = cv_image.shape[:2]
    
    # Add random lines
    for _ in range(15):
        pt1 = (np.random.randint(0, w), np.random.randint(0, h))
        pt2 = (np.random.randint(0, w), np.random.randint(0, h))
        cv2.line(cv_image, pt1, pt2, (0, 0, 0), 2)
    
    return cv_image

def process_image(input_path, output_path, style):
    """Main function to process image with specified style"""
    try:
        # Load image
        image = Image.open(input_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image if too large (for faster processing)
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.LANCZOS)
        
        # Apply style based on selection
        style_functions = {
            'vangogh': apply_vangogh_style,
            'picasso': apply_picasso_style,
            'monet': apply_monet_style,
            'abstract': apply_abstract_style,
            'dali': apply_dali_style,
            'warhol': apply_warhol_style,
            'kandinsky': apply_kandinsky_style
        }
        
        if style.lower() in style_functions:
            processed_image = style_functions[style.lower()](image)
        else:
            # Default to Van Gogh style
            processed_image = apply_vangogh_style(image)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save processed image with high quality
        processed_image.save(output_path, 'JPEG', quality=95, optimize=True)
        
        print(f"Successfully processed image with {style} style")
        print(f"Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python style_transfer.py <input_path> <output_path> <style>")
        print("Available styles: vangogh, picasso, monet, abstract, dali, warhol, kandinsky")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    style = sys.argv[3]
    
    # Validate input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} does not exist")
        sys.exit(1)
    
    process_image(input_path, output_path, style)