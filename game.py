import pdfplumber
import sys
import time
import re
import json

# Ensure terminal handles UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def process_architectural_pdf(file_path):
    start_time = time.time()
    results = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_height = float(page.height)
                page_width = float(page.width)
                
                # --- 1. Noise Filtration (Structural Bones) ---
                # We consider lines or rects with width/height > 0.1 as structural
                structural_elements = []
                
                # Check lines
                for line in page.lines:
                    # Line width is often 'width' or 'linewidth'
                    w = line.get('width', line.get('linewidth', 0))
                    if w > 0.1:
                        structural_elements.append(line)
                
                # Check rects (often walls are rects)
                for rect in page.rects:
                    rw = abs(rect['x1'] - rect['x0'])
                    rh = abs(rect['bottom'] - rect['top'])
                    # If it's a structural element, it shouldn't be too small or too thin (hatching)
                    if rw > 0.1 and rh > 0.1:
                        structural_elements.append(rect)
                
                # --- 2. Spatial Segmentation (Y-axis Projection) ---
                num_bins = 500
                bin_size = page_height / num_bins
                y_density = [0] * num_bins
                
                for obj in structural_elements:
                    y0 = max(0, min(page_height, obj['top']))
                    y1 = max(0, min(page_height, obj['bottom']))
                    v_len = abs(y1 - y0)
                    
                    # Heuristic: Ignore lines that span almost the entire page height for segmentation
                    # as they are likely borders or title block separators that bridge plans.
                    if v_len > (page_height * 0.8):
                        continue

                    start_bin = int(y0 / bin_size)
                    end_bin = int(y1 / bin_size)
                    for b in range(start_bin, min(num_bins, end_bin + 1)):
                        y_density[b] += 1
                
                # --- 3. Identify Bands (Floor Plan Boxes) ---
                bands = []
                in_band = False
                band_start = 0
                
                for b in range(num_bins):
                    has_content = y_density[b] > 2 # Low threshold to catch small details
                    if has_content and not in_band:
                        in_band = True
                        band_start = b * bin_size
                    elif not has_content and in_band:
                        in_band = False
                        band_end = b * bin_size
                        if (band_end - band_start) > 20: 
                            bands.append({'top': band_start, 'bottom': band_end})
                
                if in_band:
                    bands.append({'top': band_start, 'bottom': page_height})

                # --- 4. Anchor Identification (Elevation Levels) ---
                elevation_pattern = re.compile(r'([±+-]\d+\.\d+)(?:=(\d+\.\d+))?')
                words = page.extract_words()
                
                plan_boxes = []
                for band in bands:
                    box_words = [w for w in words if band['top'] <= w['top'] <= band['bottom']]
                    
                    elevation = None
                    area = None
                    
                    for w in box_words:
                        match = elevation_pattern.search(w['text'])
                        if match:
                            elevation = match.group(1)
                            if match.group(2):
                                area = float(match.group(2))
                            break
                    
                    elements_in_band = [e for e in structural_elements if band['top'] <= e['top'] <= band['bottom']]
                    if elements_in_band:
                        # Exclude the very long vertical lines from the bbox too if they are outside the main density
                        valid_elements = [e for e in elements_in_band if abs(e['bottom'] - e['top']) < (page_height * 0.8)]
                        if not valid_elements: valid_elements = elements_in_band
                        
                        x0 = min(e['x0'] for e in valid_elements)
                        x1 = max(e['x1'] for e in valid_elements)
                        
                        plan_boxes.append({
                            "bbox": [round(x0, 2), round(band['top'], 2), round(x1, 2), round(band['bottom'], 2)],
                            "elevation": elevation,
                            "area": area
                        })

                # --- 5. Table Cross-Referencing ---
                area_pattern = re.compile(r'(\d+\.\d{2})')
                for box in plan_boxes:
                    if box["area"] is None:
                        box_words = [w for w in words if box['bbox'][1] <= w['top'] <= box['bbox'][3]]
                        for w in box_words:
                            # Skip if it was already identified as an elevation
                            if elevation_pattern.search(w['text']): continue
                            
                            match = area_pattern.search(w['text'])
                            if match:
                                val = float(match.group(1))
                                if val > 10:
                                    box["area"] = val
                                    break

                results.append({
                    "page": page_num + 1,
                    "plans": plan_boxes
                })

                # --- 6. Screenshot Generation ---
                try:
                    # Render the page to an image
                    # Note: This might require Ghostscript or ImageMagick on some systems
                    print(f"Generating screenshots for Page {page_num + 1}...")
                    img = page.to_image(resolution=100)
                    
                    for i, box in enumerate(plan_boxes):
                        bbox = box['bbox']
                        # Crop the page first, then convert to image
                        cropped_page = page.crop(bbox)
                        
                        if i == 1:
                            print("Lines in Bounding Box 2:")
                            for line in cropped_page.lines:
                                print(line)
                                
                        img = cropped_page.to_image(resolution=100)
                        
                        elev_str = box['elevation'].replace('+', 'plus').replace('-', 'minus').replace('±', 'plusminus') if box['elevation'] else f"plan_{i+1}"
                        filename = f"crop_page{page_num + 1}_{elev_str}.png"
                        img.save(filename)
                        print(f"Saved screenshot: {filename}")
                except Exception as img_e:
                    print(f"Warning: Could not generate screenshots: {img_e}")

    except Exception as e:
        print(f"Error: {e}")

    # Output JSON
    print("\n--- EXTRACTION RESULTS (JSON) ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("---------------------------------")
    
    end_time = time.time()
    print(f"Total Runtime: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    process_architectural_pdf("test.pdf")