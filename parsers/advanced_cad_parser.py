import ezdxf
from ezdxf import recover, DXFError
import numpy as np
from shapely.geometry import LineString, Polygon, Point, MultiPolygon
from shapely.ops import unary_union
import math
import cv2
from pathlib import Path

class AdvancedCADParser:
    def __init__(self):
        self.scale_factor = 1.0
        self.unit_conversion = 1.0
        self.main_sheet_bounds = None
        
    def parse_multi_format(self, file_path):
        """Parse DXF/DWG/PDF with multi-sheet support and layer-aware extraction"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.dxf', '.dwg']:
            return self._parse_cad_file(file_path)
        elif file_ext == '.pdf':
            return self._parse_pdf_file(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_ext}")
    
    def _parse_cad_file(self, file_path):
        """Advanced CAD parsing with multi-sheet detection"""
        try:
            doc, auditor = recover.readfile(file_path)
            if auditor.has_errors:
                print(f"Fixed {len(auditor.errors)} CAD errors")
        except (IOError, DXFError) as e:
            raise Exception(f"CAD parsing failed: {e}")

        self._detect_scale_and_units(doc)
        
        # Extract from all layouts and identify main floor plan
        all_sheets = {}
        for layout_name in doc.layout_names():
            layout = doc.layouts.get(layout_name)
            entities = self._extract_layout_entities(layout)
            if entities:
                all_sheets[layout_name] = entities
        
        # Add modelspace if exists
        modelspace_entities = self._extract_layout_entities(doc.modelspace())
        if modelspace_entities:
            all_sheets['MODEL'] = modelspace_entities
        
        # Identify main floor plan
        main_sheet = self._identify_main_floor_plan(all_sheets)
        
        return self._classify_architectural_elements(main_sheet)
    
    def _parse_pdf_file(self, file_path):
        """Parse PDF with multi-page support"""
        import fitz  # PyMuPDF
        
        doc = fitz.open(file_path)
        all_pages = {}
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Extract vector graphics
            paths = page.get_drawings()
            entities = self._convert_pdf_paths_to_entities(paths)
            
            if entities:
                all_pages[f'Page_{page_num + 1}'] = entities
        
        doc.close()
        
        # Identify main floor plan page
        main_page = self._identify_main_floor_plan(all_pages)
        
        return self._classify_architectural_elements(main_page)
    
    def _detect_scale_and_units(self, doc):
        """Auto-detect drawing scale and units with high precision"""
        try:
            header = doc.header
            
            # Unit detection
            if '$INSUNITS' in header:
                units = header['$INSUNITS']
                unit_map = {
                    1: 0.0254,    # Inches to meters
                    2: 0.3048,    # Feet to meters
                    4: 1.0,       # Millimeters to meters (scaled)
                    5: 0.01,      # Centimeters to meters
                    6: 1.0,       # Meters
                    14: 0.001     # Micrometers to meters
                }
                self.unit_conversion = unit_map.get(units, 1.0)
            
            # Scale detection from dimension entities
            self._detect_scale_from_dimensions(doc)
            
        except Exception:
            self.unit_conversion = 1.0
            self.scale_factor = 1.0
    
    def _detect_scale_from_dimensions(self, doc):
        """Detect scale from dimension entities"""
        dimensions = []
        
        for layout_name in doc.layout_names():
            layout = doc.layouts.get(layout_name)
            for entity in layout:
                if entity.dxftype().startswith('DIMENSION'):
                    try:
                        dim_text = entity.dxf.text if hasattr(entity.dxf, 'text') else ''
                        if dim_text and any(char.isdigit() for char in dim_text):
                            dimensions.append(dim_text)
                    except:
                        continue
        
        # Analyze dimensions to detect scale
        if dimensions:
            # Look for typical architectural dimensions
            typical_values = [2.4, 2.5, 2.7, 3.0, 3.6, 4.0, 5.0, 6.0]  # Common room dimensions
            for dim in dimensions[:5]:  # Check first 5 dimensions
                try:
                    value = float(''.join(filter(str.isdigit, dim.replace('.', '1', 1))))
                    if value > 100:  # Likely in mm or cm
                        self.scale_factor = 0.001 if value > 1000 else 0.01
                        break
                except:
                    continue
    
    def _extract_layout_entities(self, layout):
        """Extract entities with enhanced geometric data"""
        entities = []
        
        for entity in layout:
            entity_data = self._extract_enhanced_entity_data(entity)
            if entity_data:
                entities.append(entity_data)
        
        return entities
    
    def _extract_enhanced_entity_data(self, entity):
        """Extract comprehensive geometric and architectural data"""
        entity_type = entity.dxftype()
        layer = getattr(entity.dxf, 'layer', '0').upper()
        color = getattr(entity.dxf, 'color', 256)
        linetype = getattr(entity.dxf, 'linetype', 'CONTINUOUS')
        lineweight = getattr(entity.dxf, 'lineweight', -1)
        
        data = {
            'type': entity_type,
            'layer': layer,
            'color': color,
            'linetype': linetype,
            'lineweight': lineweight,
            'architectural_type': None
        }
        
        # Enhanced entity extraction
        if entity_type == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            data.update({
                'start': self._convert_point(start),
                'end': self._convert_point(end),
                'length': self._convert_distance(start.distance(end))
            })
            
        elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
            points = self._extract_polyline_points(entity)
            data.update({
                'points': points,
                'is_closed': entity.is_closed,
                'area': self._calculate_polygon_area(points) if entity.is_closed else 0
            })
            
        elif entity_type == 'CIRCLE':
            center = entity.dxf.center
            radius = entity.dxf.radius
            data.update({
                'center': self._convert_point(center),
                'radius': self._convert_distance(radius),
                'area': math.pi * (self._convert_distance(radius) ** 2)
            })
            
        elif entity_type == 'ARC':
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            
            data.update({
                'center': self._convert_point(center),
                'radius': self._convert_distance(radius),
                'start_angle': start_angle,
                'end_angle': end_angle,
                'arc_length': self._calculate_arc_length(radius, start_angle, end_angle)
            })
            
        elif entity_type == 'HATCH':
            paths = self._extract_hatch_boundaries(entity)
            data.update({
                'paths': paths,
                'pattern': getattr(entity.dxf, 'pattern_name', 'SOLID'),
                'area': self._calculate_hatch_area(paths)
            })
            
        elif entity_type in ['TEXT', 'MTEXT']:
            insert = getattr(entity.dxf, 'insert', (0, 0, 0))
            text_content = getattr(entity.dxf, 'text', '')
            height = getattr(entity.dxf, 'height', 1)
            
            data.update({
                'text': text_content,
                'position': self._convert_point(insert),
                'height': self._convert_distance(height),
                'rotation': getattr(entity.dxf, 'rotation', 0)
            })
        
        # Classify architectural type
        data['architectural_type'] = self._classify_entity_architectural_type(data)
        
        return data if self._is_valid_entity(data) else None
    
    def _convert_point(self, point):
        """Convert point with scale and unit conversion"""
        if hasattr(point, 'x'):
            return (point.x * self.unit_conversion * self.scale_factor,
                   point.y * self.unit_conversion * self.scale_factor)
        else:
            return (point[0] * self.unit_conversion * self.scale_factor,
                   point[1] * self.unit_conversion * self.scale_factor)
    
    def _convert_distance(self, distance):
        """Convert distance with scale and unit conversion"""
        return distance * self.unit_conversion * self.scale_factor
    
    def _extract_polyline_points(self, entity):
        """Extract polyline points with proper conversion"""
        points = []
        
        if entity.dxftype() == 'LWPOLYLINE':
            for point in entity.get_points('xy'):
                points.append(self._convert_point(point))
        else:  # POLYLINE
            for vertex in entity.vertices:
                points.append(self._convert_point(vertex.dxf.location))
        
        return points
    
    def _calculate_polygon_area(self, points):
        """Calculate polygon area using shoelace formula"""
        if len(points) < 3:
            return 0
        
        area = 0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        
        return abs(area) / 2
    
    def _calculate_arc_length(self, radius, start_angle, end_angle):
        """Calculate arc length"""
        angle_diff = abs(end_angle - start_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        return self._convert_distance(radius) * math.radians(angle_diff)
    
    def _extract_hatch_boundaries(self, entity):
        """Extract hatch boundary paths"""
        paths = []
        
        for path in entity.paths:
            path_points = []
            
            if hasattr(path, 'edges'):
                for edge in path.edges:
                    if edge.type == 'LineEdge':
                        path_points.extend([
                            self._convert_point(edge.start),
                            self._convert_point(edge.end)
                        ])
                    elif edge.type == 'ArcEdge':
                        # Convert arc to line segments
                        arc_points = self._arc_to_points(edge)
                        path_points.extend(arc_points)
            
            if path_points:
                paths.append(path_points)
        
        return paths
    
    def _arc_to_points(self, arc_edge, segments=16):
        """Convert arc edge to point sequence"""
        center = self._convert_point(arc_edge.center)
        radius = self._convert_distance(arc_edge.radius)
        start_angle = math.radians(arc_edge.start_angle)
        end_angle = math.radians(arc_edge.end_angle)
        
        points = []
        angle_step = (end_angle - start_angle) / segments
        
        for i in range(segments + 1):
            angle = start_angle + i * angle_step
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
        
        return points
    
    def _calculate_hatch_area(self, paths):
        """Calculate total area of hatch paths"""
        total_area = 0
        
        for path in paths:
            if len(path) >= 3:
                total_area += self._calculate_polygon_area(path)
        
        return total_area
    
    def _classify_entity_architectural_type(self, entity_data):
        """Classify entity by architectural function"""
        layer = entity_data['layer']
        entity_type = entity_data['type']
        color = entity_data['color']
        lineweight = entity_data.get('lineweight', -1)
        
        # Wall classification
        if (any(keyword in layer for keyword in ['WALL', 'MUR', 'CLOISON', 'PARTITION']) or
            lineweight > 50 or
            (entity_type == 'LINE' and entity_data.get('length', 0) > 1.0)):
            return 'wall'
        
        # Door classification
        elif (any(keyword in layer for keyword in ['DOOR', 'PORTE']) or
              entity_type == 'ARC' or
              (entity_type == 'CIRCLE' and entity_data.get('radius', 0) < 1.5)):
            return 'door'
        
        # Window classification
        elif any(keyword in layer for keyword in ['WINDOW', 'FENETRE', 'WIN']):
            return 'window'
        
        # Restricted zone classification
        elif (any(keyword in layer for keyword in ['RESTRICT', 'PROHIB', 'NO_ENTRY', 'BLUE']) or
              color == 5 or  # Blue color
              (entity_type == 'HATCH' and 'BLUE' in layer)):
            return 'restricted_zone'
        
        # Entrance/exit classification
        elif (any(keyword in layer for keyword in ['ENTRANCE', 'EXIT', 'ENTREE', 'SORTIE']) or
              color == 1):  # Red color
            return 'entrance'
        
        # Dimension classification
        elif entity_type.startswith('DIMENSION') or 'DIM' in layer:
            return 'dimension'
        
        # Text classification
        elif entity_type in ['TEXT', 'MTEXT']:
            return 'text'
        
        return 'other'
    
    def _is_valid_entity(self, entity_data):
        """Check if entity contains valid geometric data"""
        return any(key in entity_data for key in 
                  ['start', 'points', 'center', 'paths', 'text'])
    
    def _identify_main_floor_plan(self, all_sheets):
        """Identify the main floor plan from multiple sheets"""
        if not all_sheets:
            return []
        
        # Score each sheet based on architectural content
        sheet_scores = {}
        
        for sheet_name, entities in all_sheets.items():
            score = 0
            wall_count = 0
            door_count = 0
            total_length = 0
            
            for entity in entities:
                arch_type = entity.get('architectural_type')
                
                if arch_type == 'wall':
                    wall_count += 1
                    score += 10
                    total_length += entity.get('length', 0)
                elif arch_type == 'door':
                    door_count += 1
                    score += 5
                elif arch_type in ['window', 'entrance']:
                    score += 3
                elif arch_type == 'restricted_zone':
                    score += 2
            
            # Bonus for balanced architectural elements
            if wall_count > 10 and door_count > 2:
                score += 50
            
            # Bonus for reasonable total wall length
            if 50 < total_length < 500:
                score += 30
            
            sheet_scores[sheet_name] = score
        
        # Return the sheet with highest score
        best_sheet = max(sheet_scores.items(), key=lambda x: x[1])
        print(f"Selected main floor plan: {best_sheet[0]} (score: {best_sheet[1]})")
        
        return all_sheets[best_sheet[0]]
    
    def _classify_architectural_elements(self, entities):
        """Final classification of architectural elements"""
        classified = {
            'walls': [],
            'doors': [],
            'windows': [],
            'restricted_zones': [],
            'entrances': [],
            'dimensions': [],
            'text': [],
            'other': []
        }
        
        for entity in entities:
            arch_type = entity.get('architectural_type', 'other')
            
            if arch_type == 'wall':
                classified['walls'].append(entity)
            elif arch_type == 'door':
                classified['doors'].append(entity)
            elif arch_type == 'window':
                classified['windows'].append(entity)
            elif arch_type == 'restricted_zone':
                classified['restricted_zones'].append(entity)
            elif arch_type == 'entrance':
                classified['entrances'].append(entity)
            elif arch_type == 'dimension':
                classified['dimensions'].append(entity)
            elif arch_type == 'text':
                classified['text'].append(entity)
            else:
                classified['other'].append(entity)
        
        # Post-process and validate classifications
        self._validate_and_refine_classifications(classified)
        
        return classified
    
    def _validate_and_refine_classifications(self, classified):
        """Validate and refine element classifications"""
        # Merge nearby wall segments
        classified['walls'] = self._merge_wall_segments(classified['walls'])
        
        # Detect door swings from arcs
        classified['doors'] = self._detect_door_swings(classified['doors'])
        
        # Validate restricted zones
        classified['restricted_zones'] = self._validate_restricted_zones(classified['restricted_zones'])
    
    def _merge_wall_segments(self, walls):
        """Merge nearby wall segments into continuous walls"""
        # Implementation for merging wall segments
        return walls  # Simplified for now
    
    def _detect_door_swings(self, doors):
        """Detect and classify door swing directions"""
        for door in doors:
            if door['type'] == 'ARC':
                # Calculate swing direction from arc
                start_angle = door.get('start_angle', 0)
                end_angle = door.get('end_angle', 0)
                
                swing_angle = abs(end_angle - start_angle)
                if swing_angle > 180:
                    swing_angle = 360 - swing_angle
                
                door['swing_direction'] = 'left' if end_angle > start_angle else 'right'
                door['swing_angle'] = swing_angle
        
        return doors
    
    def _validate_restricted_zones(self, zones):
        """Validate and clean restricted zone geometries"""
        valid_zones = []
        
        for zone in zones:
            if zone['type'] == 'HATCH' and zone.get('area', 0) > 1.0:  # Minimum 1m² area
                valid_zones.append(zone)
            elif zone['type'] in ['LWPOLYLINE', 'POLYLINE'] and zone.get('area', 0) > 1.0:
                valid_zones.append(zone)
        
        return valid_zones

def parse_multi_format_cad(file_path):
    """Main parsing function for production use"""
    parser = AdvancedCADParser()
    return parser.parse_multi_format(file_path)