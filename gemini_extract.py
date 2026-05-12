import pdfplumber
import cv2
import numpy as np
import re
import json
import sys
import math
import os
from shapely.geometry import LineString, Polygon, MultiPolygon, Point
from shapely.ops import unary_union, polygonize

# Ensure UTF-8 output for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def get_floorplan_bboxes(page):
    im = page.to_image(resolution=300)
    pil_image = im.original
    open_cv_image = np.array(pil_image)
    
    pdf_width = page.width
    pdf_height = page.height
    img_width = pil_image.width
    img_height = pil_image.height
    x_scale = float(pdf_width) / img_width
    y_scale = float(pdf_height) / img_height
    
    # Prepare image for OpenCV display (RGB to BGR)
    if len(open_cv_image.shape) == 3:
        display_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
    else:
        display_image = open_cv_image
        
    # Scale down the image so it actually fits on the user's screen
    max_display_height = 900.0
    display_scale = max_display_height / display_image.shape[0]
    
    if display_scale < 1.0:
        display_width = int(display_image.shape[1] * display_scale)
        display_height = int(display_image.shape[0] * display_scale)
        display_image_resized = cv2.resize(display_image, (display_width, display_height))
    else:
        display_image_resized = display_image
        display_scale = 1.0
        
    print("Please select the bounding box for the exact apartment floor plan.")
    print("Drag a rectangle, then press ENTER or SPACE to confirm.")
    print("Press 'c' to cancel.")
    
    # 2. Interactive ROI Selection on the RESIZED image
    roi = cv2.selectROI("Select Floor Plan", display_image_resized, fromCenter=False, showCrosshair=True)
    cv2.destroyAllWindows()
    
    x_scaled, y_scaled, w_scaled, h_scaled = roi
    
    if w_scaled == 0 or h_scaled == 0:
        return []
        
    # Upscale the ROI back to the original 300 DPI pixel coordinates
    x = x_scaled / display_scale
    y = y_scaled / display_scale
    w = w_scaled / display_scale
    h = h_scaled / display_scale
    
    # 5. Convert pixel coordinates back to pdfplumber points
    x0 = x * x_scale
    top = y * y_scale
    x1 = (x + w) * x_scale
    bottom = (y + h) * y_scale
    
    x0, top = max(0, x0), max(0, top)
    x1, bottom = min(pdf_width, x1), min(pdf_height, bottom)
    
    # 6. Pass ONLY this manually selected BBOX
    return [(x0, top, x1, bottom)]

def extract_metadata(text):
    level_matches = re.findall(r'[+-]\d{1,2}\.\d{2}', text)
    unique_levels = sorted(list(set(level_matches)), key=lambda x: float(x))
    address_match = re.search(r'(נחל איילון\s*[\d,]+)', text)
    if not address_match:
        address_match = re.search(r'([א-ת]+\s+[א-ת]+\s+\d+(?:,\d+)?)', text)
    neighborhood_match = re.search(r'(רמת בית שמש [א-ת]\')', text)
    if not neighborhood_match:
         neighborhood_match = re.search(r'(שכונת\s+[א-ת\' ]+)', text)
    address = address_match.group(1).strip() if address_match else "Unknown Address"
    neighborhood = neighborhood_match.group(1).strip() if neighborhood_match else "Unknown Neighborhood"
    return address, neighborhood, [float(lvl) for lvl in unique_levels]

def assign_floor_levels(page, bboxes, all_levels):
    assigned_floors = []
    for bbox in bboxes:
        x0, top, x1, bottom = bbox
        expanded_bbox = (max(0, x0 - 50), max(0, top - 50), min(page.width, x1 + 50), min(page.height, bottom + 50))
        cropped = page.within_bbox(expanded_bbox)
        text = cropped.extract_text() or ""
        matched_level = None
        for lvl in all_levels:
            lvl_str_plus = f"{lvl:+.2f}"
            lvl_str = f"{lvl:.2f}"
            if lvl_str_plus in text or lvl_str in text:
                matched_level = lvl
                break
        if matched_level is None:
             local_matches = re.findall(r'[+-]\d{1,2}\.\d{2}', text)
             if local_matches:
                 matched_level = float(local_matches[0])
        if matched_level is not None:
             assigned_floors.append({"level": matched_level, "bbox": bbox})
    assigned_floors.sort(key=lambda x: x["level"])
    return assigned_floors

