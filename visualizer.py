import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import math
from shapely.geometry import Polygon, MultiPolygon
import io
import base64

class FloorPlanVisualizer:
    def __init__(self):
        # Professional color scheme
        self.colors = {
            'walls': '#6B7280',
            'restricted': '#3B82F6',
            'entrances': '#EF4444',
            'islands_small': '#10B981',
            'islands_medium': '#059669',
            'islands_large': '#047857',
            'corridors': '#F472B6',
            'background': '#F9FAFB',
            'text': '#1F2937'
        }
        
        self.line_weights = {
            'walls': 3,
            'islands': 2,
            'corridors': 1.5,
            'restricted': 2
        }
    
    def visualize_plan(self, geometry, layout, output_path, interactive=False):
        """Generate professional architectural visualization"""
        print(f"Creating professional visualization: {output_path}")
        
        # Create high-resolution figure
        fig, ax = plt.subplots(figsize=(20, 16), dpi=300)
        ax.set_aspect('equal', adjustable='box')
        ax.set_facecolor(self.colors['background'])
        
        # Remove axes for clean look
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Draw elements in proper order (back to front)
        self._draw_background_grid(ax, geometry)
        self._draw_walls(ax, geometry)
        self._draw_restricted_areas(ax, geometry)
        self._draw_entrances(ax, geometry)
        self._draw_corridors(ax, layout)
        self._draw_islands(ax, layout)
        self._add_measurements(ax, geometry, layout)
        self._add_legend(ax)
        self._add_title_and_info(ax, layout)
        
        # Set proper bounds with padding
        self._set_plot_bounds(ax, geometry)
        
        # Save with high quality
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor=self.colors['background'], edgecolor='none')
        plt.close(fig)
        
        print(f"Visualization saved: {output_path}")
        return output_path
    
    def _draw_background_grid(self, ax, geometry):
        """Draw subtle background grid for scale reference"""
        if not geometry.get('walls'):
            return
            
        bounds = geometry['walls'].bounds
        min_x, min_y, max_x, max_y = bounds
        
        # Grid every meter
        grid_spacing = 1.0
        
        # Vertical lines
        x = math.ceil(min_x)
        while x < max_x:
            ax.axvline(x, color='#E5E7EB', linewidth=0.5, alpha=0.3, zorder=0)
            x += grid_spacing
        
        # Horizontal lines
        y = math.ceil(min_y)
        while y < max_y:
            ax.axhline(y, color='#E5E7EB', linewidth=0.5, alpha=0.3, zorder=0)
            y += grid_spacing
    
    def _draw_walls(self, ax, geometry):
        """Draw walls with professional styling"""
        walls = geometry.get('walls')
        if not walls or walls.is_empty:
            return
        
        self._plot_polygon(ax, walls, 
                          facecolor='white', 
                          edgecolor=self.colors['walls'],
                          linewidth=self.line_weights['walls'],
                          zorder=1)
    
    def _draw_restricted_areas(self, ax, geometry):
        """Draw restricted areas in blue"""
        restricted = geometry.get('restricted_areas')
        if not restricted or restricted.is_empty:
            return
        
        self._plot_polygon(ax, restricted,
                          facecolor=self.colors['restricted'],
                          edgecolor=self.colors['restricted'],
                          alpha=0.7,
                          linewidth=self.line_weights['restricted'],
                          zorder=2)
    
    def _draw_entrances(self, ax, geometry):
        """Draw entrances with door swing arcs"""
        entrances = geometry.get('entrances')
        if not entrances or entrances.is_empty:
            return
        
        self._plot_polygon(ax, entrances,
                          facecolor=self.colors['entrances'],
                          edgecolor=self.colors['entrances'],
                          alpha=0.8,
                          linewidth=self.line_weights['restricted'],
                          zorder=3)
    
    def _draw_corridors(self, ax, layout):
        """Draw corridors with area labels"""
        corridors = layout.get('corridors', [])
        
        for i, corridor in enumerate(corridors):
            if corridor.is_empty:
                continue
                
            # Draw corridor
            self._plot_polygon(ax, corridor,
                              facecolor=self.colors['corridors'],
                              edgecolor=self.colors['corridors'],
                              alpha=0.6,
                              linewidth=self.line_weights['corridors'],
                              zorder=4)
            
            # Add area label
            centroid = corridor.centroid
            area = corridor.area
            ax.text(centroid.x, centroid.y, f'{area:.1f}m²',
                   ha='center', va='center',
                   fontsize=8, fontweight='bold',
                   color='white',
                   bbox=dict(boxstyle='round,pad=0.2', 
                           facecolor=self.colors['corridors'], 
                           alpha=0.8),
                   zorder=5)
    
    def _draw_islands(self, ax, layout):
        """Draw îlots with size-based color coding"""
        islands = layout.get('islands', [])
        
        for island in islands:
            if island.is_empty:
                continue
            
            area = island.area
            
            # Color based on size
            if area < 6:  # Small islands
                color = self.colors['islands_small']
            elif area < 15:  # Medium islands
                color = self.colors['islands_medium']
            else:  # Large islands
                color = self.colors['islands_large']
            
            # Draw island with rounded corners
            self._plot_polygon(ax, island,
                              facecolor=color,
                              edgecolor=color,
                              alpha=0.9,
                              linewidth=self.line_weights['islands'],
                              zorder=6)
            
            # Add size label
            centroid = island.centroid
            bounds = island.bounds
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            
            ax.text(centroid.x, centroid.y, f'{width:.1f}×{height:.1f}m',
                   ha='center', va='center',
                   fontsize=7, fontweight='bold',
                   color='white',
                   zorder=7)
    
    def _add_measurements(self, ax, geometry, layout):
        """Add key measurements and dimensions"""
        walls = geometry.get('walls')
        if not walls or walls.is_empty:
            return
        
        bounds = walls.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        
        # Overall dimensions
        ax.text(bounds[0] + width/2, bounds[3] + 1, f'{width:.1f}m',
               ha='center', va='bottom', fontsize=10, fontweight='bold',
               color=self.colors['text'])
        
        ax.text(bounds[0] - 1, bounds[1] + height/2, f'{height:.1f}m',
               ha='right', va='center', fontsize=10, fontweight='bold',
               color=self.colors['text'], rotation=90)
    
    def _add_legend(self, ax):
        """Add professional legend"""
        legend_elements = [
            patches.Patch(color=self.colors['walls'], label='Walls'),
            patches.Patch(color=self.colors['restricted'], label='No Entry Zones'),
            patches.Patch(color=self.colors['entrances'], label='Entrances/Exits'),
            patches.Patch(color=self.colors['islands_small'], label='Small Îlots (<6m²)'),
            patches.Patch(color=self.colors['islands_medium'], label='Medium Îlots (6-15m²)'),
            patches.Patch(color=self.colors['islands_large'], label='Large Îlots (>15m²)'),
            patches.Patch(color=self.colors['corridors'], label='Corridors')
        ]
        
        legend = ax.legend(handles=legend_elements, 
                          loc='upper left', 
                          bbox_to_anchor=(1.02, 1),
                          frameon=True,
                          fancybox=True,
                          shadow=True,
                          fontsize=10)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_alpha(0.9)
    
    def _add_title_and_info(self, ax, layout):
        """Add title and layout information"""
        stats = layout.get('stats', {})
        
        title = "Professional Floor Plan Layout"
        ax.text(0.5, 1.05, title, transform=ax.transAxes,
               ha='center', va='bottom', fontsize=16, fontweight='bold',
               color=self.colors['text'])
        
        # Statistics
        info_text = []
        if 'total_area' in stats:
            info_text.append(f"Total Area: {stats['total_area']:.1f}m²")
        if 'islands_placed' in stats:
            info_text.append(f"Îlots Placed: {stats['islands_placed']}")
        if 'island_coverage' in stats:
            info_text.append(f"Coverage: {stats['island_coverage']*100:.1f}%")
        if 'corridors_created' in stats:
            info_text.append(f"Corridors: {stats['corridors_created']}")
        
        if info_text:
            ax.text(0.5, -0.05, " | ".join(info_text), transform=ax.transAxes,
                   ha='center', va='top', fontsize=10,
                   color=self.colors['text'])
    
    def _plot_polygon(self, ax, geom, **kwargs):
        """Plot Shapely polygon with proper handling of MultiPolygon"""
        if geom.is_empty:
            return
        
        if isinstance(geom, MultiPolygon):
            for poly in geom.geoms:
                self._plot_single_polygon(ax, poly, **kwargs)
        else:
            self._plot_single_polygon(ax, geom, **kwargs)
    
    def _plot_single_polygon(self, ax, poly, **kwargs):
        """Plot a single polygon"""
        if poly.is_empty:
            return
        
        # Extract exterior coordinates
        x, y = poly.exterior.xy
        
        # Create polygon patch
        polygon_patch = patches.Polygon(list(zip(x, y)), **kwargs)
        ax.add_patch(polygon_patch)
        
        # Handle holes (interiors)
        for interior in poly.interiors:
            x_int, y_int = interior.xy
            hole_patch = patches.Polygon(list(zip(x_int, y_int)), 
                                       facecolor=kwargs.get('facecolor', 'white'),
                                       edgecolor=kwargs.get('edgecolor', 'black'),
                                       zorder=kwargs.get('zorder', 1) + 0.1)
            ax.add_patch(hole_patch)
    
    def _set_plot_bounds(self, ax, geometry):
        """Set appropriate plot bounds with padding"""
        walls = geometry.get('walls')
        if not walls or walls.is_empty:
            return
        
        bounds = walls.bounds
        min_x, min_y, max_x, max_y = bounds
        
        # Add 10% padding
        width = max_x - min_x
        height = max_y - min_y
        padding_x = width * 0.1
        padding_y = height * 0.1
        
        ax.set_xlim(min_x - padding_x, max_x + padding_x)
        ax.set_ylim(min_y - padding_y, max_y + padding_y)

def visualize_plan(geometry, layout, output_path):
    """Main visualization function for backward compatibility"""
    visualizer = FloorPlanVisualizer()
    return visualizer.visualize_plan(geometry, layout, output_path)