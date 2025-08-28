#!/usr/bin/env python3

import ezdxf
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch, Wedge
from matplotlib.animation import FuncAnimation
from shapely.geometry import Polygon, Point, LineString
import numpy as np
import math
import time

class LivingArchitecture:
    def __init__(self):
        self.building = {}
        self.current_position = (0, 0)
        self.current_room = None
        self.view_angle = 0
        self.zoom_level = 1.0
        self.walking_path = []
        self.animation_active = False
        
        # Living elements
        self.people = []
        self.lighting = {}
        self.furniture = {}
        self.circulation_flow = {}
        
        # Interactive states
        self.door_states = {}  # open/closed
        self.light_states = {}  # on/off
        self.occupancy = {}  # room occupancy
        
    def bring_plan_to_life(self, dxf_path):
        """Transform raw DXF into living architectural space"""
        print("🌟 BRINGING ARCHITECTURE TO LIFE...")
        
        # Parse DXF with intelligence
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        # Extract living elements
        self._extract_living_spaces(msp)
        self._create_circulation_network()
        self._add_lighting_system()
        self._populate_with_people()
        self._setup_interactive_elements()
        
        print(f"✨ Created living building with {len(self.building['rooms'])} spaces")
        
    def _extract_living_spaces(self, msp):
        """Extract spaces as living environments"""
        self.building = {
            'rooms': [],
            'doors': [],
            'windows': [],
            'walls': [],
            'circulation': []
        }
        
        # Process entities with life context
        for entity in msp:
            layer = entity.dxf.layer.upper()
            
            if entity.dxftype() == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                
                # Detect room spaces
                if len(points) >= 3 and self._is_enclosed_space(points):
                    room = self._create_living_room(points, layer)
                    if room:
                        self.building['rooms'].append(room)
                else:
                    # Wall elements
                    wall = self._create_living_wall(points, layer)
                    self.building['walls'].append(wall)
            
            elif entity.dxftype() == 'HATCH':
                # Hatched areas as special zones
                hatch_rooms = self._extract_hatch_spaces(entity)
                self.building['rooms'].extend(hatch_rooms)
        
        # If no rooms detected, create from analysis
        if not self.building['rooms']:
            self.building['rooms'] = self._detect_living_spaces()
    
    def _is_enclosed_space(self, points):
        """Check if points form an enclosed living space"""
        if len(points) < 3:
            return False
        
        # Check closure
        first, last = points[0], points[-1]
        distance = math.sqrt((first[0] - last[0])**2 + (first[1] - last[1])**2)
        
        # Check area
        if distance < 1.0:  # Closed
            area = Polygon(points).area
            return area > 4  # Minimum livable space
        
        return False
    
    def _create_living_room(self, points, layer):
        """Create a living room with interactive properties"""
        poly = Polygon(points)
        if not poly.is_valid:
            return None
        
        area = poly.area
        centroid = poly.centroid
        
        # Determine room function and atmosphere
        room_type = self._classify_living_space(layer, area, points)
        
        return {
            'geometry': poly,
            'type': room_type,
            'area': area,
            'center': (centroid.x, centroid.y),
            'atmosphere': self._create_atmosphere(room_type),
            'lighting': self._setup_room_lighting(room_type, area),
            'furniture': self._place_living_furniture(room_type, poly),
            'occupancy': 0,
            'temperature': self._get_room_temperature(room_type),
            'activity_level': 0.0,
            'accessibility': True,
            'interactive': True
        }
    
    def _classify_living_space(self, layer, area, points):
        """Classify space based on living patterns"""
        layer_lower = layer.lower()
        
        # Layer-based classification
        if any(word in layer_lower for word in ['wc', 'toilet', 'bath']):
            return 'bathroom'
        elif any(word in layer_lower for word in ['kitchen', 'cuisine']):
            return 'kitchen'
        elif any(word in layer_lower for word in ['bedroom', 'chambre']):
            return 'bedroom'
        elif any(word in layer_lower for word in ['living', 'salon']):
            return 'living_room'
        elif any(word in layer_lower for word in ['office', 'bureau']):
            return 'office'
        
        # Area and shape-based classification
        bounds = Polygon(points).bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        aspect_ratio = max(width, height) / min(width, height)
        
        if area < 4:
            return 'storage'
        elif area < 8 and aspect_ratio > 2:
            return 'corridor'
        elif area < 10:
            return 'bathroom'
        elif area < 20:
            return 'bedroom'
        elif area < 40:
            return 'living_room'
        else:
            return 'public_space'
    
    def _create_atmosphere(self, room_type):
        """Create atmospheric properties for each room"""
        atmospheres = {
            'bathroom': {'color': '#E6F3FF', 'mood': 'clean', 'sound': 'water'},
            'kitchen': {'color': '#FFF8E1', 'mood': 'warm', 'sound': 'cooking'},
            'bedroom': {'color': '#F0F8E8', 'mood': 'peaceful', 'sound': 'quiet'},
            'living_room': {'color': '#FFF5F0', 'mood': 'social', 'sound': 'conversation'},
            'office': {'color': '#F8F9FA', 'mood': 'focused', 'sound': 'typing'},
            'corridor': {'color': '#F5F5F5', 'mood': 'transit', 'sound': 'footsteps'},
            'storage': {'color': '#F9F9F9', 'mood': 'utility', 'sound': 'silence'}
        }
        
        return atmospheres.get(room_type, {'color': '#FFFFFF', 'mood': 'neutral', 'sound': 'ambient'})
    
    def _setup_room_lighting(self, room_type, area):
        """Setup intelligent lighting for each room"""
        # Calculate lighting needs
        light_density = {
            'bathroom': 300,  # lux
            'kitchen': 500,
            'bedroom': 150,
            'living_room': 200,
            'office': 400,
            'corridor': 100
        }
        
        required_lux = light_density.get(room_type, 200)
        num_lights = max(1, int(area / 10))  # 1 light per 10m²
        
        return {
            'num_lights': num_lights,
            'required_lux': required_lux,
            'current_level': 0.7,  # 70% brightness
            'auto_control': True,
            'color_temperature': 3000 if room_type == 'bedroom' else 4000
        }
    
    def _place_living_furniture(self, room_type, room_poly):
        """Place living furniture based on room function"""
        furniture_sets = {
            'bathroom': ['toilet', 'sink', 'shower'],
            'kitchen': ['stove', 'refrigerator', 'counter', 'sink'],
            'bedroom': ['bed', 'wardrobe', 'nightstand'],
            'living_room': ['sofa', 'coffee_table', 'tv_stand', 'armchair'],
            'office': ['desk', 'chair', 'bookshelf', 'filing_cabinet']
        }
        
        furniture_list = furniture_sets.get(room_type, [])
        placed_furniture = []
        
        # Simple furniture placement
        centroid = room_poly.centroid
        for i, item in enumerate(furniture_list):
            angle = (2 * math.pi * i) / len(furniture_list)
            offset_x = 1.5 * math.cos(angle)
            offset_y = 1.5 * math.sin(angle)
            
            furniture_pos = (centroid.x + offset_x, centroid.y + offset_y)
            
            # Check if position is inside room
            if room_poly.contains(Point(furniture_pos)):
                placed_furniture.append({
                    'type': item,
                    'position': furniture_pos,
                    'interactive': True,
                    'state': 'available'
                })
        
        return placed_furniture
    
    def _get_room_temperature(self, room_type):
        """Get appropriate temperature for room type"""
        temperatures = {
            'bathroom': 24,  # °C
            'kitchen': 22,
            'bedroom': 20,
            'living_room': 21,
            'office': 22
        }
        return temperatures.get(room_type, 21)
    
    def _create_living_wall(self, points, layer):
        """Create wall with living properties"""
        return {
            'geometry': LineString(points),
            'layer': layer,
            'material': 'concrete' if 'exterior' in layer.lower() else 'drywall',
            'thickness': 200 if 'exterior' in layer.lower() else 100,
            'insulation': True,
            'interactive': False
        }
    
    def _extract_hatch_spaces(self, hatch_entity):
        """Extract living spaces from hatch patterns"""
        spaces = []
        
        try:
            for path in hatch_entity.paths:
                points = []
                for edge in path.edges:
                    if hasattr(edge, 'start'):
                        points.append((edge.start[0], edge.start[1]))
                
                if len(points) >= 3:
                    room = self._create_living_room(points, 'HATCH')
                    if room:
                        room['type'] = 'restricted_zone'
                        room['atmosphere']['color'] = '#FFE6E6'
                        spaces.append(room)
        except:
            pass
        
        return spaces
    
    def _detect_living_spaces(self):
        """Detect living spaces from wall network"""
        print("🔍 Detecting living spaces from walls...")
        
        if not self.building['walls']:
            return []
        
        # Get building bounds
        all_coords = []
        for wall in self.building['walls']:
            all_coords.extend(list(wall['geometry'].coords))
        
        if not all_coords:
            return []
        
        coords_array = np.array(all_coords)
        bounds = (coords_array[:, 0].min(), coords_array[:, 1].min(),
                 coords_array[:, 0].max(), coords_array[:, 1].max())
        
        # Create living spaces grid
        rooms = []
        grid_size = 8
        x_range = np.linspace(bounds[0], bounds[2], grid_size)
        y_range = np.linspace(bounds[1], bounds[3], grid_size)
        
        for x in x_range:
            for y in y_range:
                test_point = Point(x, y)
                
                # Check if point is in open space
                wall_geometries = [wall['geometry'] for wall in self.building['walls']]
                min_distance = min([geom.distance(test_point) for geom in wall_geometries])
                
                if min_distance > 2.0:  # Inside a room
                    # Create room around this point
                    room_size = min(8, min_distance * 1.5)
                    room_poly = test_point.buffer(room_size, resolution=8)
                    
                    # Check for overlaps with existing rooms
                    overlap = False
                    for existing_room in rooms:
                        if room_poly.intersects(existing_room['geometry']):
                            overlap_area = room_poly.intersection(existing_room['geometry']).area
                            if overlap_area > room_poly.area * 0.3:
                                overlap = True
                                break
                    
                    if not overlap and room_poly.area > 6:
                        room_type = self._classify_living_space('', room_poly.area, list(room_poly.exterior.coords))
                        
                        room = {
                            'geometry': room_poly,
                            'type': room_type,
                            'area': room_poly.area,
                            'center': (x, y),
                            'atmosphere': self._create_atmosphere(room_type),
                            'lighting': self._setup_room_lighting(room_type, room_poly.area),
                            'furniture': self._place_living_furniture(room_type, room_poly),
                            'occupancy': 0,
                            'temperature': self._get_room_temperature(room_type),
                            'activity_level': 0.0,
                            'accessibility': True,
                            'interactive': True
                        }
                        
                        rooms.append(room)
        
        print(f"✨ Created {len(rooms)} living spaces")
        return rooms
    
    def _create_circulation_network(self):
        """Create living circulation network"""
        print("🚶 Creating circulation network...")
        
        # Connect rooms through proximity
        for i, room1 in enumerate(self.building['rooms']):
            for j, room2 in enumerate(self.building['rooms']):
                if i != j:
                    distance = math.sqrt(
                        (room1['center'][0] - room2['center'][0])**2 +
                        (room1['center'][1] - room2['center'][1])**2
                    )
                    
                    if distance < 15:  # Rooms are connected
                        connection_id = f"{i}_{j}"
                        self.circulation_flow[connection_id] = {
                            'from_room': i,
                            'to_room': j,
                            'distance': distance,
                            'traffic_level': 0.0,
                            'accessibility': True,
                            'door_required': distance < 8
                        }
    
    def _add_lighting_system(self):
        """Add intelligent lighting system"""
        print("💡 Adding intelligent lighting...")
        
        for i, room in enumerate(self.building['rooms']):
            lighting = room['lighting']
            
            self.lighting[f"room_{i}"] = {
                'brightness': lighting['current_level'],
                'color_temp': lighting['color_temperature'],
                'auto_mode': lighting['auto_control'],
                'motion_sensor': True,
                'dimmer': True,
                'schedule': self._create_lighting_schedule(room['type'])
            }
    
    def _create_lighting_schedule(self, room_type):
        """Create lighting schedule based on room usage"""
        schedules = {
            'bedroom': {'morning': 0.3, 'day': 0.1, 'evening': 0.7, 'night': 0.0},
            'kitchen': {'morning': 0.8, 'day': 0.6, 'evening': 0.9, 'night': 0.2},
            'living_room': {'morning': 0.4, 'day': 0.3, 'evening': 0.8, 'night': 0.1},
            'bathroom': {'morning': 0.9, 'day': 0.7, 'evening': 0.9, 'night': 0.3},
            'office': {'morning': 0.8, 'day': 0.9, 'evening': 0.6, 'night': 0.0}
        }
        
        return schedules.get(room_type, {'morning': 0.5, 'day': 0.5, 'evening': 0.5, 'night': 0.2})
    
    def _populate_with_people(self):
        """Add people to bring life to the space"""
        print("👥 Populating with people...")
        
        # Add people to appropriate rooms
        living_rooms = [room for room in self.building['rooms'] if room['type'] in ['living_room', 'kitchen', 'office']]
        
        for i, room in enumerate(living_rooms[:3]):  # Add people to first 3 suitable rooms
            person = {
                'id': f"person_{i}",
                'position': room['center'],
                'current_room': room,
                'activity': self._get_room_activity(room['type']),
                'movement_pattern': 'stationary',
                'interaction_radius': 2.0
            }
            self.people.append(person)
    
    def _get_room_activity(self, room_type):
        """Get typical activity for room type"""
        activities = {
            'living_room': 'relaxing',
            'kitchen': 'cooking',
            'office': 'working',
            'bedroom': 'sleeping',
            'bathroom': 'personal_care'
        }
        return activities.get(room_type, 'general')
    
    def _setup_interactive_elements(self):
        """Setup interactive elements"""
        print("🎮 Setting up interactive elements...")
        
        # Initialize door states
        for connection_id, connection in self.circulation_flow.items():
            if connection['door_required']:
                self.door_states[connection_id] = 'closed'
        
        # Initialize light states
        for light_id in self.lighting:
            self.light_states[light_id] = 'on'
        
        # Initialize room occupancy
        for i, room in enumerate(self.building['rooms']):
            self.occupancy[f"room_{i}"] = 0
    
    def create_living_visualization(self, output_path):
        """Create living, interactive visualization"""
        print("🎨 Creating living visualization...")
        
        # Create figure with multiple panels
        fig = plt.figure(figsize=(20, 14))
        
        # Main living plan (large panel)
        ax_main = plt.subplot2grid((3, 4), (0, 0), colspan=3, rowspan=2)
        
        # Control panels
        ax_lighting = plt.subplot2grid((3, 4), (0, 3))
        ax_occupancy = plt.subplot2grid((3, 4), (1, 3))
        ax_navigation = plt.subplot2grid((3, 4), (2, 0), colspan=2)
        ax_atmosphere = plt.subplot2grid((3, 4), (2, 2), colspan=2)
        
        # Render living plan
        self._render_living_plan(ax_main)
        self._setup_lighting_control(ax_lighting)
        self._setup_occupancy_display(ax_occupancy)
        self._setup_navigation_control(ax_navigation)
        self._setup_atmosphere_control(ax_atmosphere)
        
        # Setup real-time interactivity
        self._setup_living_interactivity(fig, ax_main)
        
        # Start animation for living elements
        self._start_living_animation(fig, ax_main)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        return output_path
    
    def _render_living_plan(self, ax):
        """Render the living architectural plan"""
        ax.set_facecolor('#F8F9FA')
        ax.set_title('LIVING ARCHITECTURAL SPACE - Interactive Navigation', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Draw walls with material properties
        for wall in self.building['walls']:
            geom = wall['geometry']
            x, y = geom.xy
            
            color = '#2D3748' if wall['material'] == 'concrete' else '#4A5568'
            linewidth = 4 if wall['thickness'] > 150 else 2.5
            
            ax.plot(x, y, color=color, linewidth=linewidth, 
                   solid_capstyle='round', alpha=0.9, zorder=3)
        
        # Draw living rooms with atmosphere
        for i, room in enumerate(self.building['rooms']):
            geom = room['geometry']
            atmosphere = room['atmosphere']
            
            if hasattr(geom, 'exterior'):
                x, y = geom.exterior.xy
                
                # Room fill with atmospheric color
                ax.fill(x, y, color=atmosphere['color'], alpha=0.8, 
                       edgecolor='#6B7280', linewidth=1.5, zorder=1)
                
                # Room center (clickable)
                center = room['center']
                room_circle = Circle(center, 1.0, 
                                   color=atmosphere['color'],
                                   edgecolor='#374151',
                                   linewidth=2, alpha=0.9, 
                                   picker=True, gid=f'room_{i}', zorder=10)
                ax.add_patch(room_circle)
                
                # Room information
                room_info = f"{room['type'].replace('_', ' ').title()}\n"
                room_info += f"{room['area']:.1f}m² | {room['temperature']}°C\n"
                room_info += f"Occupancy: {room['occupancy']}"
                
                ax.text(center[0], center[1], room_info,
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       color='#1F2937', zorder=11)
        
        # Draw people
        for person in self.people:
            pos = person['position']
            person_circle = Circle(pos, 0.5, color='#EF4444', 
                                 edgecolor='#DC2626', linewidth=2,
                                 alpha=0.9, zorder=15)
            ax.add_patch(person_circle)
            
            # Activity indicator
            ax.text(pos[0], pos[1] - 1.5, person['activity'],
                   ha='center', va='top', fontsize=8,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8),
                   zorder=16)
        
        # Draw circulation flow
        for connection_id, connection in self.circulation_flow.items():
            room1 = self.building['rooms'][connection['from_room']]
            room2 = self.building['rooms'][connection['to_room']]
            
            pos1 = room1['center']
            pos2 = room2['center']
            
            # Flow line with traffic indication
            traffic_alpha = 0.3 + (connection['traffic_level'] * 0.7)
            line_color = '#10B981' if connection['accessibility'] else '#EF4444'
            
            ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]],
                   color=line_color, linewidth=2, alpha=traffic_alpha,
                   linestyle='--', zorder=5)
            
            # Door indicator
            if connection['door_required']:
                mid_x = (pos1[0] + pos2[0]) / 2
                mid_y = (pos1[1] + pos2[1]) / 2
                
                door_state = self.door_states.get(connection_id, 'closed')
                door_color = '#22C55E' if door_state == 'open' else '#EF4444'
                
                door_rect = Rectangle((mid_x - 0.3, mid_y - 0.1), 0.6, 0.2,
                                    color=door_color, alpha=0.8, zorder=8)
                ax.add_patch(door_rect)
        
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Add legend
        self._add_living_legend(ax)
    
    def _add_living_legend(self, ax):
        """Add legend for living elements"""
        legend_elements = [
            patches.Patch(color='#EF4444', label='People'),
            patches.Patch(color='#10B981', label='Accessible Path'),
            patches.Patch(color='#22C55E', label='Open Door'),
            patches.Patch(color='#EF4444', label='Closed Door'),
            patches.Circle((0, 0), 0.1, color='#6B7280', label='Room Center (Click)')
        ]
        
        ax.legend(handles=legend_elements, loc='upper right', 
                 bbox_to_anchor=(0.98, 0.98), fontsize=10)
    
    def _setup_lighting_control(self, ax):
        """Setup lighting control panel"""
        ax.set_title('Lighting Control', fontweight='bold')
        
        y_pos = 0.9
        for light_id, light_data in list(self.lighting.items())[:5]:
            room_num = light_id.split('_')[1]
            brightness = light_data['brightness']
            
            # Brightness indicator
            brightness_rect = Rectangle((0.1, y_pos - 0.05), brightness * 0.8, 0.1,
                                      color='#FCD34D', alpha=0.8)
            ax.add_patch(brightness_rect)
            
            ax.text(0.05, y_pos, f"Room {room_num}:",
                   transform=ax.transAxes, fontsize=9, fontweight='bold')
            ax.text(0.95, y_pos, f"{brightness*100:.0f}%",
                   transform=ax.transAxes, fontsize=9, ha='right')
            
            y_pos -= 0.18
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
    
    def _setup_occupancy_display(self, ax):
        """Setup occupancy display"""
        ax.set_title('Room Occupancy', fontweight='bold')
        
        y_pos = 0.9
        for i, room in enumerate(self.building['rooms'][:5]):
            occupancy = room['occupancy']
            room_type = room['type']
            
            # Occupancy bar
            occupancy_rect = Rectangle((0.1, y_pos - 0.05), occupancy * 0.8, 0.1,
                                     color='#3B82F6', alpha=0.7)
            ax.add_patch(occupancy_rect)
            
            ax.text(0.05, y_pos, f"{room_type.title()}:",
                   transform=ax.transAxes, fontsize=9)
            ax.text(0.95, y_pos, f"{occupancy}",
                   transform=ax.transAxes, fontsize=9, ha='right')
            
            y_pos -= 0.18
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
    
    def _setup_navigation_control(self, ax):
        """Setup navigation control"""
        ax.set_title('Navigation & Movement', fontweight='bold')
        
        # Current position indicator
        ax.text(0.05, 0.8, f"Current Position: ({self.current_position[0]:.1f}, {self.current_position[1]:.1f})",
               transform=ax.transAxes, fontsize=10, fontweight='bold')
        
        # Movement controls
        ax.text(0.05, 0.6, "Click rooms to navigate\nUse arrow keys to move\nScroll to zoom",
               transform=ax.transAxes, fontsize=10)
        
        # Walking path
        if self.walking_path:
            ax.text(0.05, 0.3, f"Walking Path: {len(self.walking_path)} steps",
                   transform=ax.transAxes, fontsize=10)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
    
    def _setup_atmosphere_control(self, ax):
        """Setup atmosphere control"""
        ax.set_title('Atmosphere & Environment', fontweight='bold')
        
        # Time of day
        current_time = time.strftime("%H:%M")
        ax.text(0.05, 0.8, f"Time: {current_time}",
               transform=ax.transAxes, fontsize=12, fontweight='bold')
        
        # Environmental controls
        ax.text(0.05, 0.6, "Environment:\n• Temperature: 21°C\n• Humidity: 45%\n• Air Quality: Good",
               transform=ax.transAxes, fontsize=10)
        
        # Activity level
        total_activity = sum(room.get('activity_level', 0) for room in self.building['rooms'])
        ax.text(0.05, 0.3, f"Building Activity: {total_activity:.1f}",
               transform=ax.transAxes, fontsize=10)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
    
    def _setup_living_interactivity(self, fig, ax_main):
        """Setup living interactivity"""
        
        def on_room_click(event):
            if hasattr(event.artist, 'get_gid') and event.artist.get_gid():
                gid = event.artist.get_gid()
                if gid.startswith('room_'):
                    room_idx = int(gid.split('_')[1])
                    room = self.building['rooms'][room_idx]
                    
                    # Navigate to room
                    self.current_position = room['center']
                    self.current_room = room
                    
                    # Update room occupancy
                    room['occupancy'] += 1
                    room['activity_level'] = min(1.0, room['activity_level'] + 0.2)
                    
                    print(f"🚪 Entered {room['type'].title()} - {room['atmosphere']['mood']} atmosphere")
                    print(f"   Temperature: {room['temperature']}°C | Activity: {room['activity_level']:.1f}")
                    
                    # Highlight current room
                    self._highlight_current_room(ax_main, room)
                    fig.canvas.draw()
        
        def on_key_press(event):
            if event.key in ['up', 'down', 'left', 'right']:
                # Move within current room or to adjacent room
                self._handle_movement(event.key)
                fig.canvas.draw()
            elif event.key == 'l':
                # Toggle lights in current room
                self._toggle_room_lights()
                fig.canvas.draw()
            elif event.key == 'd':
                # Open/close nearest door
                self._toggle_nearest_door()
                fig.canvas.draw()
        
        def on_scroll(event):
            if event.inaxes == ax_main:
                # Zoom with perspective
                zoom_factor = 1.1 if event.button == 'up' else 0.9
                self._zoom_with_perspective(ax_main, event.xdata, event.ydata, zoom_factor)
                fig.canvas.draw()
        
        fig.canvas.mpl_connect('pick_event', on_room_click)
        fig.canvas.mpl_connect('key_press_event', on_key_press)
        fig.canvas.mpl_connect('scroll_event', on_scroll)
    
    def _highlight_current_room(self, ax, room):
        """Highlight the current room"""
        geom = room['geometry']
        if hasattr(geom, 'exterior'):
            x, y = geom.exterior.xy
            highlight = patches.Polygon(list(zip(x, y)), 
                                      facecolor='yellow', alpha=0.3, 
                                      edgecolor='orange', linewidth=3, zorder=20)
            ax.add_patch(highlight)
    
    def _handle_movement(self, direction):
        """Handle movement within the living space"""
        move_distance = 2.0
        
        if direction == 'up':
            self.current_position = (self.current_position[0], self.current_position[1] + move_distance)
        elif direction == 'down':
            self.current_position = (self.current_position[0], self.current_position[1] - move_distance)
        elif direction == 'left':
            self.current_position = (self.current_position[0] - move_distance, self.current_position[1])
        elif direction == 'right':
            self.current_position = (self.current_position[0] + move_distance, self.current_position[1])
        
        # Add to walking path
        self.walking_path.append(self.current_position)
        if len(self.walking_path) > 20:  # Keep last 20 positions
            self.walking_path.pop(0)
        
        print(f"🚶 Moved to: ({self.current_position[0]:.1f}, {self.current_position[1]:.1f})")
    
    def _toggle_room_lights(self):
        """Toggle lights in current room"""
        if self.current_room:
            room_id = f"room_{self.building['rooms'].index(self.current_room)}"
            if room_id in self.light_states:
                current_state = self.light_states[room_id]
                self.light_states[room_id] = 'off' if current_state == 'on' else 'on'
                print(f"💡 Lights {self.light_states[room_id]} in {self.current_room['type']}")
    
    def _toggle_nearest_door(self):
        """Toggle nearest door"""
        if not self.current_room:
            return
        
        current_room_idx = self.building['rooms'].index(self.current_room)
        
        # Find nearest door
        nearest_door = None
        min_distance = float('inf')
        
        for connection_id, connection in self.circulation_flow.items():
            if (connection['from_room'] == current_room_idx or 
                connection['to_room'] == current_room_idx) and connection['door_required']:
                
                # Calculate distance to door (simplified)
                other_room_idx = connection['to_room'] if connection['from_room'] == current_room_idx else connection['from_room']
                other_room = self.building['rooms'][other_room_idx]
                
                distance = math.sqrt(
                    (self.current_position[0] - other_room['center'][0])**2 +
                    (self.current_position[1] - other_room['center'][1])**2
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_door = connection_id
        
        if nearest_door:
            current_state = self.door_states.get(nearest_door, 'closed')
            self.door_states[nearest_door] = 'open' if current_state == 'closed' else 'closed'
            print(f"🚪 Door {self.door_states[nearest_door]}")
    
    def _zoom_with_perspective(self, ax, center_x, center_y, zoom_factor):
        """Zoom with architectural perspective"""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        width = (xlim[1] - xlim[0]) / zoom_factor
        height = (ylim[1] - ylim[0]) / zoom_factor
        
        ax.set_xlim(center_x - width/2, center_x + width/2)
        ax.set_ylim(center_y - height/2, center_y + height/2)
    
    def _start_living_animation(self, fig, ax_main):
        """Start animation for living elements"""
        def animate(frame):
            # Animate people movement
            for person in self.people:
                # Simple random movement within room
                if person['current_room']:
                    center = person['current_room']['center']
                    angle = frame * 0.1
                    radius = 1.5
                    
                    new_x = center[0] + radius * math.cos(angle)
                    new_y = center[1] + radius * math.sin(angle)
                    
                    person['position'] = (new_x, new_y)
            
            # Update activity levels
            for room in self.building['rooms']:
                # Simulate natural activity fluctuation
                room['activity_level'] = max(0, room['activity_level'] - 0.01)
            
            return []
        
        # Start animation (commented out to avoid blocking)
        # self.animation = FuncAnimation(fig, animate, interval=100, blit=False)

def create_living_architecture(dxf_path, output_path):
    """Main function to create living architecture"""
    living_arch = LivingArchitecture()
    
    print("🌟 CREATING LIVING ARCHITECTURE")
    print("=" * 50)
    
    # Bring the plan to life
    living_arch.bring_plan_to_life(dxf_path)
    
    # Create living visualization
    return living_arch.create_living_visualization(output_path)

if __name__ == "__main__":
    dxf_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\input_files\ovo DOSSIER COSTO - plan rdc rdj - cota.dxf"
    output_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\output_files\living_ovo_architecture.png"
    
    create_living_architecture(dxf_file, output_file)