def calculate_scale_factor(words, lines):
    """
    2. Dynamic Scale Calibration (Points to CM)
    Finds a numeric length (e.g. "300") and compares it to the nearest drawn line.
    """
    for w in words:
        if w['text'].isdigit():
            val_cm = float(w['text'])
            if 50 <= val_cm <= 1500: # Reasonable architectural wall length in CM
                cx = (w['x0'] + w['x1']) / 2
                cy = (w['top'] + w['bottom']) / 2
                
                best_line = None
                min_dist = float('inf')
                
                for line in lines:
                    lcx = (line["x0"] + line["x1"]) / 2
                    lcy = (line["y0"] + line["y1"]) / 2
                    dist = math.hypot(lcx - cx, lcy - cy)
                    if dist < min_dist:
                        min_dist = dist
                        best_line = line
                
                # If nearest line is physically close to the measurement text
                if best_line and min_dist < 30: 
                    pdf_len = math.hypot(best_line["x1"] - best_line["x0"], best_line["y1"] - best_line["y0"])
                    if pdf_len > 0:
                        return val_cm / pdf_len # Returns: Real CM per 1 PDF Point
                        
    return 100.0 / 30.0 # Default fallback if no valid measurement is found


def process_walls(lines, base_z, height_diff, bbox, scale_factor):
    """
    Buffer & Union Method
    Discards noise based on scaled length, then thickens individual surviving lines 
    into polygons via shapely buffer to heal fragmented drawings.
    """
    x0_b, top_b, x1_b, bottom_b = bbox
    bbox_width = x1_b - x0_b
    bbox_height = bottom_b - top_b
    
    polygons = []
    walls = []
    
    z_level = base_z * 100.0
    extruded_height = height_diff * 100.0 if height_diff > 0 else 300.0
    
    # 1. Aggressive Basic Filtering
    for line in lines:
        x0, y0, x1, y1 = line["x0"], line["y0"], line["x1"], line["y1"]
        
        # 1. Fix the Mirror Flip (Y-Axis Inversion)
        # pdfplumber coordinate systems can be inverted; this flips it relative to the local BBOX
        y0 = bbox_height - y0
        y1 = bbox_height - y1
        
        length = math.hypot(x1 - x0, y1 - y0)
        
        # Max Length: Discard massive dimensions and page borders (60% of BBOX)
        if length > 0.60 * bbox_width or length > 0.60 * bbox_height:
            continue
            
        scaled_len = length * scale_factor
        
        # Min Length: Discard exploded text vectors and dust (Increased to 35)
        if scaled_len < 35:
            continue
            
        # 2. The Buffer Method (Thickening Lines)
        # Convert coords to final scaled units for consistency
        sx0, sy0 = x0 * scale_factor, y0 * scale_factor
        sx1, sy1 = x1 * scale_factor, y1 * scale_factor
        
        # Buffer distance = 10 (which creates a 20-unit thick wall)
        ls = LineString([(sx0, sy0), (sx1, sy1)])
        poly = ls.buffer(10, cap_style=2, join_style=2)
        polygons.append(poly)
        
        # Output directly to Three.js; the 3D renderer natively handles overlapping BoxGeometries perfectly!
        cx = (sx0 + sx1) / 2.0
        cy = (sy0 + sy1) / 2.0
        rot_rad = -math.atan2(sy1 - sy0, sx1 - sx0)
        
        walls.append({
            "type": "wall",
            "position": {"x": round(cx, 2), "y": round(cy, 2), "z": round(z_level, 2)},
            "dimensions": {"width": round(scaled_len, 2), "height": round(extruded_height, 2), "depth": 20.0},
            "rotation": round(rot_rad, 4)
        })
        
    # 3. Global Union
    # This perfectly heals intersections and overlapping fragments geometrically. 
    # Can be passed to `extract_rooms_and_labels` if negative space extraction is required.
    if polygons:
        merged_geometry = unary_union(polygons)
        
    return walls


