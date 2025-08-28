import pdfplumber
import cv2
import numpy as np
from PIL import Image
import io
from shapely.geometry import LineString, Polygon
from skimage import measure, morphology
from scipy import ndimage

class PDFParser:
    def __init__(self):
        self.dpi = 300
        self.scale_factor = 1.0
        
    def parse_pdf(self, file_path):
        """Advanced PDF parsing with multi-sheet support and element detection"""
        print(f"Parsing PDF file: {file_path}")
        
        classified_entities = {
            'walls': [],
            'doors': [],
            'windows': [],
            'restricted_zones': [],
            'entrances': [],
            'dimensions': [],
            'other': []
        }
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    print(f"Processing page {page_num + 1}/{len(pdf.pages)}")
                    
                    # Extract vector graphics first
                    vector_entities = self._extract_vector_graphics(page)
                    
                    # Convert page to image for raster analysis
                    page_image = page.to_image(resolution=self.dpi)
                    img_array = np.array(page_image.original)
                    
                    # Extract raster elements
                    raster_entities = self._extract_raster_elements(img_array)
                    
                    # Combine and classify
                    page_entities = self._merge_and_classify(vector_entities, raster_entities)
                    
                    # Add to main collection
                    for category, entities in page_entities.items():
                        classified_entities[category].extend(entities)
                        
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            
        return classified_entities
    
    def _extract_vector_graphics(self, page):
        """Extract vector graphics from PDF page"""
        entities = []
        
        # Extract lines
        for line in page.lines:
            entities.append({
                'type': 'LINE',
                'start': (line['x0'], page.height - line['y1']),
                'end': (line['x1'], page.height - line['y0']),
                'width': line.get('linewidth', 1),
                'layer': 'PDF_LINES'
            })
        
        # Extract rectangles
        for rect in page.rects:
            points = [
                (rect['x0'], page.height - rect['y1']),
                (rect['x1'], page.height - rect['y1']),
                (rect['x1'], page.height - rect['y0']),
                (rect['x0'], page.height - rect['y0'])
            ]
            entities.append({
                'type': 'LWPOLYLINE',
                'points': points,
                'is_closed': True,
                'layer': 'PDF_RECTS'
            })
        
        # Extract curves (approximate as polylines)
        for curve in page.curves:
            if len(curve['pts']) >= 2:
                points = [(pt[0], page.height - pt[1]) for pt in curve['pts']]
                entities.append({
                    'type': 'LWPOLYLINE',
                    'points': points,
                    'is_closed': False,
                    'layer': 'PDF_CURVES'
                })
        
        return entities
    
    def _extract_raster_elements(self, img_array):
        """Extract elements from rasterized PDF image using computer vision"""
        entities = []
        
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        # Detect different colored regions
        entities.extend(self._detect_colored_regions(img_array))
        
        # Detect lines using Hough transform
        entities.extend(self._detect_lines(gray))
        
        # Detect circular elements (doors/windows)
        entities.extend(self._detect_circles(gray))
        
        return entities
    
    def _detect_colored_regions(self, img_array):
        """Detect colored regions that might represent restricted zones or entrances"""
        entities = []
        
        if len(img_array.shape) != 3:
            return entities
            
        # Define color ranges for different elements
        color_ranges = {
            'restricted_zones': {
                'lower': np.array([100, 150, 200]),  # Light blue
                'upper': np.array([150, 200, 255])
            },
            'entrances': {
                'lower': np.array([200, 100, 100]),  # Light red
                'upper': np.array([255, 150, 150])
            }
        }
        
        for category, color_range in color_ranges.items():
            mask = cv2.inRange(img_array, color_range['lower'], color_range['upper'])
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                if cv2.contourArea(contour) > 100:  # Filter small noise
                    # Approximate contour to polygon
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    points = [(pt[0][0], pt[0][1]) for pt in approx]
                    
                    entities.append({
                        'type': 'HATCH',
                        'paths': [points],
                        'layer': f'PDF_{category.upper()}',
                        'category': category
                    })
        
        return entities
    
    def _detect_lines(self, gray):
        """Detect lines using Hough transform"""
        entities = []
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Hough line detection
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                               minLineLength=50, maxLineGap=10)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                entities.append({
                    'type': 'LINE',
                    'start': (x1, y1),
                    'end': (x2, y2),
                    'layer': 'PDF_DETECTED_LINES'
                })
        
        return entities
    
    def _detect_circles(self, gray):
        """Detect circular elements (doors, windows)"""
        entities = []
        
        # Hough circle detection
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                  param1=50, param2=30, minRadius=10, maxRadius=100)
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                entities.append({
                    'type': 'CIRCLE',
                    'center': (x, y),
                    'radius': r,
                    'layer': 'PDF_CIRCLES'
                })
        
        return entities
    
    def _merge_and_classify(self, vector_entities, raster_entities):
        """Merge vector and raster entities and classify them"""
        all_entities = vector_entities + raster_entities
        
        classified = {
            'walls': [],
            'doors': [],
            'windows': [],
            'restricted_zones': [],
            'entrances': [],
            'dimensions': [],
            'other': []
        }
        
        for entity in all_entities:
            layer = entity.get('layer', '').upper()
            entity_type = entity.get('type', '')
            category = entity.get('category', '')
            
            # Classification logic
            if 'RESTRICTED' in layer or category == 'restricted_zones':
                classified['restricted_zones'].append(entity)
            elif 'ENTRANCE' in layer or category == 'entrances':
                classified['entrances'].append(entity)
            elif entity_type == 'CIRCLE' or 'CURVE' in layer:
                classified['doors'].append(entity)
            elif 'LINE' in layer and entity.get('width', 1) > 2:
                classified['walls'].append(entity)
            else:
                classified['other'].append(entity)
        
        return classified

def parse_pdf(file_path):
    """Main parsing function for backward compatibility"""
    parser = PDFParser()
    return parser.parse_pdf(file_path)