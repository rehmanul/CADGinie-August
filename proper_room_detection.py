#!/usr/bin/env python3

import ezdxf
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely.ops import unary_union, polygonize
import numpy as np
from scipy.spatial import distance_matrix

class ProperRoomDetection:
    def __init__(self):
        self.rooms = []
        self.walls = []
        self.boundaries = []
        self.text_labels = []
        
    def analyze_ovo_properly(self, dxf_path):
        """Properly analyze the OVO file with correct room detection"""
        print("🔍 PROPER ROOM DETECTION - Analyzing OVO file...")
        
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        # Collect all entities by layer
        layers = {}
        for entity in msp:
            layer = entity.dxf.layer
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(entity)
        
        print(f"📋 Found layers: {list(layers.keys())}")
        
        # Extract walls and boundaries
        wall_lines = []
        room_polygons = []
        
        for layer_name, entities in layers.items():
            print(f"🔍 Processing layer '{layer_name}': {len(entities)} entities")
            
            for entity in entities:
                if entity.dxftype() == 'LWPOLYLINE':
                    points = [(p[0], p[1]) for p in entity.get_points()]
                    if len(points) >= 2:
                        # Check if it's a closed polygon (room boundary)
                        if len(points) >= 3 and self._is_closed_polygon(points):
                            poly = Polygon(points)
                            if poly.is_valid and poly.area > 1:  # Minimum 1m² room
                                room_polygons.append({
                                    'geometry': poly,
                                    'layer': layer_name,
                                    'area': poly.area,
                                    'type': self._classify_room_from_layer(layer_name, poly)
                                })
                                print(f"  ✓ Found room: {poly.area:.1f}m² on layer {layer_name}")
                        else:
                            # It's a wall line
                            wall_lines.append(LineString(points))
                
                elif entity.dxftype() == 'HATCH':
                    # Hatched areas are often rooms
                    hatch_polys = self._extract_hatch_boundaries(entity)
                    for poly in hatch_polys:
                        if poly.area > 1:
                            room_polygons.append({
                                'geometry': poly,
                                'layer': layer_name,
                                'area': poly.area,
                                'type': self._classify_room_from_layer(layer_name, poly)
                            })
                            print(f"  ✓ Found hatched room: {poly.area:.1f}m² on layer {layer_name}")
                
                elif entity.dxftype() in ['TEXT', 'MTEXT']:
                    # Text labels help identify rooms
                    text_info = self._extract_text_info(entity)
                    if text_info:
                        self.text_labels.append(text_info)
        
        # If no room polygons found, detect from wall network
        if not room_polygons:
            print("🔍 No explicit rooms found, detecting from wall network...")
            room_polygons = self._detect_rooms_from_walls(wall_lines)
        
        # Merge nearby text labels with rooms
        self._assign_text_to_rooms(room_polygons)
        
        self.rooms = room_polygons
        self.walls = wall_lines
        
        print(f"✅ FINAL RESULTS:")
        print(f"   Walls: {len(self.walls)}")
        print(f"   Rooms: {len(self.rooms)}")
        
        # Print room details
        for i, room in enumerate(self.rooms):
            print(f"   Room {i+1}: {room['type']} - {room['area']:.1f}m² (layer: {room['layer']})")
        
        return self.rooms, self.walls

    def _is_closed_polygon(self, points):
        """Check if polyline forms a closed polygon"""
        if len(points) < 3:
            return False
        
        # Check if first and last points are close
        first = points[0]
        last = points[-1]
        distance = ((first[0] - last[0])**2 + (first[1] - last[1])**2)**0.5
        
        return distance < 0.1  # Within 10cm tolerance

    def _extract_hatch_boundaries(self, hatch_entity):
        """Extract polygon boundaries from hatch entity"""
        polygons = []
        
        try:
            for path in hatch_entity.paths:
                path_points = []
                
                for edge in path.edges:
                    if hasattr(edge, 'start'):
                        path_points.append((edge.start[0], edge.start[1]))
                    elif hasattr(edge, 'center'):  # Arc
                        # Approximate arc with points
                        center = edge.center
                        radius = edge.radius
                        start_angle = edge.start_angle
                        end_angle = edge.end_angle
                        
                        angles = np.linspace(start_angle, end_angle, 10)
                        for angle in angles:
                            x = center[0] + radius * np.cos(np.radians(angle))
                            y = center[1] + radius * np.sin(np.radians(angle))
                            path_points.append((x, y))
                
                if len(path_points) >= 3:
                    try:
                        poly = Polygon(path_points)
                        if poly.is_valid:
                            polygons.append(poly)
                    except:
                        pass
        except:
            pass
        
        return polygons

    def _extract_text_info(self, text_entity):
        """Extract text information"""
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
                'text': text.strip(),
                'position': position,
                'layer': text_entity.dxf.layer
            }
        except:
            return None

    def _classify_room_from_layer(self, layer_name, polygon):
        """Classify room type from layer name and geometry"""
        layer_lower = layer_name.lower()
        area = polygon.area
        
        # Layer-based classification
        if any(keyword in layer_lower for keyword in ['wc', 'toilet', 'bath', 'sdb']):
            return 'bathroom'
        elif any(keyword in layer_lower for keyword in ['kitchen', 'cuisine', 'cook']):
            return 'kitchen'
        elif any(keyword in layer_lower for keyword in ['bedroom', 'chambre', 'bed']):
            return 'bedroom'
        elif any(keyword in layer_lower for keyword in ['living', 'salon', 'séjour']):
            return 'living'
        elif any(keyword in layer_lower for keyword in ['office', 'bureau', 'work']):
            return 'office'
        elif any(keyword in layer_lower for keyword in ['storage', 'closet', 'placard']):
            return 'storage'
        elif any(keyword in layer_lower for keyword in ['corridor', 'hall', 'passage']):
            return 'corridor'
        elif any(keyword in layer_lower for keyword in ['balcon', 'terrace', 'terrasse']):
            return 'balcony'
        
        # Area-based classification if no layer match
        if area < 3:
            return 'storage'
        elif area < 6:
            return 'bathroom'
        elif area < 12:
            return 'bedroom'
        elif area < 25:
            return 'living'
        elif area < 50:
            return 'office'
        else:
            return 'public_space'

    def _detect_rooms_from_walls(self, wall_lines):
        """Detect rooms from wall network using proper geometric analysis"""
        if not wall_lines:
            return []
        
        print("🔍 Detecting rooms from wall network...")
        
        # Get overall bounds
        all_coords = []
        for wall in wall_lines:
            all_coords.extend(list(wall.coords))
        
        if not all_coords:
            return []
        
        coords_array = np.array(all_coords)
        bounds = (coords_array[:, 0].min(), coords_array[:, 1].min(),
                 coords_array[:, 0].max(), coords_array[:, 1].max())
        
        print(f"Building bounds: {bounds}")
        
        # Create a finer grid for room detection
        rooms = []
        grid_density = 20  # More points for better detection
        
        x_range = np.linspace(bounds[0], bounds[2], grid_density)
        y_range = np.linspace(bounds[1], bounds[3], grid_density)
        
        processed_points = set()
        
        for i, x in enumerate(x_range):
            for j, y in enumerate(y_range):
                if (i, j) in processed_points:
                    continue
                
                test_point = Point(x, y)
                
                # Check if point is inside a room (away from walls)
                min_wall_distance = min([wall.distance(test_point) for wall in wall_lines])
                
                if min_wall_distance > 1.0:  # Point is inside a room
                    # Grow region around this point to find room boundary
                    room_points = self._grow_room_region(x, y, wall_lines, x_range, y_range)
                    
                    if len(room_points) > 4:  # Minimum points for a room
                        try:
                            # Create convex hull of room points
                            from scipy.spatial import ConvexHull
                            hull = ConvexHull(room_points)
                            room_coords = [room_points[i] for i in hull.vertices]
                            
                            room_poly = Polygon(room_coords)
                            if room_poly.is_valid and room_poly.area > 4:  # Minimum 4m²
                                rooms.append({
                                    'geometry': room_poly,
                                    'layer': 'detected',
                                    'area': room_poly.area,
                                    'type': self._classify_room_from_layer('', room_poly)
                                })
                                
                                # Mark processed grid points
                                for px, py in room_points:
                                    pi = np.argmin(np.abs(x_range - px))
                                    pj = np.argmin(np.abs(y_range - py))
                                    processed_points.add((pi, pj))
                                
                                print(f"  ✓ Detected room: {room_poly.area:.1f}m²")
                        except:
                            pass
        
        return rooms

    def _grow_room_region(self, start_x, start_y, wall_lines, x_range, y_range):
        """Grow region from seed point to find room boundary"""
        room_points = [(start_x, start_y)]
        to_check = [(start_x, start_y)]
        checked = set()
        
        step_size = (x_range[1] - x_range[0]) if len(x_range) > 1 else 1.0
        
        while to_check and len(room_points) < 100:  # Limit to prevent infinite loops
            current_x, current_y = to_check.pop(0)
            
            if (current_x, current_y) in checked:
                continue
            checked.add((current_x, current_y))
            
            # Check 8 neighboring points
            for dx in [-step_size, 0, step_size]:
                for dy in [-step_size, 0, step_size]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    new_x = current_x + dx
                    new_y = current_y + dy
                    
                    # Check bounds
                    if (new_x < x_range[0] or new_x > x_range[-1] or
                        new_y < y_range[0] or new_y > y_range[-1]):
                        continue
                    
                    if (new_x, new_y) in checked:
                        continue
                    
                    test_point = Point(new_x, new_y)
                    min_wall_distance = min([wall.distance(test_point) for wall in wall_lines])
                    
                    if min_wall_distance > 1.0:  # Still inside room
                        room_points.append((new_x, new_y))
                        to_check.append((new_x, new_y))
        
        return room_points

    def _assign_text_to_rooms(self, room_polygons):
        """Assign text labels to nearby rooms"""
        for text_info in self.text_labels:
            text_point = Point(text_info['position'])
            
            # Find closest room
            min_distance = float('inf')
            closest_room = None
            
            for room in room_polygons:
                distance = room['geometry'].distance(text_point)
                if distance < min_distance:
                    min_distance = distance
                    closest_room = room
            
            # If text is close to room (within 5m), use text for room type
            if closest_room and min_distance < 5.0:
                text = text_info['text'].lower()
                if any(keyword in text for keyword in ['wc', 'toilet', 'bath']):
                    closest_room['type'] = 'bathroom'
                elif any(keyword in text for keyword in ['kitchen', 'cuisine']):
                    closest_room['type'] = 'kitchen'
                elif any(keyword in text for keyword in ['bedroom', 'chambre']):
                    closest_room['type'] = 'bedroom'
                elif any(keyword in text for keyword in ['living', 'salon']):
                    closest_room['type'] = 'living'

    def visualize_proper_detection(self, output_path):
        """Visualize the properly detected rooms"""
        if not self.rooms:
            print("❌ No rooms detected to visualize")
            return
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Colors for different room types
        room_colors = {
            'bathroom': '#E6FFFA',
            'kitchen': '#FFF5F5', 
            'bedroom': '#F0FFF4',
            'living': '#FFFAF0',
            'office': '#F7FAFC',
            'storage': '#FAF5FF',
            'corridor': '#FFF8E1',
            'balcony': '#F0F8FF',
            'public_space': '#E8F5E8'
        }
        
        # Draw walls
        for wall in self.walls:
            x, y = wall.xy
            ax.plot(x, y, color='#2D3748', linewidth=1.5, alpha=0.8)
        
        # Draw rooms
        for i, room in enumerate(self.rooms):
            geom = room['geometry']
            room_type = room['type']
            area = room['area']
            
            if hasattr(geom, 'exterior'):
                x, y = geom.exterior.xy
                color = room_colors.get(room_type, '#F9F9F9')
                
                # Fill room
                ax.fill(x, y, color=color, alpha=0.7, edgecolor='#4A5568', linewidth=1)
                
                # Room label
                centroid = geom.centroid
                ax.text(centroid.x, centroid.y, 
                       f"{room_type.replace('_', ' ').title()}\n{area:.1f}m²",
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
        
        # Statistics
        room_counts = {}
        total_area = 0
        for room in self.rooms:
            room_type = room['type']
            room_counts[room_type] = room_counts.get(room_type, 0) + 1
            total_area += room['area']
        
        stats_text = f"ROOM DETECTION RESULTS:\n"
        stats_text += f"Total Rooms: {len(self.rooms)}\n"
        stats_text += f"Total Area: {total_area:.1f}m²\n\n"
        stats_text += "Room Types:\n"
        for room_type, count in room_counts.items():
            stats_text += f"• {room_type.replace('_', ' ').title()}: {count}\n"
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
               verticalalignment='top', fontsize=11, fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        ax.set_aspect('equal')
        ax.set_title('PROPER ROOM DETECTION - OVO DOSSIER COSTO', 
                    fontsize=16, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.show()
        
        return output_path

def analyze_ovo_properly():
    """Main function to properly analyze OVO file"""
    detector = ProperRoomDetection()
    
    dxf_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\input_files\ovo DOSSIER COSTO - plan rdc rdj - cota.dxf"
    output_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\output_files\proper_ovo_detection.png"
    
    print("🏗️ PROPER ROOM DETECTION FOR OVO")
    print("=" * 50)
    
    # Analyze the file properly
    rooms, walls = detector.analyze_ovo_properly(dxf_file)
    
    # Visualize results
    detector.visualize_proper_detection(output_file)
    
    return output_file

if __name__ == "__main__":
    analyze_ovo_properly()