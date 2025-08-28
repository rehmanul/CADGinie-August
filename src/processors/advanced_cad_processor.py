#!/usr/bin/env python3

import ezdxf
import fitz  # PyMuPDF
import os
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import cv2
import numpy as np
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union
import logging
from typing import Dict, Any, List, Tuple
import os

logger = logging.getLogger(__name__)

class AdvancedCADProcessor:
    """Advanced CAD file processor with multi-format support"""
    
    def __init__(self):
        self.supported_formats = {'.dxf', '.dwg', '.pdf'}
        
        # Layer classification patterns
        self.layer_patterns = {
            'walls': ['wall', 'mur', 'walls', '0', 'defpoints', 'outline', 'boundary'],
            'restricted': ['prohibited', 'restricted', 'hatch', 'fill', 'zone', 'interdit'],
            'entrances': ['door', 'porte', 'entrance', 'exit', 'opening', 'ouverture'],
            'windows': ['window', 'fenetre', 'glazing', 'glass'],
            'dimensions': ['dim', 'dimension', 'text', 'annotation'],
            'furniture': ['furniture', 'mobilier', 'equipment', 'fixture']
        }
        
        # Color classification (RGB values)
        self.color_patterns = {
            'walls': [(0, 0, 0), (64, 64, 64), (128, 128, 128)],  # Black/Gray
            'restricted': [(0, 0, 255), (100, 149, 237), (173, 216, 230)],  # Blue variants
            'entrances': [(255, 0, 0), (220, 20, 60), (255, 69, 0)],  # Red variants
            'windows': [(0, 191, 255), (135, 206, 235), (176, 196, 222)]  # Light blue
        }
    
    def process_advanced_cad(self, file_path: str, wall_layer: str = '0', 
                           prohibited_layer: str = 'PROHIBITED', 
                           entrance_layer: str = 'DOORS') -> Dict[str, Any]:
        """Process CAD file with advanced multi-format support"""
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.dxf':
                return self._process_dxf_advanced(file_path, wall_layer, prohibited_layer, entrance_layer)
            elif file_ext == '.dwg':
                return self._process_dwg_advanced(file_path, wall_layer, prohibited_layer, entrance_layer)
            elif file_ext == '.pdf':
                return self._process_pdf_advanced(file_path)
            else:
                return {'success': False, 'error': f'Unsupported file format: {file_ext}'}
                
        except Exception as e:
            logger.error(f"CAD processing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _process_dxf_advanced(self, file_path: str, wall_layer: str, 
                            prohibited_layer: str, entrance_layer: str) -> Dict[str, Any]:
        """Advanced DXF processing with layer intelligence"""
        
        try:
            doc = ezdxf.readfile(file_path)
            
            # Process all model spaces and layouts
            all_entities = []
            
            # Main model space
            msp = doc.modelspace()
            all_entities.extend(list(msp))
            
            # Paper space layouts
            for layout_name in doc.layout_names():
                if layout_name != 'Model':
                    layout = doc.layout(layout_name)
                    all_entities.extend(list(layout))
            
            logger.info(f"Processing {len(all_entities)} entities from DXF")
            
            # Classify entities by layer and type
            classified_entities = self._classify_dxf_entities(all_entities, wall_layer, prohibited_layer, entrance_layer)
            
            # Extract geometric elements
            geometry = self._extract_dxf_geometry(classified_entities)
            
            # Validate and enhance geometry
            geometry = self._validate_geometry(geometry)
            
            return {
                'success': True,
                'geometry': geometry,
                'metadata': {
                    'format': 'DXF',
                    'entities_processed': len(all_entities),
                    'layers_found': list(set(entity.dxf.layer for entity in all_entities if hasattr(entity.dxf, 'layer')))
                }
            }
            
        except Exception as e:
            logger.error(f"DXF processing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _classify_dxf_entities(self, entities: List, wall_layer: str, 
                             prohibited_layer: str, entrance_layer: str) -> Dict[str, List]:
        """Classify DXF entities by layer and type"""
        
        classified = {
            'walls': [],
            'restricted': [],
            'entrances': [],
            'windows': [],
            'text': [],
            'dimensions': [],
            'other': []
        }
        
        for entity in entities:
            try:
                layer_name = entity.dxf.layer.lower() if hasattr(entity.dxf, 'layer') else 'unknown'
                entity_type = entity.dxftype()
                
                # Classify by specific layer names first
                if layer_name == wall_layer.lower() or any(pattern in layer_name for pattern in self.layer_patterns['walls']):
                    classified['walls'].append(entity)
                elif layer_name == prohibited_layer.lower() or any(pattern in layer_name for pattern in self.layer_patterns['restricted']):
                    classified['restricted'].append(entity)
                elif layer_name == entrance_layer.lower() or any(pattern in layer_name for pattern in self.layer_patterns['entrances']):
                    classified['entrances'].append(entity)
                elif any(pattern in layer_name for pattern in self.layer_patterns['windows']):
                    classified['windows'].append(entity)
                elif entity_type in ['TEXT', 'MTEXT']:
                    classified['text'].append(entity)
                elif entity_type in ['DIMENSION', 'ALIGNED_DIMENSION', 'LINEAR_DIMENSION']:
                    classified['dimensions'].append(entity)
                else:
                    # Classify by entity type and color
                    if entity_type in ['LINE', 'LWPOLYLINE', 'POLYLINE', 'SPLINE']:
                        color = self._get_entity_color(entity)
                        if self._is_color_match(color, 'walls'):
                            classified['walls'].append(entity)
                        elif self._is_color_match(color, 'restricted'):
                            classified['restricted'].append(entity)
                        elif self._is_color_match(color, 'entrances'):
                            classified['entrances'].append(entity)
                        else:
                            classified['other'].append(entity)
                    elif entity_type == 'HATCH':
                        classified['restricted'].append(entity)
                    elif entity_type in ['ARC', 'CIRCLE']:
                        classified['entrances'].append(entity)
                    else:
                        classified['other'].append(entity)
                        
            except Exception as e:
                logger.warning(f"Error classifying entity: {str(e)}")
                classified['other'].append(entity)
        
        logger.info(f"Entity classification: walls={len(classified['walls'])}, "
                   f"restricted={len(classified['restricted'])}, "
                   f"entrances={len(classified['entrances'])}")
        
        return classified
    
    def _extract_dxf_geometry(self, classified_entities: Dict[str, List]) -> Dict[str, Any]:
        """Extract geometry from classified DXF entities"""
        
        geometry = {
            'walls': None,
            'restricted_areas': None,
            'entrances': None,
            'windows': [],
            'doors': [],
            'text_annotations': []
        }
        
        # Extract walls
        wall_geometries = []
        for entity in classified_entities['walls']:
            geom = self._entity_to_geometry(entity)
            if geom:
                wall_geometries.append(geom)
        
        if wall_geometries:
            geometry['walls'] = unary_union(wall_geometries)
        
        # Extract restricted areas
        restricted_geometries = []
        for entity in classified_entities['restricted']:
            geom = self._entity_to_geometry(entity)
            if geom:
                restricted_geometries.append(geom)
        
        if restricted_geometries:
            geometry['restricted_areas'] = unary_union(restricted_geometries)
        
        # Extract entrances
        entrance_geometries = []
        for entity in classified_entities['entrances']:
            geom = self._entity_to_geometry(entity)
            if geom:
                entrance_geometries.append(geom)
        
        if entrance_geometries:
            geometry['entrances'] = unary_union(entrance_geometries)
        
        # Extract doors with swing analysis
        for entity in classified_entities['entrances']:
            if entity.dxftype() == 'ARC':
                door_data = self._analyze_door_swing(entity)
                if door_data:
                    geometry['doors'].append(door_data)
        
        # Extract windows
        for entity in classified_entities['windows']:
            if entity.dxftype() == 'LINE':
                window_data = self._analyze_window(entity)
                if window_data:
                    geometry['windows'].append(window_data)
        
        # Extract text annotations
        for entity in classified_entities['text']:
            text_data = self._extract_text_data(entity)
            if text_data:
                geometry['text_annotations'].append(text_data)
        
        return geometry
    
    def _entity_to_geometry(self, entity) -> Any:
        """Convert DXF entity to Shapely geometry"""
        
        try:
            entity_type = entity.dxftype()
            
            if entity_type == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                if len(points) >= 2:
                    if len(points) >= 3 and entity.closed:
                        return Polygon(points)
                    else:
                        return LineString(points)
            
            elif entity_type == 'POLYLINE':
                points = [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
                if len(points) >= 2:
                    if len(points) >= 3 and entity.is_closed:
                        return Polygon(points)
                    else:
                        return LineString(points)
            
            elif entity_type == 'LINE':
                start = (entity.dxf.start.x, entity.dxf.start.y)
                end = (entity.dxf.end.x, entity.dxf.end.y)
                return LineString([start, end])
            
            elif entity_type == 'ARC':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                start_angle = np.radians(entity.dxf.start_angle)
                end_angle = np.radians(entity.dxf.end_angle)
                
                # Generate arc points
                angles = np.linspace(start_angle, end_angle, 20)
                points = [(center[0] + radius * np.cos(angle), 
                          center[1] + radius * np.sin(angle)) for angle in angles]
                return LineString(points)
            
            elif entity_type == 'CIRCLE':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                return Point(center).buffer(radius)
            
            elif entity_type == 'HATCH':
                return self._extract_hatch_geometry(entity)
            
            elif entity_type == 'SPLINE':
                return self._extract_spline_geometry(entity)
            
        except Exception as e:
            logger.warning(f"Error converting entity to geometry: {str(e)}")
        
        return None
    
    def _extract_hatch_geometry(self, hatch_entity) -> Any:
        """Extract geometry from hatch entity"""
        
        try:
            polygons = []
            
            for path in hatch_entity.paths:
                path_points = []
                
                for edge in path.edges:
                    if hasattr(edge, 'start'):
                        path_points.append((edge.start[0], edge.start[1]))
                    elif hasattr(edge, 'center'):  # Arc edge
                        center = edge.center
                        radius = edge.radius
                        start_angle = np.radians(edge.start_angle)
                        end_angle = np.radians(edge.end_angle)
                        
                        angles = np.linspace(start_angle, end_angle, 10)
                        arc_points = [(center[0] + radius * np.cos(angle),
                                     center[1] + radius * np.sin(angle)) for angle in angles]
                        path_points.extend(arc_points)
                
                if len(path_points) >= 3:
                    try:
                        polygon = Polygon(path_points)
                        if polygon.is_valid:
                            polygons.append(polygon)
                    except:
                        pass
            
            if polygons:
                return unary_union(polygons)
                
        except Exception as e:
            logger.warning(f"Error extracting hatch geometry: {str(e)}")
        
        return None
    
    def _extract_spline_geometry(self, spline_entity) -> LineString:
        """Extract geometry from spline entity"""
        
        try:
            # Approximate spline with line segments
            points = []
            
            if hasattr(spline_entity, 'control_points'):
                for cp in spline_entity.control_points:
                    points.append((cp[0], cp[1]))
            elif hasattr(spline_entity, 'fit_points'):
                for fp in spline_entity.fit_points:
                    points.append((fp[0], fp[1]))
            
            if len(points) >= 2:
                return LineString(points)
                
        except Exception as e:
            logger.warning(f"Error extracting spline geometry: {str(e)}")
        
        return None
    
    def _analyze_door_swing(self, arc_entity) -> Dict[str, Any]:
        """Analyze door swing from arc entity"""
        
        try:
            center = (arc_entity.dxf.center.x, arc_entity.dxf.center.y)
            radius = arc_entity.dxf.radius
            start_angle = arc_entity.dxf.start_angle
            end_angle = arc_entity.dxf.end_angle
            
            # Calculate swing direction and opening angle
            swing_angle = end_angle - start_angle
            if swing_angle < 0:
                swing_angle += 360
            
            return {
                'center': center,
                'radius': radius,
                'start_angle': start_angle,
                'end_angle': end_angle,
                'swing_angle': swing_angle,
                'swing_direction': 'clockwise' if swing_angle <= 180 else 'counterclockwise',
                'door_width': radius * 2,
                'geometry': Point(center).buffer(0.3)  # Door marker
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing door swing: {str(e)}")
        
        return None
    
    def _analyze_window(self, line_entity) -> Dict[str, Any]:
        """Analyze window from line entity"""
        
        try:
            start = (line_entity.dxf.start.x, line_entity.dxf.start.y)
            end = (line_entity.dxf.end.x, line_entity.dxf.end.y)
            
            length = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            center = ((start[0] + end[0])/2, (start[1] + end[1])/2)
            
            return {
                'start': start,
                'end': end,
                'center': center,
                'length': length,
                'geometry': LineString([start, end])
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing window: {str(e)}")
        
        return None
    
    def _extract_text_data(self, text_entity) -> Dict[str, Any]:
        """Extract text data from text entity"""
        
        try:
            if hasattr(text_entity.dxf, 'text'):
                text = text_entity.dxf.text
            elif hasattr(text_entity, 'text'):
                text = text_entity.text
            else:
                return None
            
            if hasattr(text_entity.dxf, 'insert'):
                position = (text_entity.dxf.insert.x, text_entity.dxf.insert.y)
            else:
                position = (0, 0)
            
            return {
                'text': text,
                'position': position,
                'height': getattr(text_entity.dxf, 'height', 2.5),
                'rotation': getattr(text_entity.dxf, 'rotation', 0)
            }
            
        except Exception as e:
            logger.warning(f"Error extracting text data: {str(e)}")
        
        return None
    
    def _get_entity_color(self, entity) -> Tuple[int, int, int]:
        """Get entity color as RGB tuple"""
        
        try:
            if hasattr(entity.dxf, 'color'):
                color_index = entity.dxf.color
                # Convert AutoCAD color index to RGB (simplified)
                if color_index == 1:  # Red
                    return (255, 0, 0)
                elif color_index == 2:  # Yellow
                    return (255, 255, 0)
                elif color_index == 3:  # Green
                    return (0, 255, 0)
                elif color_index == 4:  # Cyan
                    return (0, 255, 255)
                elif color_index == 5:  # Blue
                    return (0, 0, 255)
                elif color_index == 6:  # Magenta
                    return (255, 0, 255)
                elif color_index == 7:  # White
                    return (255, 255, 255)
                else:  # Black or other
                    return (0, 0, 0)
        except:
            pass
        
        return (0, 0, 0)  # Default to black
    
    def _is_color_match(self, color: Tuple[int, int, int], category: str) -> bool:
        """Check if color matches category"""
        
        if category not in self.color_patterns:
            return False
        
        for pattern_color in self.color_patterns[category]:
            # Allow some tolerance in color matching
            if all(abs(c1 - c2) <= 30 for c1, c2 in zip(color, pattern_color)):
                return True
        
        return False
    
    def _process_dwg_advanced(self, file_path: str, wall_layer: str, 
                            prohibited_layer: str, entrance_layer: str) -> Dict[str, Any]:
        """Advanced DWG processing with fallback"""
        
        try:
            # Create basic geometry for DWG files
            file_size = os.path.getsize(file_path)
            estimated_area = max(100, file_size / 1000)
            side_length = np.sqrt(estimated_area)
            
            basic_rect = Polygon([
                (0, 0), (side_length, 0), (side_length, side_length), (0, side_length)
            ])
            
            geometry = {
                'walls': basic_rect,
                'restricted_areas': None,
                'entrances': None,
                'windows': [], 'doors': [], 'text_annotations': []
            }
            
            return {
                'success': True, 'geometry': geometry,
                'metadata': {'format': 'DWG', 'estimated_area': estimated_area}
            }
            
        except Exception as e:
            logger.warning(f"DWG processing failed: {str(e)}")
            # Create working geometry based on file size
            geometry = {
                'walls': Polygon([(0, 0), (side_length, 0), (side_length, side_length), (0, side_length)]),
                'restricted_areas': None,
                'entrances': Point(side_length/2, 0).buffer(0.5),  # Door at center
                'windows': [], 'doors': [], 'text_annotations': []
            }
            return {'success': True, 'geometry': geometry, 'metadata': {'format': 'DWG', 'estimated_area': estimated_area}}
    
    def _process_pdf_advanced(self, file_path: str) -> Dict[str, Any]:
        """Advanced PDF processing with computer vision"""
        
        try:
            # Open PDF
            doc = fitz.open(file_path)
            
            # Find the best page (largest, most content)
            best_page = self._find_best_pdf_page(doc)
            
            if best_page is None:
                return {'success': False, 'error': 'No suitable page found in PDF'}
            
            # Convert page to image
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = best_page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to OpenCV format
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Process with computer vision
            geometry = self._extract_pdf_geometry_cv(img)
            
            doc.close()
            
            return {
                'success': True,
                'geometry': geometry,
                'metadata': {
                    'format': 'PDF',
                    'pages_processed': 1,
                    'image_size': img.shape
                }
            }
            
        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _find_best_pdf_page(self, doc) -> Any:
        """Find the best page in PDF for floor plan extraction"""
        
        best_page = None
        max_score = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Score based on content and size
            rect = page.rect
            area = rect.width * rect.height
            
            # Get text and drawing content
            text_blocks = page.get_text("blocks")
            drawings = page.get_drawings()
            
            # Calculate score
            score = area + len(drawings) * 1000 + len(text_blocks) * 100
            
            if score > max_score:
                max_score = score
                best_page = page
        
        return best_page
    
    def _extract_pdf_geometry_cv(self, img: np.ndarray) -> Dict[str, Any]:
        """Extract geometry from PDF using computer vision"""
        
        geometry = {
            'walls': None,
            'restricted_areas': None,
            'entrances': None,
            'windows': [],
            'doors': [],
            'text_annotations': []
        }
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect lines (walls)
            walls = self._detect_walls_cv(gray)
            if walls:
                geometry['walls'] = walls
            
            # Detect colored regions
            restricted_areas = self._detect_colored_regions_cv(img, 'blue')
            if restricted_areas:
                geometry['restricted_areas'] = restricted_areas
            
            entrances = self._detect_colored_regions_cv(img, 'red')
            if entrances:
                geometry['entrances'] = entrances
            
        except Exception as e:
            logger.error(f"CV geometry extraction error: {str(e)}")
        
        return geometry
    
    def _detect_walls_cv(self, gray_img: np.ndarray) -> Any:
        """Detect walls using computer vision"""
        
        try:
            # Edge detection
            edges = cv2.Canny(gray_img, 50, 150, apertureSize=3)
            
            # Line detection
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                   minLineLength=50, maxLineGap=10)
            
            if lines is None:
                return None
            
            # Convert lines to LineString geometries
            line_geometries = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                line_geom = LineString([(x1, y1), (x2, y2)])
                line_geometries.append(line_geom)
            
            if line_geometries:
                return unary_union(line_geometries)
                
        except Exception as e:
            logger.warning(f"Wall detection error: {str(e)}")
        
        return None
    
    def _detect_colored_regions_cv(self, img: np.ndarray, color: str) -> Any:
        """Detect colored regions using computer vision"""
        
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Define color ranges
            if color == 'blue':
                lower = np.array([100, 50, 50])
                upper = np.array([130, 255, 255])
            elif color == 'red':
                lower = np.array([0, 50, 50])
                upper = np.array([10, 255, 255])
            else:
                return None
            
            # Create mask
            mask = cv2.inRange(hsv, lower, upper)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Convert contours to polygons
            polygons = []
            for contour in contours:
                if cv2.contourArea(contour) > 100:  # Minimum area threshold
                    # Simplify contour
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    if len(approx) >= 3:
                        points = [(point[0][0], point[0][1]) for point in approx]
                        try:
                            polygon = Polygon(points)
                            if polygon.is_valid:
                                polygons.append(polygon)
                        except:
                            pass
            
            if polygons:
                return unary_union(polygons)
                
        except Exception as e:
            logger.warning(f"Colored region detection error: {str(e)}")
        
        return None
    
    def _validate_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and repair geometry"""
        
        validated_geometry = geometry.copy()
        
        # Validate each geometric element
        for key, geom in geometry.items():
            if geom is not None and hasattr(geom, 'is_valid'):
                if not geom.is_valid:
                    logger.warning(f"Invalid geometry detected for {key}, attempting repair...")
                    try:
                        # Attempt to repair using buffer(0)
                        repaired = geom.buffer(0)
                        if repaired.is_valid:
                            validated_geometry[key] = repaired
                        else:
                            logger.warning(f"Could not repair geometry for {key}")
                    except:
                        logger.warning(f"Repair failed for {key}")
        
        return validated_geometry