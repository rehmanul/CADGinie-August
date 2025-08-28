import numpy as np
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union, polygonize
from shapely.validation import make_valid
import math

class GeometryProcessor:
    def __init__(self):
        self.tolerance = 0.01
        self.wall_thickness = 0.2
        
    def process_geometry(self, classified_entities, wall_layer='0', prohibited_layer='PROHIBITED', entrance_layer='ENTRANCE'):
        """Advanced geometry processing with architectural element recognition"""
        print("Processing geometry with architectural intelligence...")
        
        # Extract and process different element types
        walls = self._process_walls(classified_entities.get('walls', []) + classified_entities.get('other', []))
        restricted_zones = self._process_areas(classified_entities.get('restricted_zones', []))
        entrances = self._process_entrances(classified_entities.get('entrances', []) + classified_entities.get('doors', []))
        
        # Create main boundary from walls
        main_boundary = self._create_boundary(walls)
        
        if not main_boundary or main_boundary.is_empty:
            print("Warning: Could not create valid boundary from walls")
            return None
            
        # Calculate usable area
        usable_area = self._calculate_usable_area(main_boundary, restricted_zones, entrances)
        
        # Detect rooms and spaces
        rooms = self._detect_rooms(main_boundary, walls)
        
        return {
            'walls': main_boundary,
            'wall_lines': walls,
            'restricted_areas': restricted_zones,
            'entrances': entrances,
            'usable_area': usable_area,
            'rooms': rooms,
            'total_area': main_boundary.area if main_boundary else 0,
            'usable_area_ratio': usable_area.area / main_boundary.area if main_boundary and main_boundary.area > 0 else 0
        }
    
    def _process_walls(self, wall_entities):
        """Process wall entities into geometric lines with proper thickness"""
        wall_lines = []
        
        for entity in wall_entities:
            lines = self._entity_to_lines(entity)
            wall_lines.extend(lines)
        
        # Merge connected lines
        merged_lines = self._merge_connected_lines(wall_lines)
        
        # Filter out very short lines (likely noise)
        filtered_lines = [line for line in merged_lines if line.length > 0.1]
        
        return filtered_lines
    
    def _process_areas(self, area_entities):
        """Process area entities (hatches, polygons) into Shapely polygons"""
        areas = []
        
        for entity in area_entities:
            if entity['type'] == 'HATCH' and 'paths' in entity:
                for path in entity['paths']:
                    if len(path) >= 3:
                        try:
                            poly = Polygon(path)
                            if poly.is_valid and poly.area > 0.1:
                                areas.append(poly)
                        except:
                            continue
            elif entity['type'] in ['LWPOLYLINE', 'POLYLINE'] and entity.get('is_closed'):
                points = entity.get('points', [])
                if len(points) >= 3:
                    try:
                        poly = Polygon(points)
                        if poly.is_valid and poly.area > 0.1:
                            areas.append(poly)
                    except:
                        continue
        
        return unary_union(areas) if areas else Polygon()
    
    def _process_entrances(self, entrance_entities):
        """Process entrance/door entities with swing detection"""
        entrances = []
        
        for entity in entrance_entities:
            if entity['type'] == 'ARC':
                # Door swing arc
                center = Point(entity['center'])
                radius = entity['radius']
                
                # Create door swing polygon
                start_angle = math.radians(entity['start_angle'])
                end_angle = math.radians(entity['end_angle'])
                
                # Generate arc points
                angles = np.linspace(start_angle, end_angle, 20)
                arc_points = [(center.x + radius * math.cos(a), center.y + radius * math.sin(a)) for a in angles]
                arc_points.append(entity['center'])  # Close to center
                
                try:
                    door_poly = Polygon(arc_points)
                    if door_poly.is_valid:
                        entrances.append(door_poly)
                except:
                    continue
                    
            elif entity['type'] == 'CIRCLE':
                # Circular entrance area
                center = Point(entity['center'])
                entrance_area = center.buffer(entity['radius'])
                entrances.append(entrance_area)
        
        return unary_union(entrances) if entrances else Polygon()
    
    def _entity_to_lines(self, entity):
        """Convert entity to LineString objects"""
        lines = []
        
        if entity['type'] == 'LINE':
            line = LineString([entity['start'], entity['end']])
            if line.length > self.tolerance:
                lines.append(line)
                
        elif entity['type'] in ['LWPOLYLINE', 'POLYLINE']:
            points = entity.get('points', [])
            if len(points) >= 2:
                for i in range(len(points) - 1):
                    line = LineString([points[i], points[i + 1]])
                    if line.length > self.tolerance:
                        lines.append(line)
                        
                # Close polygon if needed
                if entity.get('is_closed') and len(points) > 2:
                    line = LineString([points[-1], points[0]])
                    if line.length > self.tolerance:
                        lines.append(line)
        
        return lines
    
    def _merge_connected_lines(self, lines):
        """Merge connected line segments"""
        if not lines:
            return []
            
        merged = []
        used = set()
        
        for i, line1 in enumerate(lines):
            if i in used:
                continue
                
            current_line = line1
            used.add(i)
            
            # Try to extend the line by connecting with other lines
            extended = True
            while extended:
                extended = False
                for j, line2 in enumerate(lines):
                    if j in used:
                        continue
                        
                    # Check if lines can be connected
                    if self._can_connect_lines(current_line, line2):
                        current_line = self._connect_lines(current_line, line2)
                        used.add(j)
                        extended = True
                        break
            
            merged.append(current_line)
        
        return merged
    
    def _can_connect_lines(self, line1, line2):
        """Check if two lines can be connected"""
        tolerance = self.tolerance * 2
        
        endpoints1 = [Point(line1.coords[0]), Point(line1.coords[-1])]
        endpoints2 = [Point(line2.coords[0]), Point(line2.coords[-1])]
        
        for p1 in endpoints1:
            for p2 in endpoints2:
                if p1.distance(p2) < tolerance:
                    return True
        return False
    
    def _connect_lines(self, line1, line2):
        """Connect two lines into a single line"""
        coords1 = list(line1.coords)
        coords2 = list(line2.coords)
        
        # Find connection points and order
        tolerance = self.tolerance * 2
        
        if Point(coords1[-1]).distance(Point(coords2[0])) < tolerance:
            # line1 end connects to line2 start
            return LineString(coords1 + coords2[1:])
        elif Point(coords1[-1]).distance(Point(coords2[-1])) < tolerance:
            # line1 end connects to line2 end (reverse line2)
            return LineString(coords1 + coords2[-2::-1])
        elif Point(coords1[0]).distance(Point(coords2[0])) < tolerance:
            # line1 start connects to line2 start (reverse line1)
            return LineString(coords1[::-1] + coords2[1:])
        elif Point(coords1[0]).distance(Point(coords2[-1])) < tolerance:
            # line1 start connects to line2 end
            return LineString(coords2 + coords1[1:])
        
        return line1  # Fallback
    
    def _create_boundary(self, wall_lines):
        """Create building boundary from wall lines"""
        if not wall_lines:
            return Polygon()
        
        # Try to create polygons from lines
        try:
            # Create a buffer around all lines to form walls with thickness
            wall_union = unary_union(wall_lines)
            boundary = wall_union.buffer(self.wall_thickness / 2)
            
            # If we get a MultiPolygon, take the largest one
            if isinstance(boundary, MultiPolygon):
                boundary = max(boundary.geoms, key=lambda p: p.area)
            
            return make_valid(boundary)
            
        except Exception as e:
            print(f"Error creating boundary: {e}")
            
            # Fallback: create convex hull
            all_points = []
            for line in wall_lines:
                all_points.extend(line.coords)
            
            if len(all_points) >= 3:
                return Polygon(all_points).convex_hull
            
            return Polygon()
    
    def _calculate_usable_area(self, main_boundary, restricted_zones, entrances):
        """Calculate usable area excluding restricted zones and entrance buffers"""
        if not main_boundary or main_boundary.is_empty:
            return Polygon()
        
        usable = main_boundary
        
        # Remove restricted zones
        if restricted_zones and not restricted_zones.is_empty:
            usable = usable.difference(restricted_zones)
        
        # Create buffer around entrances to avoid placing items too close
        if entrances and not entrances.is_empty:
            entrance_buffer = entrances.buffer(1.0)  # 1m buffer around entrances
            usable = usable.difference(entrance_buffer)
        
        # Ensure result is valid
        if hasattr(usable, 'geoms'):
            # If MultiPolygon, take the largest piece
            usable = max(usable.geoms, key=lambda p: p.area) if usable.geoms else Polygon()
        
        return make_valid(usable) if usable.is_valid else Polygon()
    
    def _detect_rooms(self, boundary, wall_lines):
        """Detect individual rooms within the boundary"""
        rooms = []
        
        try:
            # This is a simplified room detection
            # In a full implementation, this would use more sophisticated algorithms
            
            # For now, return the main boundary as a single room
            if boundary and not boundary.is_empty:
                rooms.append({
                    'geometry': boundary,
                    'area': boundary.area,
                    'type': 'main_space'
                })
        
        except Exception as e:
            print(f"Error detecting rooms: {e}")
        
        return rooms

def process_geometry(entities, wall_layer='0', prohibited_layer='PROHIBITED', entrance_layer='ENTRANCE'):
    """Main processing function for backward compatibility"""
    processor = GeometryProcessor()
    return processor.process_geometry(entities, wall_layer, prohibited_layer, entrance_layer)