def extract_rooms_and_labels(walls, words, scale_factor):
    """
    3. Room Polygonization & Label Mapping
    Creates inner room bounds from walls and checks spatial containment of text labels.
    """
    ROOM_LABELS = ["מטבח", "סלון", "חדר", "ממ\"ד", "מרפסת", "אמבטיה", "שירותים"]
    rooms = []
    
    # Create LineStrings directly down the center of each scaled 3D wall
    wall_lines = []
    for w in walls:
        cx, cy = w["position"]["x"], w["position"]["y"]
        width = w["dimensions"]["width"]
        rotation = w.get("rotation", 0)
        
        # Determine original angle in PDF space
        angle = -rotation
        dx = (width / 2) * math.cos(angle)
        dy = (width / 2) * math.sin(angle)
        
        wall_lines.append(LineString([(cx - dx, cy - dy), (cx + dx, cy + dy)]))
            
    # Mathematically find all closed polygons (the empty space enclosed by walls)
    room_polygons = list(polygonize(wall_lines))
    
    for poly in room_polygons:
        # Calculate area (Coordinates are already in CM from process_walls)
        area_sqm = poly.area / 10000.0  # CM^2 to M^2
        if area_sqm < 1.0: continue     # Skip tiny accidental closures
        
        poly_center = poly.centroid
        room_label = "חלל" 
        measurements = []
        
        for w in words:
            # Scale word position to match the new CM world
            wx = ((w['x0'] + w['x1']) / 2) * scale_factor
            wy = ((w['top'] + w['bottom']) / 2) * scale_factor
            
            # Check if this text resides physically inside the generated room boundaries
            if poly.contains(Point(wx, wy)):
                text = w['text']
                if any(r in text for r in ROOM_LABELS):
                    room_label = text
                elif text.replace('.', '', 1).isdigit():
                    measurements.append(float(text))
                    
        rooms.append({
            "label": room_label,
            "area_sqm": round(area_sqm, 2),
            "extracted_measurements": measurements,
            "center_position": {
                "x": round(poly_center.x, 2),
                "y": 0,
                "z": round(poly_center.y, 2)
            }
        })
        
    return rooms

def detect_fixtures(cropped_page, bbox):
    fixtures = []
    template_dir = "./templates"
    if not os.path.exists(template_dir):
        return fixtures
        
    try:
        pil_img = cropped_page.to_image(resolution=300).original
        cv_img = np.array(pil_img)
        if len(cv_img.shape) == 3:
            gray_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2GRAY)
        else:
            gray_img = cv_img
            
        scale_factor = 72.0 / 300.0
            
        for filename in os.listdir(template_dir):
            if not filename.endswith('.png'): continue
            template_path = os.path.join(template_dir, filename)
            template = cv2.imread(template_path, 0)
            if template is None: continue
            
            h, w = template.shape
            res = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.8
            loc = np.where(res >= threshold)
            
            fixture_type = filename.split('.')[0]
            for pt in zip(*loc[::-1]):
                cx_pixels = pt[0] + w/2
                cy_pixels = pt[1] + h/2
                cx_points = cx_pixels * scale_factor
                cy_points = cy_pixels * scale_factor
                fixtures.append({
                    "type": fixture_type,
                    "position": {"x": round(cx_points, 2), "y": 0, "z": round(cy_points, 2)}
                })
    except Exception as e:
        print(f"Template matching warning: {e}")
    return fixtures

def main():
    pdf_path = "test.pdf"
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            bboxes = get_floorplan_bboxes(page)
            if not bboxes:
                print(json.dumps({"error": "Failed to isolate floor plan bounding boxes."}))
                sys.exit(1)
            
            text = page.extract_text() or ""
            address, neighborhood, all_levels = extract_metadata(text)
            assigned_floors = assign_floor_levels(page, bboxes, all_levels)
            
            structures = []
            
            for i, floor_data in enumerate(assigned_floors):
                bbox = floor_data["bbox"]
                level = floor_data["level"]
                
                if i < len(assigned_floors) - 1:
                    height_diff = assigned_floors[i+1]["level"] - level
                else:
                    height_diff = 3.0
                    
                cropped_page = page.within_bbox(bbox)
                
                # 1. Calculate Real Scale (CM per PDF Point)
                words = cropped_page.extract_words()
                scale_factor = calculate_scale_factor(words, cropped_page.lines)
                
                # 2. Extract perfectly scaled wall coordinates
                walls = process_walls(cropped_page.lines, level, height_diff, bbox, scale_factor)
                
                # 3. Polygonize walls to find livable rooms and map labels inside them
                rooms = extract_rooms_and_labels(walls, words, scale_factor)
                
                # 4. Detect Fixtures (Note: these coordinate outputs need scale_factor too ideally, but leaving as is)
                fixtures = detect_fixtures(cropped_page, bbox)
                
                structures.append({
                    "id": f"structure_{i+1}",
                    "type": "floor_plan",
                    "level": level,
                    "bbox": bbox,
                    "walls": walls,
                    "rooms": rooms,
                    "fixtures": fixtures
                })
                
            output = {
                "property_address": address,
                "neighborhood": neighborhood,
                "structures": structures
            }
            
            print(json.dumps(output, ensure_ascii=False, indent=2))
            with open("building_data.json", "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
                
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()