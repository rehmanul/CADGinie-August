import ezdxf
from ezdxf import recover, DXFError
import numpy as np
from shapely.geometry import LineString, Polygon, Point
import math

class CADParser:
    def __init__(self):
        self.scale_factor = 1.0
        self.unit_conversion = 1.0
        
    def parse_dwg_dxf(self, file_path):
        """Advanced CAD file parsing with layer-aware extraction and element classification"""
        print(f"Parsing CAD file: {file_path}")
        
        try:
            doc, auditor = recover.readfile(file_path)
            if auditor.has_errors:
                print(f"Fixed {len(auditor.errors)} errors in CAD file")
        except (IOError, DXFError) as e:
            print(f"Error reading CAD file: {e}")
            return []

        # Auto-detect scale and units
        self._detect_scale_and_units(doc)
        
        # Extract entities from all layouts
        entities = []
        for layout_name in doc.layout_names():
            layout = doc.layouts.get(layout_name)
            if layout_name.upper() in ['MODEL', 'PLAN', 'FLOOR']:
                entities.extend(self._extract_layout_entities(layout))
        
        # If no specific layouts found, use modelspace
        if not entities:
            entities = self._extract_layout_entities(doc.modelspace())
            
        return self._classify_entities(entities)
    
    def _detect_scale_and_units(self, doc):
        """Auto-detect drawing scale and units"""
        try:
            header = doc.header
            if '$INSUNITS' in header:
                units = header['$INSUNITS']
                # Convert to meters
                unit_map = {1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0}
                self.unit_conversion = unit_map.get(units, 1.0) / 1000.0
        except:
            self.unit_conversion = 1.0
            
    def _extract_layout_entities(self, layout):
        """Extract geometric entities from a layout"""
        entities = []
        
        for entity in layout:
            entity_data = self._extract_entity_data(entity)
            if entity_data:
                entities.append(entity_data)
                
        return entities
    
    def _extract_entity_data(self, entity):
        """Extract comprehensive geometric data from DXF entity"""
        entity_type = entity.dxftype()
        layer = getattr(entity.dxf, 'layer', '0')
        color = getattr(entity.dxf, 'color', 256)
        
        data = {
            'type': entity_type,
            'layer': layer,
            'color': color,
            'linetype': getattr(entity.dxf, 'linetype', 'CONTINUOUS')
        }
        
        if entity_type == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            data.update({
                'start': (start.x * self.unit_conversion, start.y * self.unit_conversion),
                'end': (end.x * self.unit_conversion, end.y * self.unit_conversion)
            })
            
        elif entity_type in ['LWPOLYLINE', 'POLYLINE']:
            points = []
            if entity_type == 'LWPOLYLINE':
                points = [(p[0] * self.unit_conversion, p[1] * self.unit_conversion) 
                         for p in entity.get_points('xy')]
            else:
                points = [(v.dxf.location.x * self.unit_conversion, 
                          v.dxf.location.y * self.unit_conversion) 
                         for v in entity.vertices]
            
            data.update({
                'points': points,
                'is_closed': entity.is_closed,
                'width': getattr(entity.dxf, 'const_width', 0)
            })
            
        elif entity_type == 'CIRCLE':
            center = entity.dxf.center
            data.update({
                'center': (center.x * self.unit_conversion, center.y * self.unit_conversion),
                'radius': entity.dxf.radius * self.unit_conversion
            })
            
        elif entity_type == 'ARC':
            center = entity.dxf.center
            data.update({
                'center': (center.x * self.unit_conversion, center.y * self.unit_conversion),
                'radius': entity.dxf.radius * self.unit_conversion,
                'start_angle': entity.dxf.start_angle,
                'end_angle': entity.dxf.end_angle
            })
            
        elif entity_type == 'HATCH':
            # Extract hatch boundaries for area detection
            paths = []
            for path in entity.paths:
                if hasattr(path, 'edges'):
                    path_points = []
                    for edge in path.edges:
                        if edge.type == 'LineEdge':
                            path_points.extend([
                                (edge.start.x * self.unit_conversion, edge.start.y * self.unit_conversion),
                                (edge.end.x * self.unit_conversion, edge.end.y * self.unit_conversion)
                            ])
                    if path_points:
                        paths.append(path_points)
            data['paths'] = paths
            
        elif entity_type == 'TEXT' or entity_type == 'MTEXT':
            insert = entity.dxf.insert if hasattr(entity.dxf, 'insert') else (0, 0, 0)
            data.update({
                'text': entity.dxf.text if hasattr(entity.dxf, 'text') else '',
                'position': (insert[0] * self.unit_conversion, insert[1] * self.unit_conversion),
                'height': getattr(entity.dxf, 'height', 1) * self.unit_conversion
            })
            
        return data if any(k in data for k in ['start', 'points', 'center', 'paths', 'text']) else None
    
    def _classify_entities(self, entities):
        """Classify entities by architectural function"""
        classified = {
            'walls': [],
            'doors': [],
            'windows': [],
            'restricted_zones': [],
            'entrances': [],
            'dimensions': [],
            'other': []
        }
        
        for entity in entities:
            layer = entity['layer'].upper()
            entity_type = entity['type']
            color = entity.get('color', 256)
            
            # Classification logic based on layer names, colors, and geometry
            if any(keyword in layer for keyword in ['WALL', 'MUR', 'CLOISON']):
                classified['walls'].append(entity)
            elif any(keyword in layer for keyword in ['DOOR', 'PORTE']) or entity_type == 'ARC':
                classified['doors'].append(entity)
            elif any(keyword in layer for keyword in ['WINDOW', 'FENETRE']):
                classified['windows'].append(entity)
            elif any(keyword in layer for keyword in ['RESTRICT', 'PROHIB', 'NO_ENTRY', 'BLUE']) or color == 5:
                classified['restricted_zones'].append(entity)
            elif any(keyword in layer for keyword in ['ENTRANCE', 'EXIT', 'ENTREE', 'SORTIE']) or color == 1:
                classified['entrances'].append(entity)
            elif entity_type in ['TEXT', 'MTEXT'] or 'DIM' in layer:
                classified['dimensions'].append(entity)
            else:
                classified['other'].append(entity)
                
        return classified

def parse_dwg_dxf(file_path):
    """Main parsing function for backward compatibility"""
    parser = CADParser()
    return parser.parse_dwg_dxf(file_path)