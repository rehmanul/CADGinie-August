import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, Circle, Rectangle, Polygon as MplPolygon
import numpy as np
from shapely.geometry import Polygon, LineString, Point
import math

class PixelPerfectRenderer:
    def __init__(self):
        self.colors = {
            'walls': '#6B7280',
            'restricted': '#3B82F6',
            'entrances': '#EF4444',
            'corridors': '#F472B6',
            'background': '#FFFFFF',
            'grid': '#F3F4F6',
            'text': '#1F2937',
            'legend_bg': '#F9FAFB'
        }
        
        self.line_weights = {
            'walls': 3.0,
            'restricted': 1.5,
            'entrances': 2.0,
            'corridors': 2.0,
            'grid': 0.5,
            'outline': 1.0
        }
        
        self.fonts = {
            'title': {'size': 16, 'weight': 'bold'},
            'legend': {'size': 12, 'weight': 'normal'},
            'labels': {'size': 10, 'weight': 'normal'},
            'measurements': {'size': 8, 'weight': 'normal'}
        }
    
    def render_pixel_perfect_plan(self, geometry_data, layout_data, output_path, 
                                 title="Professional Floor Plan", dpi=300):
        """Render pixel-perfect floor plan with professional styling"""
        
        fig_size, plot_bounds = self._calculate_optimal_layout(geometry_data, layout_data)
        
        fig, ax = plt.subplots(1, 1, figsize=fig_size, dpi=dpi)
        
        self._setup_professional_styling(ax, plot_bounds)
        
        self._render_building_envelope(ax, geometry_data)
        self._render_walls(ax, geometry_data)
        self._render_restricted_zones(ax, geometry_data)
        self._render_entrances_with_swings(ax, geometry_data)
        self._render_doors_with_swings(ax, geometry_data)
        self._render_windows(ax, geometry_data)
        
        self._render_categorized_ilots(ax, layout_data)
        self._render_corridor_network(ax, layout_data)
        
        self._add_measurements_and_annotations(ax, geometry_data, layout_data)
        self._add_interactive_legend(ax, layout_data)
        self._add_title_and_branding(ax, title, layout_data.get('stats', {}))
        
        self._save_high_quality_output(fig, output_path, dpi)
        
        plt.close(fig)
        return output_path
    
    def _calculate_optimal_layout(self, geometry_data, layout_data):
        """Calculate optimal figure size and plot bounds"""
        
        building_envelope = geometry_data.get('building_envelope')
        if building_envelope and not building_envelope.is_empty:
            bounds = building_envelope.bounds
        else:
            usable_areas = geometry_data.get('usable_areas', {})
            usable_area = usable_areas.get('usable_area')
            if usable_area and not usable_area.is_empty:
                bounds = usable_area.bounds
            else:
                bounds = (0, 0, 20, 20)
        
        min_x, min_y, max_x, max_y = bounds
        
        margin_x = (max_x - min_x) * 0.1
        margin_y = (max_y - min_y) * 0.1
        
        plot_bounds = (min_x - margin_x, min_y - margin_y, max_x + margin_x, max_y + margin_y)
        
        width = plot_bounds[2] - plot_bounds[0]
        height = plot_bounds[3] - plot_bounds[1]
        aspect_ratio = width / height
        
        if aspect_ratio > 1.5:
            fig_width = 16
            fig_height = fig_width / aspect_ratio
        elif aspect_ratio < 0.67:
            fig_height = 12
            fig_width = fig_height * aspect_ratio
        else:
            fig_width = 12
            fig_height = 12 / aspect_ratio
        
        return (fig_width, fig_height), plot_bounds
    
    def _setup_professional_styling(self, ax, plot_bounds):
        """Setup professional architectural styling"""
        
        ax.set_xlim(plot_bounds[0], plot_bounds[2])
        ax.set_ylim(plot_bounds[1], plot_bounds[3])
        ax.set_aspect('equal')
        ax.set_facecolor(self.colors['background'])
        
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        
        self._add_professional_grid(ax, plot_bounds)
    
    def _add_professional_grid(self, ax, plot_bounds):
        """Add subtle professional grid"""
        
        min_x, min_y, max_x, max_y = plot_bounds
        grid_spacing = 1.0
        
        x = math.ceil(min_x / grid_spacing) * grid_spacing
        while x <= max_x:
            ax.axvline(x, color=self.colors['grid'], 
                      linewidth=self.line_weights['grid'], 
                      alpha=0.3, zorder=0)
            x += grid_spacing
        
        y = math.ceil(min_y / grid_spacing) * grid_spacing
        while y <= max_y:
            ax.axhline(y, color=self.colors['grid'], 
                      linewidth=self.line_weights['grid'], 
                      alpha=0.3, zorder=0)
            y += grid_spacing
    
    def _render_building_envelope(self, ax, geometry_data):
        """Render building envelope outline"""
        
        building_envelope = geometry_data.get('building_envelope')
        if not building_envelope or building_envelope.is_empty:
            return
        
        if hasattr(building_envelope, 'exterior'):
            coords = list(building_envelope.exterior.coords)
            envelope_patch = MplPolygon(coords, 
                                      facecolor='none',
                                      edgecolor=self.colors['walls'],
                                      linewidth=self.line_weights['walls'] * 0.5,
                                      alpha=0.3,
                                      zorder=1)
            ax.add_patch(envelope_patch)
    
    def _render_walls(self, ax, geometry_data):
        """Render walls as thick gray lines"""
        
        wall_data = geometry_data.get('walls', {})
        wall_polygons = wall_data.get('polygons', [])
        
        for wall_poly in wall_polygons:
            if wall_poly.is_empty:
                continue
            
            if hasattr(wall_poly, 'exterior'):
                coords = list(wall_poly.exterior.coords)
                wall_patch = MplPolygon(coords,
                                      facecolor=self.colors['walls'],
                                      edgecolor=self.colors['walls'],
                                      linewidth=self.line_weights['walls'],
                                      alpha=0.8,
                                      zorder=5)
                ax.add_patch(wall_patch)
                
                for interior in wall_poly.interiors:
                    hole_coords = list(interior.coords)
                    hole_patch = MplPolygon(hole_coords,
                                          facecolor=self.colors['background'],
                                          edgecolor=self.colors['walls'],
                                          linewidth=self.line_weights['walls'] * 0.5,
                                          zorder=6)
                    ax.add_patch(hole_patch)
    
    def _render_restricted_zones(self, ax, geometry_data):
        """Render restricted zones in blue"""
        
        restricted_data = geometry_data.get('restricted_zones', {})
        restricted_polygons = restricted_data.get('polygons', [])
        
        for restricted_poly in restricted_polygons:
            if restricted_poly.is_empty:
                continue
            
            if hasattr(restricted_poly, 'exterior'):
                coords = list(restricted_poly.exterior.coords)
                restricted_patch = MplPolygon(coords,
                                            facecolor=self.colors['restricted'],
                                            edgecolor=self.colors['restricted'],
                                            linewidth=self.line_weights['restricted'],
                                            alpha=0.3,
                                            zorder=3)
                ax.add_patch(restricted_patch)
    
    def _render_entrances_with_swings(self, ax, geometry_data):
        """Render entrances/exits in red with curved door swings"""
        
        entrance_data = geometry_data.get('entrances', {})
        entrance_points = entrance_data.get('points', [])
        
        for entrance_point in entrance_points:
            if isinstance(entrance_point, Point):
                x, y = entrance_point.x, entrance_point.y
                
                entrance_circle = Circle((x, y), 0.3,
                                       facecolor=self.colors['entrances'],
                                       edgecolor=self.colors['entrances'],
                                       linewidth=self.line_weights['entrances'],
                                       alpha=0.8,
                                       zorder=7)
                ax.add_patch(entrance_circle)
                
                clearance_circle = Circle((x, y), 1.5,
                                        facecolor='none',
                                        edgecolor=self.colors['entrances'],
                                        linewidth=self.line_weights['entrances'] * 0.5,
                                        alpha=0.3,
                                        linestyle='--',
                                        zorder=2)
                ax.add_patch(clearance_circle)
    
    def _render_doors_with_swings(self, ax, geometry_data):
        """Render doors with swing directions"""
        
        door_data = geometry_data.get('doors', {})
        doors = door_data.get('doors', [])
        
        for door in doors:
            center = door.get('center')
            radius = door.get('radius', 0.9)
            start_angle = door.get('start_angle', 0)
            end_angle = door.get('end_angle', 90)
            
            if not center:
                continue
            
            x, y = center
            
            hinge_circle = Circle((x, y), 0.1,
                                facecolor=self.colors['entrances'],
                                edgecolor=self.colors['entrances'],
                                zorder=8)
            ax.add_patch(hinge_circle)
            
            swing_arc = Arc((x, y), radius * 2, radius * 2,
                          angle=0,
                          theta1=start_angle,
                          theta2=end_angle,
                          color=self.colors['entrances'],
                          linewidth=self.line_weights['entrances'],
                          alpha=0.7,
                          zorder=7)
            ax.add_patch(swing_arc)
            
            end_angle_rad = math.radians(end_angle)
            leaf_x = x + radius * math.cos(end_angle_rad)
            leaf_y = y + radius * math.sin(end_angle_rad)
            
            ax.plot([x, leaf_x], [y, leaf_y],
                   color=self.colors['entrances'],
                   linewidth=self.line_weights['entrances'],
                   alpha=0.7,
                   zorder=7)
    
    def _render_windows(self, ax, geometry_data):
        """Render windows"""
        
        window_data = geometry_data.get('windows', {})
        windows = window_data.get('windows', [])
        
        for window in windows:
            window_line = window.get('line')
            if not window_line:
                continue
            
            coords = list(window_line.coords)
            if len(coords) >= 2:
                xs, ys = zip(*coords)
                ax.plot(xs, ys,
                       color=self.colors['walls'],
                       linewidth=self.line_weights['walls'] * 1.5,
                       alpha=0.6,
                       zorder=6)
    
    def _render_categorized_ilots(self, ax, layout_data):
        """Render îlots with category-based color coding"""
        
        categories = layout_data.get('categories', {})
        
        for category_name, category_data in categories.items():
            islands = category_data.get('islands', [])
            color = category_data.get('color', '#22C55E')
            outline_color = category_data.get('outline', '#16A34A')
            
            for island in islands:
                if island.is_empty:
                    continue
                
                if hasattr(island, 'exterior'):
                    coords = list(island.exterior.coords)
                    island_patch = MplPolygon(coords,
                                            facecolor=color,
                                            edgecolor=outline_color,
                                            linewidth=self.line_weights['outline'],
                                            alpha=0.7,
                                            zorder=10)
                    ax.add_patch(island_patch)
                    
                    centroid = island.centroid
                    area = island.area
                    ax.text(centroid.x, centroid.y, f'{area:.1f}m²',
                           ha='center', va='center',
                           fontsize=self.fonts['measurements']['size'],
                           fontweight=self.fonts['measurements']['weight'],
                           color=self.colors['text'],
                           zorder=11)
    
    def _render_corridor_network(self, ax, layout_data):
        """Render corridor network with area labels"""
        
        corridors = layout_data.get('corridors', [])
        
        for i, corridor in enumerate(corridors):
            corridor_geom = corridor.get('geometry')
            corridor_area = corridor.get('area', 0)
            
            if not corridor_geom or corridor_geom.is_empty:
                continue
            
            if hasattr(corridor_geom, 'exterior'):
                coords = list(corridor_geom.exterior.coords)
                corridor_patch = MplPolygon(coords,
                                          facecolor=self.colors['corridors'],
                                          edgecolor=self.colors['corridors'],
                                          linewidth=self.line_weights['corridors'],
                                          alpha=0.4,
                                          zorder=4)
                ax.add_patch(corridor_patch)
                
                centroid = corridor_geom.centroid
                ax.text(centroid.x, centroid.y, f'{corridor_area:.2f}m²',
                       ha='center', va='center',
                       fontsize=self.fonts['labels']['size'],
                       fontweight=self.fonts['labels']['weight'],
                       color=self.colors['text'],
                       bbox=dict(boxstyle='round,pad=0.3',
                               facecolor=self.colors['background'],
                               edgecolor=self.colors['corridors'],
                               alpha=0.8),
                       zorder=12)
    
    def _add_measurements_and_annotations(self, ax, geometry_data, layout_data):
        """Add measurements and annotations"""
        
        building_envelope = geometry_data.get('building_envelope')
        if building_envelope and not building_envelope.is_empty:
            bounds = building_envelope.bounds
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            
            self._add_dimension_line(ax, 
                                   (bounds[0], bounds[1] - 0.5),
                                   (bounds[2], bounds[1] - 0.5),
                                   f'{width:.1f}m')
            
            self._add_dimension_line(ax,
                                   (bounds[0] - 0.5, bounds[1]),
                                   (bounds[0] - 0.5, bounds[3]),
                                   f'{height:.1f}m',
                                   vertical=True)
    
    def _add_dimension_line(self, ax, start, end, label, vertical=False):
        """Add dimension line with label"""
        
        x1, y1 = start
        x2, y2 = end
        
        ax.plot([x1, x2], [y1, y2],
               color=self.colors['text'],
               linewidth=self.line_weights['grid'],
               alpha=0.7,
               zorder=15)
        
        marker_size = 0.1
        if vertical:
            ax.plot([x1 - marker_size, x1 + marker_size], [y1, y1],
                   color=self.colors['text'], linewidth=1, zorder=15)
            ax.plot([x2 - marker_size, x2 + marker_size], [y2, y2],
                   color=self.colors['text'], linewidth=1, zorder=15)
        else:
            ax.plot([x1, x1], [y1 - marker_size, y1 + marker_size],
                   color=self.colors['text'], linewidth=1, zorder=15)
            ax.plot([x2, x2], [y2 - marker_size, y2 + marker_size],
                   color=self.colors['text'], linewidth=1, zorder=15)
        
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        rotation = 90 if vertical else 0
        
        ax.text(mid_x, mid_y, label,
               ha='center', va='center',
               fontsize=self.fonts['measurements']['size'],
               fontweight=self.fonts['measurements']['weight'],
               color=self.colors['text'],
               rotation=rotation,
               bbox=dict(boxstyle='round,pad=0.2',
                       facecolor=self.colors['background'],
                       edgecolor='none',
                       alpha=0.8),
               zorder=16)
    
    def _add_interactive_legend(self, ax, layout_data):
        """Add interactive legend matching color scheme"""
        
        legend_elements = [
            ('Walls', self.colors['walls'], 'rectangle'),
            ('Restricted Zones', self.colors['restricted'], 'rectangle'),
            ('Entrances/Exits', self.colors['entrances'], 'circle'),
            ('Corridors', self.colors['corridors'], 'rectangle')
        ]
        
        categories = layout_data.get('categories', {})
        for category_name, category_data in categories.items():
            if category_data.get('islands'):
                color = category_data.get('color', '#22C55E')
                legend_elements.append((f'Îlots ({category_name.title()})', color, 'rectangle'))
        
        ax_bounds = ax.get_xlim(), ax.get_ylim()
        legend_x = ax_bounds[0][1] - (ax_bounds[0][1] - ax_bounds[0][0]) * 0.02
        legend_y = ax_bounds[1][1] - (ax_bounds[1][1] - ax_bounds[1][0]) * 0.05
        
        legend_height = len(legend_elements) * 0.8 + 1.0
        legend_width = 4.0
        
        legend_bg = Rectangle((legend_x - legend_width, legend_y - legend_height),
                            legend_width, legend_height,
                            facecolor=self.colors['legend_bg'],
                            edgecolor=self.colors['text'],
                            linewidth=0.5,
                            alpha=0.9,
                            zorder=20)
        ax.add_patch(legend_bg)
        
        ax.text(legend_x - legend_width/2, legend_y - 0.3, 'Legend',
               ha='center', va='center',
               fontsize=self.fonts['legend']['size'],
               fontweight='bold',
               color=self.colors['text'],
               zorder=21)
        
        for i, (label, color, shape) in enumerate(legend_elements):
            item_y = legend_y - 1.0 - i * 0.6
            
            if shape == 'circle':
                indicator = Circle((legend_x - legend_width + 0.3, item_y),
                                 0.15,
                                 facecolor=color,
                                 edgecolor=color,
                                 zorder=21)
            else:
                indicator = Rectangle((legend_x - legend_width + 0.15, item_y - 0.1),
                                    0.3, 0.2,
                                    facecolor=color,
                                    edgecolor=color,
                                    zorder=21)
            
            ax.add_patch(indicator)
            
            ax.text(legend_x - legend_width + 0.7, item_y, label,
                   ha='left', va='center',
                   fontsize=self.fonts['legend']['size'],
                   fontweight=self.fonts['legend']['weight'],
                   color=self.colors['text'],
                   zorder=21)
    
    def _add_title_and_branding(self, ax, title, stats):
        """Add title and professional branding"""
        
        ax_bounds = ax.get_xlim(), ax.get_ylim()
        title_x = (ax_bounds[0][0] + ax_bounds[0][1]) / 2
        title_y = ax_bounds[1][1] - (ax_bounds[1][1] - ax_bounds[1][0]) * 0.02
        
        ax.text(title_x, title_y, title,
               ha='center', va='top',
               fontsize=self.fonts['title']['size'],
               fontweight=self.fonts['title']['weight'],
               color=self.colors['text'],
               zorder=25)
        
        if stats:
            stats_text = self._format_stats_summary(stats)
            stats_x = ax_bounds[0][0] + (ax_bounds[0][1] - ax_bounds[0][0]) * 0.02
            stats_y = ax_bounds[1][0] + (ax_bounds[1][1] - ax_bounds[1][0]) * 0.05
            
            ax.text(stats_x, stats_y, stats_text,
                   ha='left', va='bottom',
                   fontsize=self.fonts['labels']['size'],
                   fontweight=self.fonts['labels']['weight'],
                   color=self.colors['text'],
                   bbox=dict(boxstyle='round,pad=0.5',
                           facecolor=self.colors['legend_bg'],
                           edgecolor=self.colors['text'],
                           alpha=0.9),
                   zorder=25)
    
    def _format_stats_summary(self, stats):
        """Format statistics summary"""
        
        total_area = stats.get('total_usable_area', 0)
        islands_placed = stats.get('islands_placed', 0)
        corridors_created = stats.get('corridors_created', 0)
        
        return (f"Total Area: {total_area:.1f}m²\n"
                f"Îlots Placed: {islands_placed}\n"
                f"Corridors: {corridors_created}")
    
    def _save_high_quality_output(self, fig, output_path, dpi):
        """Save high-quality output with proper settings"""
        
        plt.tight_layout()
        
        fig.savefig(output_path,
                   dpi=dpi,
                   bbox_inches='tight',
                   pad_inches=0.1,
                   facecolor=self.colors['background'],
                   edgecolor='none',
                   format='png',
                   quality=95)

def render_pixel_perfect_plan(geometry_data, layout_data, output_path, 
                            title="Professional Floor Plan", dpi=300):
    """Main rendering function"""
    renderer = PixelPerfectRenderer()
    return renderer.render_pixel_perfect_plan(
        geometry_data, layout_data, output_path, title, dpi
    )