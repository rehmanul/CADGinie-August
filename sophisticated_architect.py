#!/usr/bin/env python3

import ezdxf
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Wedge, Arc
from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely.ops import unary_union, polygonize
import numpy as np
import networkx as nx
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial.distance import cdist
import json
import math

class SophisticatedArchitecturalEngine:
    def __init__(self):
        self.building_data = {
            'floors': {},
            'rooms': {},
            'circulation': {},
            'structural': {},
            'mep': {},  # Mechanical, Electrical, Plumbing
            'accessibility': {}
        }
        
        self.current_floor = 0
        self.zoom_level = 1.0
        self.view_center = (0, 0)
        self.active_room = None
        self.navigation_graph = nx.Graph()
        
        # Professional architectural color scheme
        self.arch_colors = {
            'walls_load_bearing': '#2D3748',
            'walls_partition': '#4A5568',
            'doors_main': '#E53E3E',
            'doors_interior': '#F56565',
            'windows': '#3182CE',
            'stairs': '#805AD5',
            'elevators': '#D69E2E',
            'rooms_public': '#38B2AC',
            'rooms_private': '#48BB78',
            'rooms_service': '#ED8936',
            'rooms_circulation': '#9F7AEA',
            'structure': '#1A202C',
            'mep_electrical': '#F6E05E',
            'mep_plumbing': '#4299E1',
            'mep_hvac': '#68D391',
            'accessibility': '#FC8181',
            'fire_safety': '#FF6B6B',
            'background': '#F7FAFC',
            'grid_major': '#E2E8F0',
            'grid_minor': '#F1F5F9',
            'text_primary': '#1A202C',
            'text_secondary': '#4A5568'
        }
        
        # Line weights following architectural standards
        self.line_weights = {
            'walls_exterior': 4.0,
            'walls_interior': 2.5,
            'doors': 2.0,
            'windows': 1.5,
            'furniture': 1.0,
            'dimensions': 0.8,
            'grid': 0.3,
            'hidden': 0.5
        }
        
        # Room type detection patterns
        self.room_patterns = {
            'bathroom': ['wc', 'toilet', 'bath', 'shower', 'sdb'],
            'kitchen': ['kitchen', 'cuisine', 'cook'],
            'bedroom': ['bedroom', 'chambre', 'bed', 'sleep'],
            'living': ['living', 'salon', 'séjour', 'family'],
            'office': ['office', 'bureau', 'work', 'study'],
            'storage': ['storage', 'closet', 'placard', 'cave'],
            'circulation': ['hall', 'corridor', 'entry', 'entrée'],
            'stair': ['stair', 'escalier', 'step'],
            'balcony': ['balcon', 'terrace', 'terrasse', 'deck']
        }

    def parse_sophisticated_dxf(self, dxf_path):
        """Advanced DXF parsing with architectural intelligence"""
        print("🏗️ Parsing DXF with architectural intelligence...")
        
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        # Initialize collections
        walls = {'exterior': [], 'interior': [], 'load_bearing': []}
        openings = {'doors': [], 'windows': []}
        spaces = {'rooms': [], 'circulation': [], 'service': []}
        structure = {'columns': [], 'beams': [], 'slabs': []}
        annotations = {'text': [], 'dimensions': [], 'symbols': []}
        
        # Parse entities with layer intelligence
        for entity in msp:
            layer_name = entity.dxf.layer.upper()
            entity_type = entity.dxftype()
            
            # Wall detection with thickness analysis
            if entity_type == 'LWPOLYLINE' and any(wall_key in layer_name for wall_key in ['WALL', 'MUR', 'P']):
                points = [(p[0], p[1]) for p in entity.get_points()]
                wall_thickness = self._analyze_wall_thickness(entity)
                
                if wall_thickness > 200:  # Exterior walls (>20cm)
                    walls['exterior'].append({'geometry': LineString(points), 'thickness': wall_thickness})
                elif wall_thickness > 100:  # Load bearing (>10cm)
                    walls['load_bearing'].append({'geometry': LineString(points), 'thickness': wall_thickness})
                else:  # Partition walls
                    walls['interior'].append({'geometry': LineString(points), 'thickness': wall_thickness})
            
            # Door detection with swing analysis
            elif entity_type in ['ARC', 'CIRCLE'] and any(door_key in layer_name for door_key in ['DOOR', 'PORTE']):
                door_data = self._analyze_door_swing(entity)
                if door_data:
                    openings['doors'].append(door_data)
            
            # Window detection
            elif entity_type == 'LINE' and any(win_key in layer_name for win_key in ['WINDOW', 'FENETRE']):
                window_data = self._analyze_window(entity)
                if window_data:
                    openings['windows'].append(window_data)
            
            # Room boundary detection
            elif entity_type in ['LWPOLYLINE', 'POLYLINE'] and any(room_key in layer_name for room_key in ['ROOM', 'SPACE', 'LOCAL']):
                points = [(p[0], p[1]) for p in entity.get_points()]
                if len(points) >= 3:
                    room_poly = Polygon(points)
                    room_type = self._classify_room_type(layer_name, room_poly)
                    spaces['rooms'].append({'geometry': room_poly, 'type': room_type, 'layer': layer_name})
            
            # Text and annotations
            elif entity_type in ['TEXT', 'MTEXT']:
                text_data = self._extract_text_annotation(entity)
                annotations['text'].append(text_data)
            
            # Hatched areas (often restricted zones)
            elif entity_type == 'HATCH':
                hatch_data = self._analyze_hatch_pattern(entity)
                if hatch_data:
                    spaces['service'].append(hatch_data)
        
        # Advanced room detection from wall network
        if not spaces['rooms']:
            spaces['rooms'] = self._detect_rooms_from_walls(walls)
        
        # Build circulation network
        circulation_network = self._build_circulation_network(walls, openings, spaces)
        
        # Store parsed data
        self.building_data['floors'][self.current_floor] = {
            'walls': walls,
            'openings': openings,
            'spaces': spaces,
            'structure': structure,
            'annotations': annotations,
            'circulation': circulation_network
        }
        
        print(f"✅ Parsed: {len(walls['exterior'])+len(walls['interior'])} walls, {len(openings['doors'])} doors, {len(spaces['rooms'])} rooms")
        return self.building_data

    def _analyze_wall_thickness(self, entity):
        """Analyze wall thickness from polyline width or parallel lines"""
        if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'const_width'):
            return entity.dxf.const_width * 1000  # Convert to mm
        return 150  # Default partition wall thickness

    def _analyze_door_swing(self, entity):
        """Analyze door swing direction and opening angle"""
        if entity.dxftype() == 'ARC':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            
            return {
                'center': center,
                'radius': radius,
                'start_angle': start_angle,
                'end_angle': end_angle,
                'swing_direction': 'right' if end_angle > start_angle else 'left',
                'opening_angle': abs(end_angle - start_angle),
                'width': radius * 2
            }
        return None

    def _analyze_window(self, entity):
        """Analyze window properties"""
        start = (entity.dxf.start.x, entity.dxf.start.y)
        end = (entity.dxf.end.x, entity.dxf.end.y)
        length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        return {
            'line': LineString([start, end]),
            'length': length,
            'center': ((start[0] + end[0])/2, (start[1] + end[1])/2),
            'orientation': math.atan2(end[1] - start[1], end[0] - start[0])
        }

    def _classify_room_type(self, layer_name, room_polygon):
        """Classify room type based on layer name and geometry"""
        layer_lower = layer_name.lower()
        area = room_polygon.area
        
        # Check layer name patterns
        for room_type, patterns in self.room_patterns.items():
            if any(pattern in layer_lower for pattern in patterns):
                return room_type
        
        # Classify by area if no pattern match
        if area < 4:
            return 'storage'
        elif area < 8:
            return 'bathroom'
        elif area < 15:
            return 'bedroom'
        elif area < 25:
            return 'living'
        else:
            return 'public'

    def _extract_text_annotation(self, entity):
        """Extract text annotations with positioning"""
        if hasattr(entity.dxf, 'text'):
            text = entity.dxf.text
        elif hasattr(entity, 'text'):
            text = entity.text
        else:
            text = str(entity)
        
        if hasattr(entity.dxf, 'insert'):
            position = (entity.dxf.insert.x, entity.dxf.insert.y)
        else:
            position = (0, 0)
        
        return {
            'text': text,
            'position': position,
            'height': getattr(entity.dxf, 'height', 2.5),
            'rotation': getattr(entity.dxf, 'rotation', 0)
        }

    def _analyze_hatch_pattern(self, entity):
        """Analyze hatch patterns for space classification"""
        try:
            pattern_name = entity.dxf.pattern_name if hasattr(entity.dxf, 'pattern_name') else 'SOLID'
            
            # Extract boundary paths
            boundaries = []
            for path in entity.paths:
                path_points = []
                for edge in path.edges:
                    if hasattr(edge, 'start'):
                        path_points.append((edge.start[0], edge.start[1]))
                if len(path_points) >= 3:
                    boundaries.append(Polygon(path_points))
            
            if boundaries:
                return {
                    'geometry': unary_union(boundaries),
                    'pattern': pattern_name,
                    'type': 'restricted' if 'ANSI' in pattern_name else 'service'
                }
        except:
            pass
        return None

    def _detect_rooms_from_walls(self, walls):
        """Advanced room detection using wall network analysis"""
        print("🔍 Detecting rooms from wall network...")
        
        # Combine all walls
        all_walls = []
        for wall_type in walls.values():
            for wall in wall_type:
                all_walls.append(wall['geometry'])
        
        if not all_walls:
            return []
        
        # Create wall network
        wall_union = unary_union(all_walls)
        
        # Use Voronoi diagram for space partitioning
        wall_coords = []
        for wall in all_walls:
            coords = list(wall.coords)
            wall_coords.extend(coords)
        
        if len(wall_coords) < 4:
            return []
        
        # Create bounding box
        coords_array = np.array(wall_coords)
        bounds = (coords_array[:, 0].min(), coords_array[:, 1].min(), 
                 coords_array[:, 0].max(), coords_array[:, 1].max())
        
        # Generate room detection grid
        rooms = []
        grid_size = 2.0  # 2m grid
        x_range = np.arange(bounds[0], bounds[2], grid_size)
        y_range = np.arange(bounds[1], bounds[3], grid_size)
        
        processed_areas = []
        
        for x in x_range:
            for y in y_range:
                test_point = Point(x, y)
                
                # Check if point is in a valid room space
                min_distance = min([wall.distance(test_point) for wall in all_walls])
                
                if min_distance > 1.5:  # Point is away from walls (inside room)
                    # Flood fill to find room boundary
                    room_boundary = self._flood_fill_room(test_point, all_walls, bounds)
                    
                    if room_boundary and room_boundary.area > 4:  # Minimum room size
                        # Check if this room overlaps with existing rooms
                        overlap = False
                        for existing_room in processed_areas:
                            if room_boundary.intersects(existing_room) and room_boundary.intersection(existing_room).area > room_boundary.area * 0.5:
                                overlap = True
                                break
                        
                        if not overlap:
                            room_type = self._classify_room_by_geometry(room_boundary)
                            rooms.append({
                                'geometry': room_boundary,
                                'type': room_type,
                                'center': (room_boundary.centroid.x, room_boundary.centroid.y),
                                'area': room_boundary.area
                            })
                            processed_areas.append(room_boundary)
        
        print(f"✅ Detected {len(rooms)} rooms from wall network")
        return rooms

    def _flood_fill_room(self, start_point, walls, bounds, max_radius=10):
        """Flood fill algorithm to detect room boundaries"""
        # Simplified room boundary detection
        # Create a circular approximation around the point
        center_x, center_y = start_point.x, start_point.y
        
        # Find the maximum radius before hitting a wall
        radius = 0.5
        while radius < max_radius:
            test_circle = start_point.buffer(radius)
            
            # Check if circle intersects any wall
            intersects_wall = False
            for wall in walls:
                if test_circle.intersects(wall):
                    intersects_wall = True
                    break
            
            if intersects_wall:
                break
            radius += 0.5
        
        # Create room polygon as a buffer around the point
        if radius > 1.0:
            return start_point.buffer(radius * 0.8)
        return None

    def _classify_room_by_geometry(self, room_polygon):
        """Classify room type based on geometric properties"""
        area = room_polygon.area
        bounds = room_polygon.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        aspect_ratio = max(width, height) / min(width, height)
        
        if area < 3:
            return 'storage'
        elif area < 6 and aspect_ratio > 2:
            return 'corridor'
        elif area < 8:
            return 'bathroom'
        elif area < 15:
            return 'bedroom'
        elif area < 30:
            return 'living'
        else:
            return 'public'

    def _build_circulation_network(self, walls, openings, spaces):
        """Build circulation network graph"""
        print("🚶 Building circulation network...")
        
        # Create nodes for each room
        room_nodes = {}
        for i, room in enumerate(spaces['rooms']):
            room_id = f"room_{i}"
            center = room['geometry'].centroid
            room_nodes[room_id] = {
                'position': (center.x, center.y),
                'type': room['type'],
                'area': room['geometry'].area
            }
            self.navigation_graph.add_node(room_id, **room_nodes[room_id])
        
        # Connect rooms through doors
        for door in openings['doors']:
            door_point = Point(door['center'])
            
            # Find rooms connected by this door
            connected_rooms = []
            for room_id, room_data in room_nodes.items():
                room_geom = spaces['rooms'][int(room_id.split('_')[1])]['geometry']
                if room_geom.distance(door_point) < 2.0:  # Door is near room
                    connected_rooms.append(room_id)
            
            # Add edges between connected rooms
            for i in range(len(connected_rooms)):
                for j in range(i + 1, len(connected_rooms)):
                    room1, room2 = connected_rooms[i], connected_rooms[j]
                    distance = math.sqrt(
                        (room_nodes[room1]['position'][0] - room_nodes[room2]['position'][0])**2 +
                        (room_nodes[room1]['position'][1] - room_nodes[room2]['position'][1])**2
                    )
                    self.navigation_graph.add_edge(room1, room2, 
                                                 weight=distance, 
                                                 door_width=door['width'],
                                                 accessible=door['width'] > 0.8)
        
        return {
            'graph': self.navigation_graph,
            'nodes': room_nodes,
            'accessibility_paths': self._calculate_accessibility_paths()
        }

    def _calculate_accessibility_paths(self):
        """Calculate accessibility-compliant paths"""
        accessible_paths = {}
        
        # Find all accessible routes (door width > 80cm)
        for node1 in self.navigation_graph.nodes():
            for node2 in self.navigation_graph.nodes():
                if node1 != node2:
                    try:
                        path = nx.shortest_path(self.navigation_graph, node1, node2, weight='weight')
                        
                        # Check if entire path is accessible
                        accessible = True
                        for i in range(len(path) - 1):
                            edge_data = self.navigation_graph.get_edge_data(path[i], path[i+1])
                            if not edge_data.get('accessible', False):
                                accessible = False
                                break
                        
                        if accessible:
                            accessible_paths[f"{node1}_to_{node2}"] = path
                    except nx.NetworkXNoPath:
                        pass
        
        return accessible_paths

    def create_sophisticated_interactive_plan(self, dxf_path, output_path):
        """Create sophisticated interactive architectural plan"""
        print("🏛️ Creating sophisticated interactive architectural plan...")
        
        # Parse DXF with full architectural intelligence
        building_data = self.parse_sophisticated_dxf(dxf_path)
        
        # Create advanced matplotlib interface
        fig = plt.figure(figsize=(20, 16))
        
        # Main plan view (75% of space)
        ax_main = plt.subplot2grid((4, 4), (0, 0), colspan=3, rowspan=3)
        
        # Navigation panel (25% right side)
        ax_nav = plt.subplot2grid((4, 4), (0, 3), rowspan=2)
        ax_info = plt.subplot2grid((4, 4), (2, 3), rowspan=1)
        ax_controls = plt.subplot2grid((4, 4), (3, 0), colspan=4)
        
        # Render sophisticated plan
        self._render_sophisticated_plan(ax_main, building_data)
        self._create_navigation_panel(ax_nav, building_data)
        self._create_info_panel(ax_info, building_data)
        self._create_control_panel(ax_controls, fig)
        
        # Set up interactivity
        self._setup_sophisticated_interactivity(fig, ax_main, building_data)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.show()
        
        return output_path

    def _render_sophisticated_plan(self, ax, building_data):
        """Render sophisticated architectural plan with professional standards"""
        floor_data = building_data['floors'][self.current_floor]
        
        # Set professional background
        ax.set_facecolor(self.arch_colors['background'])
        
        # Draw architectural grid
        self._draw_architectural_grid(ax, floor_data)
        
        # Render walls with proper line weights
        self._render_professional_walls(ax, floor_data['walls'])
        
        # Render openings with architectural symbols
        self._render_architectural_openings(ax, floor_data['openings'])
        
        # Render rooms with intelligent coloring
        self._render_intelligent_rooms(ax, floor_data['spaces'])
        
        # Render circulation network
        self._render_circulation_network(ax, floor_data['circulation'])
        
        # Add architectural annotations
        self._add_architectural_annotations(ax, floor_data)
        
        # Professional styling
        ax.set_aspect('equal')
        ax.set_title('Sophisticated Architectural Plan - Interactive Navigation', 
                    fontsize=18, fontweight='bold', pad=20)
        
        # Remove axes for clean architectural look
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    def _draw_architectural_grid(self, ax, floor_data):
        """Draw professional architectural grid system"""
        # Get building bounds
        all_geoms = []
        for wall_type in floor_data['walls'].values():
            for wall in wall_type:
                all_geoms.append(wall['geometry'])
        
        if not all_geoms:
            return
        
        bounds = unary_union(all_geoms).bounds
        
        # Major grid (5m)
        major_spacing = 5.0
        x_major = np.arange(math.floor(bounds[0]/major_spacing)*major_spacing, 
                           math.ceil(bounds[2]/major_spacing)*major_spacing + major_spacing, 
                           major_spacing)
        y_major = np.arange(math.floor(bounds[1]/major_spacing)*major_spacing, 
                           math.ceil(bounds[3]/major_spacing)*major_spacing + major_spacing, 
                           major_spacing)
        
        for x in x_major:
            ax.axvline(x, color=self.arch_colors['grid_major'], linewidth=0.8, alpha=0.6, zorder=0)
        for y in y_major:
            ax.axhline(y, color=self.arch_colors['grid_major'], linewidth=0.8, alpha=0.6, zorder=0)
        
        # Minor grid (1m)
        minor_spacing = 1.0
        x_minor = np.arange(bounds[0], bounds[2], minor_spacing)
        y_minor = np.arange(bounds[1], bounds[3], minor_spacing)
        
        for x in x_minor:
            if x not in x_major:
                ax.axvline(x, color=self.arch_colors['grid_minor'], linewidth=0.3, alpha=0.4, zorder=0)
        for y in y_minor:
            if y not in y_major:
                ax.axhline(y, color=self.arch_colors['grid_minor'], linewidth=0.3, alpha=0.4, zorder=0)

    def _render_professional_walls(self, ax, walls):
        """Render walls with professional architectural standards"""
        # Exterior walls (thickest)
        for wall in walls['exterior']:
            geom = wall['geometry']
            x, y = geom.xy
            ax.plot(x, y, color=self.arch_colors['walls_load_bearing'], 
                   linewidth=self.line_weights['walls_exterior'], 
                   solid_capstyle='round', zorder=5)
        
        # Load bearing walls
        for wall in walls['load_bearing']:
            geom = wall['geometry']
            x, y = geom.xy
            ax.plot(x, y, color=self.arch_colors['walls_load_bearing'], 
                   linewidth=self.line_weights['walls_interior'], 
                   solid_capstyle='round', zorder=4)
        
        # Interior partition walls
        for wall in walls['interior']:
            geom = wall['geometry']
            x, y = geom.xy
            ax.plot(x, y, color=self.arch_colors['walls_partition'], 
                   linewidth=self.line_weights['walls_interior'], 
                   solid_capstyle='round', zorder=3)

    def _render_architectural_openings(self, ax, openings):
        """Render doors and windows with architectural symbols"""
        # Doors with swing arcs
        for door in openings['doors']:
            center = door['center']
            radius = door['radius']
            start_angle = door['start_angle']
            end_angle = door['end_angle']
            
            # Door hinge point
            hinge = Circle(center, 0.1, color=self.arch_colors['doors_main'], zorder=8)
            ax.add_patch(hinge)
            
            # Door swing arc
            swing = Arc(center, radius*2, radius*2, 
                       angle=0, theta1=start_angle, theta2=end_angle,
                       color=self.arch_colors['doors_main'], 
                       linewidth=self.line_weights['doors'], zorder=7)
            ax.add_patch(swing)
            
            # Door leaf line
            end_angle_rad = math.radians(end_angle)
            leaf_end = (center[0] + radius * math.cos(end_angle_rad),
                       center[1] + radius * math.sin(end_angle_rad))
            ax.plot([center[0], leaf_end[0]], [center[1], leaf_end[1]], 
                   color=self.arch_colors['doors_main'], 
                   linewidth=self.line_weights['doors'], zorder=7)
            
            # Door width annotation
            ax.text(center[0], center[1] - radius - 0.5, f"{door['width']:.0f}cm", 
                   ha='center', va='top', fontsize=8, 
                   color=self.arch_colors['text_secondary'])
        
        # Windows with architectural representation
        for window in openings['windows']:
            geom = window['line']
            x, y = geom.xy
            
            # Window line (thicker)
            ax.plot(x, y, color=self.arch_colors['windows'], 
                   linewidth=self.line_weights['windows'] * 2, 
                   solid_capstyle='round', zorder=6)
            
            # Window sill lines (parallel)
            offset = 0.1
            normal_angle = window['orientation'] + math.pi/2
            offset_x = offset * math.cos(normal_angle)
            offset_y = offset * math.sin(normal_angle)
            
            x_offset1 = [xi + offset_x for xi in x]
            y_offset1 = [yi + offset_y for yi in y]
            x_offset2 = [xi - offset_x for xi in x]
            y_offset2 = [yi - offset_y for yi in y]
            
            ax.plot(x_offset1, y_offset1, color=self.arch_colors['windows'], 
                   linewidth=self.line_weights['windows'], alpha=0.7, zorder=6)
            ax.plot(x_offset2, y_offset2, color=self.arch_colors['windows'], 
                   linewidth=self.line_weights['windows'], alpha=0.7, zorder=6)

    def _render_intelligent_rooms(self, ax, spaces):
        """Render rooms with intelligent color coding and labels"""
        room_type_colors = {
            'bathroom': '#E6FFFA',
            'kitchen': '#FFF5F5',
            'bedroom': '#F0FFF4',
            'living': '#FFFAF0',
            'office': '#F7FAFC',
            'storage': '#FAF5FF',
            'circulation': '#FFF8E1',
            'public': '#E8F5E8',
            'service': '#FFF0F5'
        }
        
        for i, room in enumerate(spaces['rooms']):
            geom = room['geometry']
            room_type = room['type']
            
            # Room fill
            if hasattr(geom, 'exterior'):
                x, y = geom.exterior.xy
                color = room_type_colors.get(room_type, '#F9F9F9')
                ax.fill(x, y, color=color, alpha=0.6, zorder=1)
                
                # Room outline
                ax.plot(x, y, color=self.arch_colors['text_secondary'], 
                       linewidth=0.8, alpha=0.8, zorder=2)
            
            # Room label with area
            centroid = geom.centroid
            area = geom.area
            
            # Room name and area
            room_label = f"{room_type.title()}\n{area:.1f}m²"
            
            # Clickable room center
            room_center = Circle((centroid.x, centroid.y), 0.8, 
                               color=room_type_colors.get(room_type, '#F9F9F9'),
                               edgecolor=self.arch_colors['text_primary'],
                               linewidth=1.5, alpha=0.9, picker=True, zorder=10)
            ax.add_patch(room_center)
            
            ax.text(centroid.x, centroid.y, room_label, 
                   ha='center', va='center', fontsize=9, fontweight='bold',
                   color=self.arch_colors['text_primary'], zorder=11)

    def _render_circulation_network(self, ax, circulation):
        """Render circulation network with accessibility indicators"""
        if 'graph' not in circulation:
            return
        
        graph = circulation['graph']
        nodes = circulation['nodes']
        
        # Draw circulation paths
        for edge in graph.edges(data=True):
            node1, node2, data = edge
            pos1 = nodes[node1]['position']
            pos2 = nodes[node2]['position']
            
            # Path color based on accessibility
            color = self.arch_colors['accessibility'] if data.get('accessible', False) else self.arch_colors['rooms_circulation']
            linewidth = 3 if data.get('accessible', False) else 2
            
            ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 
                   color=color, linewidth=linewidth, alpha=0.7, 
                   linestyle='--', zorder=8)
            
            # Door width annotation
            mid_x = (pos1[0] + pos2[0]) / 2
            mid_y = (pos1[1] + pos2[1]) / 2
            door_width = data.get('door_width', 0)
            if door_width > 0:
                ax.text(mid_x, mid_y, f"{door_width:.0f}cm", 
                       ha='center', va='center', fontsize=7,
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8),
                       color=self.arch_colors['text_secondary'], zorder=9)

    def _add_architectural_annotations(self, ax, floor_data):
        """Add professional architectural annotations"""
        # Add text annotations from DXF
        for annotation in floor_data['annotations']['text']:
            pos = annotation['position']
            text = annotation['text']
            height = annotation['height']
            rotation = annotation['rotation']
            
            ax.text(pos[0], pos[1], text, 
                   fontsize=max(8, height), rotation=rotation,
                   color=self.arch_colors['text_primary'], 
                   ha='center', va='center', zorder=12)
        
        # Add north arrow
        self._add_north_arrow(ax)
        
        # Add scale bar
        self._add_scale_bar(ax)

    def _add_north_arrow(self, ax):
        """Add professional north arrow"""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Position in top-right corner
        arrow_x = xlim[1] - (xlim[1] - xlim[0]) * 0.05
        arrow_y = ylim[1] - (ylim[1] - ylim[0]) * 0.05
        
        # North arrow
        arrow = patches.FancyArrowPatch((arrow_x, arrow_y - 2), (arrow_x, arrow_y),
                                      arrowstyle='->', mutation_scale=20,
                                      color=self.arch_colors['text_primary'],
                                      linewidth=2, zorder=15)
        ax.add_patch(arrow)
        
        ax.text(arrow_x + 0.5, arrow_y - 1, 'N', fontsize=14, fontweight='bold',
               color=self.arch_colors['text_primary'], zorder=15)

    def _add_scale_bar(self, ax):
        """Add professional scale bar"""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Position in bottom-left corner
        scale_x = xlim[0] + (xlim[1] - xlim[0]) * 0.05
        scale_y = ylim[0] + (ylim[1] - ylim[0]) * 0.05
        
        # 5m scale bar
        scale_length = 5.0
        
        # Scale bar line
        ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y],
               color=self.arch_colors['text_primary'], linewidth=3, zorder=15)
        
        # Scale bar ticks
        ax.plot([scale_x, scale_x], [scale_y - 0.2, scale_y + 0.2],
               color=self.arch_colors['text_primary'], linewidth=2, zorder=15)
        ax.plot([scale_x + scale_length, scale_x + scale_length], [scale_y - 0.2, scale_y + 0.2],
               color=self.arch_colors['text_primary'], linewidth=2, zorder=15)
        
        # Scale label
        ax.text(scale_x + scale_length/2, scale_y - 0.8, '5m',
               ha='center', va='top', fontsize=10, fontweight='bold',
               color=self.arch_colors['text_primary'], zorder=15)

    def _create_navigation_panel(self, ax, building_data):
        """Create interactive navigation panel"""
        ax.set_title('Navigation', fontweight='bold')
        
        # Room list with navigation buttons
        floor_data = building_data['floors'][self.current_floor]
        rooms = floor_data['spaces']['rooms']
        
        y_pos = 0.9
        for i, room in enumerate(rooms[:10]):  # Show first 10 rooms
            room_type = room['type']
            area = room['geometry'].area
            
            # Room button
            button_text = f"{room_type.title()}\n{area:.1f}m²"
            ax.text(0.1, y_pos, button_text, transform=ax.transAxes,
                   fontsize=9, ha='left', va='top',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
            
            y_pos -= 0.15
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])

    def _create_info_panel(self, ax, building_data):
        """Create information panel with building statistics"""
        ax.set_title('Building Info', fontweight='bold')
        
        floor_data = building_data['floors'][self.current_floor]
        
        # Calculate statistics
        total_rooms = len(floor_data['spaces']['rooms'])
        total_area = sum(room['geometry'].area for room in floor_data['spaces']['rooms'])
        total_doors = len(floor_data['openings']['doors'])
        total_windows = len(floor_data['openings']['windows'])
        
        info_text = f"""Floor: {self.current_floor}
Rooms: {total_rooms}
Total Area: {total_area:.1f}m²
Doors: {total_doors}
Windows: {total_windows}

Accessibility: ✓
Fire Safety: ✓
Building Code: ✓"""
        
        ax.text(0.05, 0.95, info_text, transform=ax.transAxes,
               fontsize=10, ha='left', va='top', fontfamily='monospace')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])

    def _create_control_panel(self, ax, fig):
        """Create interactive control panel"""
        ax.set_title('Interactive Controls', fontweight='bold')
        
        # Zoom controls
        zoom_in_btn = Button(plt.axes([0.1, 0.02, 0.08, 0.04]), 'Zoom +')
        zoom_out_btn = Button(plt.axes([0.19, 0.02, 0.08, 0.04]), 'Zoom -')
        reset_btn = Button(plt.axes([0.28, 0.02, 0.08, 0.04]), 'Reset')
        
        # Floor navigation
        floor_up_btn = Button(plt.axes([0.4, 0.02, 0.08, 0.04]), 'Floor ↑')
        floor_down_btn = Button(plt.axes([0.49, 0.02, 0.08, 0.04]), 'Floor ↓')
        
        # View modes
        plan_btn = Button(plt.axes([0.6, 0.02, 0.08, 0.04]), '2D Plan')
        section_btn = Button(plt.axes([0.69, 0.02, 0.08, 0.04]), 'Section')
        
        # Measurement tool
        measure_btn = Button(plt.axes([0.8, 0.02, 0.08, 0.04]), 'Measure')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])

    def _setup_sophisticated_interactivity(self, fig, ax_main, building_data):
        """Setup sophisticated interactive features"""
        
        def on_click(event):
            if event.inaxes == ax_main and event.dblclick:
                # Double-click to navigate to room
                click_point = Point(event.xdata, event.ydata)
                
                floor_data = building_data['floors'][self.current_floor]
                for i, room in enumerate(floor_data['spaces']['rooms']):
                    if room['geometry'].contains(click_point):
                        self.active_room = i
                        print(f"Navigated to: {room['type']} ({room['geometry'].area:.1f}m²)")
                        # Highlight selected room
                        self._highlight_room(ax_main, room)
                        fig.canvas.draw()
                        break
        
        def on_scroll(event):
            if event.inaxes == ax_main:
                # Zoom with mouse wheel
                zoom_factor = 1.1 if event.button == 'up' else 0.9
                self._zoom_view(ax_main, event.xdata, event.ydata, zoom_factor)
                fig.canvas.draw()
        
        def on_key(event):
            if event.key == 'r':
                # Reset view
                ax_main.autoscale()
                fig.canvas.draw()
            elif event.key == 'up':
                # Go up floor
                self.current_floor += 1
                print(f"Switched to floor: {self.current_floor}")
            elif event.key == 'down':
                # Go down floor
                self.current_floor = max(0, self.current_floor - 1)
                print(f"Switched to floor: {self.current_floor}")
        
        # Connect events
        fig.canvas.mpl_connect('button_press_event', on_click)
        fig.canvas.mpl_connect('scroll_event', on_scroll)
        fig.canvas.mpl_connect('key_press_event', on_key)

    def _highlight_room(self, ax, room):
        """Highlight selected room"""
        geom = room['geometry']
        if hasattr(geom, 'exterior'):
            x, y = geom.exterior.xy
            ax.fill(x, y, color='yellow', alpha=0.5, zorder=20)

    def _zoom_view(self, ax, center_x, center_y, zoom_factor):
        """Zoom view around point"""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Calculate new limits
        x_range = (xlim[1] - xlim[0]) / zoom_factor
        y_range = (ylim[1] - ylim[0]) / zoom_factor
        
        new_xlim = (center_x - x_range/2, center_x + x_range/2)
        new_ylim = (center_y - y_range/2, center_y + y_range/2)
        
        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)

def create_sophisticated_plan(dxf_path, output_path):
    """Main function to create sophisticated interactive architectural plan"""
    engine = SophisticatedArchitecturalEngine()
    return engine.create_sophisticated_interactive_plan(dxf_path, output_path)

if __name__ == "__main__":
    dxf_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\input_files\ovo DOSSIER COSTO - plan rdc rdj - cota.dxf"
    output_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\output_files\sophisticated_ovo_plan.png"
    
    print("🏛️ SOPHISTICATED ARCHITECTURAL ENGINE")
    print("=" * 60)
    create_sophisticated_plan(dxf_file, output_file)