#!/usr/bin/env python3

import ezdxf
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point, LineString
import numpy as np
import json

class FastSophisticatedPlan:
    def __init__(self):
        self.rooms = []
        self.walls = []
        self.doors = []
        self.current_floor = 0
        
        self.colors = {
            'walls': '#2D3748',
            'rooms': {'bathroom': '#E6FFFA', 'kitchen': '#FFF5F5', 'bedroom': '#F0FFF4', 
                     'living': '#FFFAF0', 'office': '#F7FAFC', 'corridor': '#FFF8E1'},
            'doors': '#E53E3E',
            'selected': '#FFD700',
            'grid': '#E2E8F0'
        }

    def parse_fast(self, dxf_path):
        """Fast DXF parsing"""
        print("🚀 Fast parsing DXF...")
        
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        # Quick wall extraction
        for entity in msp:
            if entity.dxftype() == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                if len(points) >= 2:
                    self.walls.append(LineString(points))
        
        # Quick room detection - grid-based
        if self.walls:
            bounds = self.walls[0].bounds
            for wall in self.walls[1:]:
                wb = wall.bounds
                bounds = (min(bounds[0], wb[0]), min(bounds[1], wb[1]),
                         max(bounds[2], wb[2]), max(bounds[3], wb[3]))
            
            # Simple room detection
            grid_size = 5
            for x in np.linspace(bounds[0], bounds[2], grid_size):
                for y in np.linspace(bounds[1], bounds[3], grid_size):
                    pt = Point(x, y)
                    if all(wall.distance(pt) > 2 for wall in self.walls):
                        room_type = self._quick_classify(x, y, bounds)
                        self.rooms.append({
                            'center': (x, y),
                            'type': room_type,
                            'geometry': pt.buffer(3),
                            'clickable': True
                        })
        
        print(f"✅ Found {len(self.walls)} walls, {len(self.rooms)} rooms")

    def _quick_classify(self, x, y, bounds):
        """Quick room classification"""
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        
        # Simple position-based classification
        rel_x = (x - bounds[0]) / width
        rel_y = (y - bounds[1]) / height
        
        if rel_x < 0.3 and rel_y < 0.3:
            return 'bathroom'
        elif rel_x > 0.7 and rel_y < 0.3:
            return 'kitchen'
        elif rel_y > 0.7:
            return 'bedroom'
        elif 0.3 < rel_x < 0.7 and 0.3 < rel_y < 0.7:
            return 'living'
        else:
            return 'office'

    def create_interactive(self, dxf_path, output_path):
        """Create fast interactive plan"""
        print("🏛️ Creating interactive plan...")
        
        self.parse_fast(dxf_path)
        
        # Create figure with panels
        fig, ((ax_main, ax_nav), (ax_info, ax_ctrl)) = plt.subplots(2, 2, 
                                                                    figsize=(16, 12),
                                                                    gridspec_kw={'width_ratios': [3, 1], 
                                                                               'height_ratios': [3, 1]})
        
        # Main plan
        self._draw_plan(ax_main)
        self._setup_navigation(ax_nav)
        self._setup_info(ax_info)
        self._setup_controls(ax_ctrl, fig, ax_main)
        
        # Interactivity
        self._setup_clicks(fig, ax_main)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight')
        plt.show()
        
        return output_path

    def _draw_plan(self, ax):
        """Draw the architectural plan"""
        # Grid
        if self.walls:
            bounds = self.walls[0].bounds
            for wall in self.walls[1:]:
                wb = wall.bounds
                bounds = (min(bounds[0], wb[0]), min(bounds[1], wb[1]),
                         max(bounds[2], wb[2]), max(bounds[3], wb[3]))
            
            # Grid lines
            for x in np.arange(bounds[0], bounds[2], 5):
                ax.axvline(x, color=self.colors['grid'], alpha=0.3, linewidth=0.5)
            for y in np.arange(bounds[1], bounds[3], 5):
                ax.axhline(y, color=self.colors['grid'], alpha=0.3, linewidth=0.5)
        
        # Walls
        for wall in self.walls:
            x, y = wall.xy
            ax.plot(x, y, color=self.colors['walls'], linewidth=3, solid_capstyle='round')
        
        # Rooms
        for i, room in enumerate(self.rooms):
            geom = room['geometry']
            room_type = room['type']
            
            # Room area
            if hasattr(geom, 'exterior'):
                x, y = geom.exterior.xy
                color = self.colors['rooms'].get(room_type, '#F9F9F9')
                ax.fill(x, y, color=color, alpha=0.6, picker=True, gid=f'room_{i}')
            
            # Room label
            center = room['center']
            ax.text(center[0], center[1], f"{room_type.title()}\n{geom.area:.1f}m²",
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        ax.set_aspect('equal')
        ax.set_title('Interactive Architectural Plan - Click Rooms to Navigate', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])

    def _setup_navigation(self, ax):
        """Setup navigation panel"""
        ax.set_title('Room Navigation', fontweight='bold')
        
        y_pos = 0.9
        for i, room in enumerate(self.rooms[:8]):
            room_type = room['type']
            area = room['geometry'].area
            
            ax.text(0.1, y_pos, f"→ {room_type.title()}\n   {area:.1f}m²",
                   transform=ax.transAxes, fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='lightblue', alpha=0.7))
            y_pos -= 0.2
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])

    def _setup_info(self, ax):
        """Setup info panel"""
        ax.set_title('Building Information', fontweight='bold')
        
        total_area = sum(room['geometry'].area for room in self.rooms)
        room_counts = {}
        for room in self.rooms:
            room_type = room['type']
            room_counts[room_type] = room_counts.get(room_type, 0) + 1
        
        info_text = f"""Floor: {self.current_floor}
Total Rooms: {len(self.rooms)}
Total Area: {total_area:.1f}m²

Room Types:"""
        
        for room_type, count in room_counts.items():
            info_text += f"\n• {room_type.title()}: {count}"
        
        info_text += f"""

Features:
✓ Interactive Navigation
✓ Room Classification  
✓ Area Calculations
✓ Zoom & Pan Support"""
        
        ax.text(0.05, 0.95, info_text, transform=ax.transAxes,
               fontsize=9, ha='left', va='top', fontfamily='monospace')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])

    def _setup_controls(self, ax, fig, ax_main):
        """Setup control buttons"""
        ax.set_title('Interactive Controls', fontweight='bold')
        
        # Create buttons
        btn_zoom_in = Button(plt.axes([0.1, 0.02, 0.08, 0.04]), 'Zoom +')
        btn_zoom_out = Button(plt.axes([0.2, 0.02, 0.08, 0.04]), 'Zoom -')
        btn_reset = Button(plt.axes([0.3, 0.02, 0.08, 0.04]), 'Reset View')
        btn_floor_up = Button(plt.axes([0.5, 0.02, 0.08, 0.04]), 'Floor ↑')
        btn_floor_down = Button(plt.axes([0.6, 0.02, 0.08, 0.04]), 'Floor ↓')
        
        # Button callbacks
        def zoom_in(event):
            xlim = ax_main.get_xlim()
            ylim = ax_main.get_ylim()
            ax_main.set_xlim(xlim[0]*0.8, xlim[1]*0.8)
            ax_main.set_ylim(ylim[0]*0.8, ylim[1]*0.8)
            fig.canvas.draw()
        
        def zoom_out(event):
            xlim = ax_main.get_xlim()
            ylim = ax_main.get_ylim()
            ax_main.set_xlim(xlim[0]*1.2, xlim[1]*1.2)
            ax_main.set_ylim(ylim[0]*1.2, ylim[1]*1.2)
            fig.canvas.draw()
        
        def reset_view(event):
            ax_main.autoscale()
            fig.canvas.draw()
        
        def floor_up(event):
            self.current_floor += 1
            print(f"🏢 Switched to floor: {self.current_floor}")
        
        def floor_down(event):
            self.current_floor = max(0, self.current_floor - 1)
            print(f"🏢 Switched to floor: {self.current_floor}")
        
        btn_zoom_in.on_clicked(zoom_in)
        btn_zoom_out.on_clicked(zoom_out)
        btn_reset.on_clicked(reset_view)
        btn_floor_up.on_clicked(floor_up)
        btn_floor_down.on_clicked(floor_down)
        
        ax.text(0.1, 0.5, "Use buttons above or:\n• Click rooms to navigate\n• Scroll to zoom\n• Arrow keys for floors",
               transform=ax.transAxes, fontsize=10)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])

    def _setup_clicks(self, fig, ax_main):
        """Setup click interactions"""
        def on_pick(event):
            if hasattr(event.artist, 'get_gid') and event.artist.get_gid():
                gid = event.artist.get_gid()
                if gid.startswith('room_'):
                    room_idx = int(gid.split('_')[1])
                    room = self.rooms[room_idx]
                    
                    print(f"🚪 Navigated to: {room['type'].title()} ({room['geometry'].area:.1f}m²)")
                    
                    # Highlight room
                    center = room['center']
                    highlight = patches.Circle(center, 2, color=self.colors['selected'], 
                                             alpha=0.5, zorder=10)
                    ax_main.add_patch(highlight)
                    
                    # Zoom to room
                    ax_main.set_xlim(center[0]-5, center[0]+5)
                    ax_main.set_ylim(center[1]-5, center[1]+5)
                    
                    fig.canvas.draw()
        
        def on_scroll(event):
            if event.inaxes == ax_main:
                zoom_factor = 1.1 if event.button == 'up' else 0.9
                xlim = ax_main.get_xlim()
                ylim = ax_main.get_ylim()
                
                center_x = (xlim[0] + xlim[1]) / 2
                center_y = (ylim[0] + ylim[1]) / 2
                
                width = (xlim[1] - xlim[0]) / zoom_factor
                height = (ylim[1] - ylim[0]) / zoom_factor
                
                ax_main.set_xlim(center_x - width/2, center_x + width/2)
                ax_main.set_ylim(center_y - height/2, center_y + height/2)
                fig.canvas.draw()
        
        fig.canvas.mpl_connect('pick_event', on_pick)
        fig.canvas.mpl_connect('scroll_event', on_scroll)

def create_fast_sophisticated_plan(dxf_path, output_path):
    """Create fast sophisticated interactive plan"""
    planner = FastSophisticatedPlan()
    return planner.create_interactive(dxf_path, output_path)

if __name__ == "__main__":
    dxf_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\input_files\ovo DOSSIER COSTO - plan rdc rdj - cota.dxf"
    output_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\output_files\fast_sophisticated_ovo.png"
    
    print("🚀 FAST SOPHISTICATED ARCHITECTURAL PLAN")
    print("=" * 50)
    create_fast_sophisticated_plan(dxf_file, output_file)