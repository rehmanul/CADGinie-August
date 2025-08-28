import numpy as np
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, box
from shapely.ops import unary_union, polygonize
from shapely.validation import make_valid
import math

class AdvancedGeometryProcessor:
    def __init__(self):
        self.wall_thickness = 0.2
        self.entrance_clearance = 1.5
        self.min_room_area = 4.0
        
    def process_architectural_geometry(self, classified_entities, wall_layer="0", 
                                     prohibited_layer="PROHIBITED", entrance_layer="ENTRANCE"):
        """Process classified entities into architectural geometry"""
        
        wall_geometry = self._process_walls(classified_entities['walls'])
        restricted_geometry = self._process_restricted_zones(classified_entities['restricted_zones'])
        entrance_geometry = self._process_entrances(classified_entities['entrances'])
        door_geometry = self._process_doors_with_swings(classified_entities['doors'])
        window_geometry = self._process_windows(classified_entities['windows'])
        
        building_envelope = self._calculate_building_envelope(wall_geometry)
        usable_areas = self._calculate_usable_areas(
            building_envelope, wall_geometry, restricted_geometry, 
            entrance_geometry, door_geometry
        )
        
        validated_geometry = self._validate_and_correct_geometry({
            'walls': wall_geometry,
            'restricted_zones': restricted_geometry,
            'entrances': entrance_geometry,
            'doors': door_geometry,
            'windows': window_geometry,
            'building_envelope': building_envelope,
            'usable_areas': usable_areas
        })
        
        stats = self._calculate_geometry_statistics(validated_geometry)
        validated_geometry['statistics'] = stats
        
        return validated_geometry
    
    def _process_walls(self, wall_entities):
        """Process wall entities into geometric representations"""
        wall_lines = []
        wall_polygons = []
        
        for entity in wall_entities:
            if entity['type'] == 'LINE':
                start = entity['start']
                end = entity['end']
                wall_line = LineString([start, end])
                wall_lines.append(wall_line)
                wall_poly = wall_line.buffer(self.wall_thickness / 2)
                wall_polygons.append(wall_poly)
                
            elif entity['type'] in ['LWPOLYLINE', 'POLYLINE']:
                points = entity['points']
                if len(points) >= 2:
                    wall_line = LineString(points)
                    wall_lines.append(wall_line)
                    wall_poly = wall_line.buffer(self.wall_thickness / 2)
                    wall_polygons.append(wall_poly)
        
        merged_walls = self._merge_wall_segments(wall_lines, wall_polygons)
        
        return {
            'lines': wall_lines,
            'polygons': wall_polygons,
            'merged': merged_walls,
            'total_length': sum(line.length for line in wall_lines)
        }
    
    def _merge_wall_segments(self, wall_lines, wall_polygons):
        """Merge overlapping and adjacent wall segments"""
        if not wall_polygons:
            return {'lines': [], 'polygons': []}
        
        try:
            merged_polygon = unary_union(wall_polygons)
            
            if isinstance(merged_polygon, Polygon):
                merged_polygons = [merged_polygon]
            elif isinstance(merged_polygon, MultiPolygon):
                merged_polygons = list(merged_polygon.geoms)
            else:
                merged_polygons = wall_polygons
            
            merged_lines = []
            for poly in merged_polygons:
                if poly.is_valid and not poly.is_empty:
                    centerline = self._extract_polygon_centerline(poly)
                    if centerline:
                        merged_lines.append(centerline)
            
            return {'lines': merged_lines, 'polygons': merged_polygons}
            
        except Exception:
            return {'lines': wall_lines, 'polygons': wall_polygons}
    
    def _extract_polygon_centerline(self, polygon):
        """Extract approximate centerline from wall polygon"""
        try:
            bounds = polygon.bounds
            center_x = (bounds[0] + bounds[2]) / 2
            center_y = (bounds[1] + bounds[3]) / 2
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            
            if width > height:
                line = LineString([(bounds[0], center_y), (bounds[2], center_y)])
            else:
                line = LineString([(center_x, bounds[1]), (center_x, bounds[3])])
            
            return line
        except Exception:
            return None
    
    def _process_restricted_zones(self, restricted_entities):
        """Process restricted zone entities"""
        restricted_polygons = []
        
        for entity in restricted_entities:
            if entity['type'] == 'HATCH':
                for path in entity.get('paths', []):
                    if len(path) >= 3:
                        try:
                            poly = Polygon(path)
                            if poly.is_valid and poly.area > self.min_room_area:
                                restricted_polygons.append(poly)
                        except Exception:
                            continue
                            
            elif entity['type'] in ['LWPOLYLINE', 'POLYLINE']:
                points = entity['points']
                if len(points) >= 3 and entity.get('is_closed', False):
                    try:
                        poly = Polygon(points)
                        if poly.is_valid and poly.area > 1.0:
                            restricted_polygons.append(poly)
                    except Exception:
                        continue
            
            elif entity['type'] == 'CIRCLE':
                center = entity['center']
                radius = entity['radius']
                circle = Point(center).buffer(radius)
                if circle.area > 1.0:
                    restricted_polygons.append(circle)
        
        if restricted_polygons:
            try:
                unified_restricted = unary_union(restricted_polygons)
                if isinstance(unified_restricted, Polygon):
                    restricted_polygons = [unified_restricted]
                elif isinstance(unified_restricted, MultiPolygon):
                    restricted_polygons = list(unified_restricted.geoms)
            except Exception:
                pass
        
        return {
            'polygons': restricted_polygons,
            'total_area': sum(poly.area for poly in restricted_polygons)
        }
    
    def _process_entrances(self, entrance_entities):
        """Process entrance/exit entities with clearance zones"""
        entrance_points = []
        entrance_zones = []
        
        for entity in entrance_entities:
            if entity['type'] == 'CIRCLE':
                center = entity['center']
                entrance_point = Point(center)
                entrance_points.append(entrance_point)
                clearance_zone = entrance_point.buffer(self.entrance_clearance)
                entrance_zones.append(clearance_zone)
                
            elif entity['type'] == 'ARC':
                center = entity['center']
                entrance_point = Point(center)
                entrance_points.append(entrance_point)
                clearance_zone = entrance_point.buffer(self.entrance_clearance)
                entrance_zones.append(clearance_zone)
                
            elif entity['type'] in ['LWPOLYLINE', 'POLYLINE']:
                points = entity['points']
                if points:
                    line = LineString(points)
                    entrance_point = line.centroid
                    entrance_points.append(entrance_point)
                    clearance_zone = entrance_point.buffer(self.entrance_clearance)
                    entrance_zones.append(clearance_zone)
        
        return {
            'points': entrance_points,
            'clearance_zones': entrance_zones,
            'count': len(entrance_points)
        }
    
    def _process_doors_with_swings(self, door_entities):
        """Process doors with swing direction detection"""
        doors = []
        door_swings = []
        
        for entity in door_entities:
            if entity['type'] == 'ARC':
                center = entity['center']
                radius = entity['radius']
                start_angle = entity.get('start_angle', 0)
                end_angle = entity.get('end_angle', 90)
                
                swing_points = self._create_door_swing_polygon(center, radius, start_angle, end_angle)
                
                if swing_points:
                    swing_poly = Polygon(swing_points)
                    door_swings.append(swing_poly)
                    
                    doors.append({
                        'center': center,
                        'radius': radius,
                        'start_angle': start_angle,
                        'end_angle': end_angle,
                        'swing_direction': entity.get('swing_direction', 'unknown'),
                        'swing_polygon': swing_poly
                    })
            
            elif entity['type'] == 'CIRCLE':
                center = entity['center']
                radius = entity['radius']
                
                swing_poly = Point(center).buffer(radius)
                door_swings.append(swing_poly)
                
                doors.append({
                    'center': center,
                    'radius': radius,
                    'start_angle': 0,
                    'end_angle': 360,
                    'swing_direction': 'full',
                    'swing_polygon': swing_poly
                })
        
        return {
            'doors': doors,
            'swing_polygons': door_swings,
            'count': len(doors)
        }
    
    def _create_door_swing_polygon(self, center, radius, start_angle, end_angle):
        """Create door swing polygon from arc parameters"""
        try:
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)
            
            points = [center]
            
            num_segments = max(8, int(abs(end_angle - start_angle) / 10))
            angle_step = (end_rad - start_rad) / num_segments
            
            for i in range(num_segments + 1):
                angle = start_rad + i * angle_step
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
                points.append((x, y))
            
            points.append(center)
            return points
            
        except Exception:
            return None
    
    def _process_windows(self, window_entities):
        """Process window entities"""
        windows = []
        
        for entity in window_entities:
            if entity['type'] == 'LINE':
                start = entity['start']
                end = entity['end']
                
                window_line = LineString([start, end])
                windows.append({
                    'line': window_line,
                    'start': start,
                    'end': end,
                    'length': window_line.length
                })
                
            elif entity['type'] in ['LWPOLYLINE', 'POLYLINE']:
                points = entity['points']
                if len(points) >= 2:
                    window_line = LineString(points)
                    windows.append({
                        'line': window_line,
                        'points': points,
                        'length': window_line.length
                    })
        
        return {
            'windows': windows,
            'total_length': sum(w['length'] for w in windows),
            'count': len(windows)
        }
    
    def _calculate_building_envelope(self, wall_geometry):
        """Calculate building envelope from walls"""
        try:
            if not wall_geometry['polygons']:
                return Polygon()
            
            wall_union = unary_union(wall_geometry['polygons'])
            
            if isinstance(wall_union, Polygon):
                envelope = wall_union.convex_hull
            elif isinstance(wall_union, MultiPolygon):
                largest_poly = max(wall_union.geoms, key=lambda p: p.area)
                envelope = largest_poly.convex_hull
            else:
                all_coords = []
                for line in wall_geometry['lines']:
                    all_coords.extend(line.coords)
                
                if len(all_coords) >= 3:
                    envelope = Polygon(all_coords).convex_hull
                else:
                    envelope = Polygon()
            
            return envelope
            
        except Exception:
            return Polygon()
    
    def _calculate_usable_areas(self, building_envelope, wall_geometry, 
                               restricted_geometry, entrance_geometry, door_geometry):
        """Calculate usable areas for îlot placement"""
        
        if building_envelope.is_empty:
            return {'usable_area': Polygon(), 'rooms': [], 'total_usable_area': 0}
        
        try:
            usable_area = building_envelope
            
            if wall_geometry['polygons']:
                wall_union = unary_union(wall_geometry['polygons'])
                usable_area = usable_area.difference(wall_union)
            
            if restricted_geometry['polygons']:
                restricted_union = unary_union(restricted_geometry['polygons'])
                usable_area = usable_area.difference(restricted_union)
            
            if entrance_geometry['clearance_zones']:
                entrance_union = unary_union(entrance_geometry['clearance_zones'])
                usable_area = usable_area.difference(entrance_union)
            
            if door_geometry['swing_polygons']:
                door_union = unary_union(door_geometry['swing_polygons'])
                usable_area = usable_area.difference(door_union)
            
            usable_area = make_valid(usable_area)
            
            rooms = []
            if isinstance(usable_area, MultiPolygon):
                for poly in usable_area.geoms:
                    if poly.area >= self.min_room_area:
                        rooms.append(poly)
                
                if rooms:
                    usable_area = max(rooms, key=lambda p: p.area)
                else:
                    usable_area = Polygon()
            elif isinstance(usable_area, Polygon) and usable_area.area >= self.min_room_area:
                rooms = [usable_area]
            else:
                usable_area = Polygon()
                rooms = []
            
            total_usable_area = sum(room.area for room in rooms)
            
            return {
                'usable_area': usable_area,
                'rooms': rooms,
                'total_usable_area': total_usable_area
            }
            
        except Exception:
            return {'usable_area': Polygon(), 'rooms': [], 'total_usable_area': 0}
    
    def _validate_and_correct_geometry(self, geometry_dict):
        """Validate and correct all geometric elements"""
        
        for key, geom_data in geometry_dict.items():
            if key == 'walls':
                geometry_dict[key] = self._validate_wall_geometry(geom_data)
            elif key == 'restricted_zones':
                geometry_dict[key] = self._validate_polygon_geometry(geom_data)
            elif key == 'entrances':
                geometry_dict[key] = self._validate_entrance_geometry(geom_data)
            elif key == 'doors':
                geometry_dict[key] = self._validate_door_geometry(geom_data)
            elif key == 'building_envelope':
                geometry_dict[key] = make_valid(geom_data) if geom_data else Polygon()
            elif key == 'usable_areas':
                geometry_dict[key] = self._validate_usable_areas(geom_data)
        
        return geometry_dict
    
    def _validate_wall_geometry(self, wall_data):
        """Validate wall geometry"""
        validated_lines = []
        validated_polygons = []
        
        for line in wall_data.get('lines', []):
            if line.is_valid and line.length > 0.1:
                validated_lines.append(line)
        
        for poly in wall_data.get('polygons', []):
            validated_poly = make_valid(poly)
            if validated_poly and not validated_poly.is_empty:
                validated_polygons.append(validated_poly)
        
        wall_data['lines'] = validated_lines
        wall_data['polygons'] = validated_polygons
        
        return wall_data
    
    def _validate_polygon_geometry(self, geom_data):
        """Validate polygon geometry"""
        validated_polygons = []
        
        for poly in geom_data.get('polygons', []):
            validated_poly = make_valid(poly)
            if validated_poly and not validated_poly.is_empty and validated_poly.area > 0.1:
                validated_polygons.append(validated_poly)
        
        geom_data['polygons'] = validated_polygons
        geom_data['total_area'] = sum(poly.area for poly in validated_polygons)
        
        return geom_data
    
    def _validate_entrance_geometry(self, entrance_data):
        """Validate entrance geometry"""
        validated_points = []
        validated_zones = []
        
        for point in entrance_data.get('points', []):
            if isinstance(point, Point) and point.is_valid:
                validated_points.append(point)
        
        for zone in entrance_data.get('clearance_zones', []):
            validated_zone = make_valid(zone)
            if validated_zone and not validated_zone.is_empty:
                validated_zones.append(validated_zone)
        
        entrance_data['points'] = validated_points
        entrance_data['clearance_zones'] = validated_zones
        entrance_data['count'] = len(validated_points)
        
        return entrance_data
    
    def _validate_door_geometry(self, door_data):
        """Validate door geometry"""
        validated_doors = []
        validated_swings = []
        
        for door in door_data.get('doors', []):
            swing_poly = door.get('swing_polygon')
            if swing_poly:
                validated_swing = make_valid(swing_poly)
                if validated_swing and not validated_swing.is_empty:
                    door['swing_polygon'] = validated_swing
                    validated_doors.append(door)
                    validated_swings.append(validated_swing)
        
        door_data['doors'] = validated_doors
        door_data['swing_polygons'] = validated_swings
        door_data['count'] = len(validated_doors)
        
        return door_data
    
    def _validate_usable_areas(self, usable_data):
        """Validate usable area geometry"""
        usable_area = usable_data.get('usable_area', Polygon())
        rooms = usable_data.get('rooms', [])
        
        if usable_area:
            usable_area = make_valid(usable_area)
            if usable_area.is_empty or usable_area.area < self.min_room_area:
                usable_area = Polygon()
        
        validated_rooms = []
        for room in rooms:
            validated_room = make_valid(room)
            if validated_room and not validated_room.is_empty and validated_room.area >= self.min_room_area:
                validated_rooms.append(validated_room)
        
        total_usable_area = sum(room.area for room in validated_rooms)
        
        return {
            'usable_area': usable_area,
            'rooms': validated_rooms,
            'total_usable_area': total_usable_area
        }
    
    def _calculate_geometry_statistics(self, geometry_dict):
        """Calculate comprehensive geometry statistics"""
        
        building_envelope = geometry_dict.get('building_envelope', Polygon())
        total_building_area = building_envelope.area if building_envelope else 0
        
        wall_data = geometry_dict.get('walls', {})
        total_wall_length = wall_data.get('total_length', 0)
        wall_area = sum(poly.area for poly in wall_data.get('polygons', []))
        
        usable_data = geometry_dict.get('usable_areas', {})
        total_usable_area = usable_data.get('total_usable_area', 0)
        usable_ratio = total_usable_area / total_building_area if total_building_area > 0 else 0
        
        restricted_data = geometry_dict.get('restricted_zones', {})
        restricted_area = restricted_data.get('total_area', 0)
        
        door_data = geometry_dict.get('doors', {})
        entrance_data = geometry_dict.get('entrances', {})
        
        return {
            'total_building_area': total_building_area,
            'total_wall_length': total_wall_length,
            'wall_area': wall_area,
            'total_usable_area': total_usable_area,
            'usable_area_ratio': usable_ratio,
            'restricted_area': restricted_area,
            'door_count': door_data.get('count', 0),
            'entrance_count': entrance_data.get('count', 0),
            'room_count': len(usable_data.get('rooms', [])),
            'wall_to_floor_ratio': wall_area / total_building_area if total_building_area > 0 else 0
        }

def process_architectural_geometry(classified_entities, wall_layer="0", 
                                 prohibited_layer="PROHIBITED", entrance_layer="ENTRANCE"):
    """Main geometry processing function"""
    processor = AdvancedGeometryProcessor()
    return processor.process_architectural_geometry(
        classified_entities, wall_layer, prohibited_layer, entrance_layer
    )