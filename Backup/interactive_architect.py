#!/usr/bin/env python3

import ezdxf
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
import numpy as np

class InteractiveArchitectPlan:
    def __init__(self):
        self.rooms = {}
        self.stairs = []
        self.doors = []
        self.windows = []
        self.current_floor = 0
        self.zoom_level = 1.0
        
    def parse_architectural_elements(self, dxf_path):
        """Parse DXF into proper architectural elements"""
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        walls = []
        room_boundaries = []
        
        for entity in msp:
            layer = entity.dxf.layer.upper()
            
            if entity.dxftype() == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                
                if 'WALL' in layer or layer == 'P':
                    walls.append(LineString(points))
                elif 'ROOM' in layer or 'SPACE' in layer:
                    if len(points) >= 3:
                        room_boundaries.append(Polygon(points))
                elif 'STAIR' in layer:
                    self.stairs.append({'geometry': Polygon(points), 'floor': 0})
        
        # Auto-detect rooms from wall intersections
        self._detect_rooms_from_walls(walls)
        
        return walls, room_boundaries
    
    def _detect_rooms_from_walls(self, walls):
        """Detect rooms from wall network"""
        # Simplified room detection - find enclosed areas
        wall_union = unary_union(walls)
        
        # Create grid points and test which are enclosed
        bounds = wall_union.bounds
        x_range = np.linspace(bounds[0], bounds[2], 50)
        y_range = np.linspace(bounds[1], bounds[3], 50)
        
        room_id = 0
        for x in x_range[::5]:
            for y in y_range[::5]:
                pt = Point(x, y)
                # If point is far from walls, it's likely inside a room
                if wall_union.distance(pt) > 2:
                    self.rooms[f"Room_{room_id}"] = {
                        'center': (x, y),
                        'type': 'general',
                        'floor': 0,
                        'accessible': True
                    }
                    room_id += 1
    
    def create_interactive_plan(self, dxf_path, output_path):
        """Create interactive architectural plan"""
        walls, room_boundaries = self.parse_architectural_elements(dxf_path)
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Draw walls as thick lines
        for wall in walls:
            x, y = wall.xy
            ax.plot(x, y, color='#2D3748', linewidth=4, solid_capstyle='round')
        
        # Draw rooms with navigation points
        colors = ['#E6FFFA', '#F0FFF4', '#FFF5F5', '#FFFAF0', '#F7FAFC']
        for i, (room_name, room_data) in enumerate(self.rooms.items()):
            center = room_data['center']
            
            # Room indicator
            circle = plt.Circle(center, 1.5, 
                              color=colors[i % len(colors)], 
                              alpha=0.7, 
                              picker=True)
            ax.add_patch(circle)
            
            # Room label with navigation
            ax.text(center[0], center[1], room_name, 
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Add stairs with floor navigation
        for stair in self.stairs:
            geom = stair['geometry']
            if hasattr(geom, 'exterior'):
                x, y = geom.exterior.xy
                ax.fill(x, y, color='#4A5568', alpha=0.8, picker=True)
                
                centroid = geom.centroid
                ax.text(centroid.x, centroid.y, '↕\nSTAIRS', 
                       ha='center', va='center', color='white', fontweight='bold')
        
        # Interactive controls
        self._add_navigation_controls(fig, ax)
        
        ax.set_aspect('equal')
        ax.set_title('Interactive Architectural Plan - Click to Navigate', fontsize=16, fontweight='bold')
        
        # Event handlers
        fig.canvas.mpl_connect('pick_event', self._on_click)
        fig.canvas.mpl_connect('scroll_event', self._on_scroll)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        return output_path
    
    def _add_navigation_controls(self, fig, ax):
        """Add interactive navigation controls"""
        # Zoom controls
        ax_zoom_in = plt.axes([0.02, 0.95, 0.08, 0.04])
        ax_zoom_out = plt.axes([0.11, 0.95, 0.08, 0.04])
        ax_reset = plt.axes([0.20, 0.95, 0.08, 0.04])
        
        btn_zoom_in = Button(ax_zoom_in, 'Zoom +')
        btn_zoom_out = Button(ax_zoom_out, 'Zoom -')
        btn_reset = Button(ax_reset, 'Reset')
        
        btn_zoom_in.on_clicked(lambda x: self._zoom(ax, 1.2))
        btn_zoom_out.on_clicked(lambda x: self._zoom(ax, 0.8))
        btn_reset.on_clicked(lambda x: self._reset_view(ax))
        
        # Floor navigation
        ax_floor_up = plt.axes([0.02, 0.85, 0.08, 0.04])
        ax_floor_down = plt.axes([0.11, 0.85, 0.08, 0.04])
        
        btn_floor_up = Button(ax_floor_up, 'Floor ↑')
        btn_floor_down = Button(ax_floor_down, 'Floor ↓')
        
        btn_floor_up.on_clicked(lambda x: self._change_floor(ax, 1))
        btn_floor_down.on_clicked(lambda x: self._change_floor(ax, -1))
    
    def _on_click(self, event):
        """Handle room/stair clicks for navigation"""
        if event.artist:
            print(f"Navigating to: {event.artist}")
            # Implement room navigation logic
    
    def _on_scroll(self, event):
        """Handle mouse scroll for zoom"""
        if event.inaxes:
            zoom_factor = 1.1 if event.button == 'up' else 0.9
            self._zoom(event.inaxes, zoom_factor)
    
    def _zoom(self, ax, factor):
        """Zoom in/out"""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        center_x = (xlim[0] + xlim[1]) / 2
        center_y = (ylim[0] + ylim[1]) / 2
        
        width = (xlim[1] - xlim[0]) / factor
        height = (ylim[1] - ylim[0]) / factor
        
        ax.set_xlim(center_x - width/2, center_x + width/2)
        ax.set_ylim(center_y - height/2, center_y + height/2)
        ax.figure.canvas.draw()
    
    def _reset_view(self, ax):
        """Reset to original view"""
        ax.autoscale()
        ax.figure.canvas.draw()
    
    def _change_floor(self, ax, direction):
        """Navigate between floors"""
        self.current_floor += direction
        print(f"Switched to floor: {self.current_floor}")
        # Implement floor switching logic

def create_interactive_plan(dxf_path, output_path):
    """Main function to create interactive architectural plan"""
    architect = InteractiveArchitectPlan()
    return architect.create_interactive_plan(dxf_path, output_path)

if __name__ == "__main__":
    dxf_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\input_files\ovo DOSSIER COSTO - plan rdc rdj - cota.dxf"
    output_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\output_files\interactive_ovo_plan.png"
    
    create_interactive_plan(dxf_file, output_file)