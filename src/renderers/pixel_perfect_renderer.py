#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch, Arc, Wedge
import numpy as np
from shapely.geometry import Polygon, Point, LineString
import math
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class PixelPerfectRenderer:
    """Pixel-perfect floor plan renderer with professional architectural standards"""
    
    def __init__(self):
        # Professional architectural color scheme
        self.colors = {
            'walls': '#6B7280',
            'restricted_areas': '#3B82F6',
            'entrances': '#EF4444',
            'corridors': '#F472B6',
            'background': '#FFFFFF',
            'grid_major': '#E5E7EB',
            'grid_minor': '#F3F4F6',
            'text_primary': '#1F2937',
            'text_secondary': '#6B7280',
            'legend_bg': '#F9FAFB',
            'measurements': '#374151'
        }
        
        # Professional line weights (in points)
        self.line_weights = {
            'walls_exterior': 4.0,
            'walls_interior': 2.5,
            'restricted_areas': 2.0,
            'entrances': 2.0,
            'corridors': 2.0,
            'islands_outline': 1.5,
            'grid_major': 0.8,
            'grid_minor': 0.4,
            'measurements': 1.0,
            'annotations': 0.8
        }
        
        # Typography settings
        self.fonts = {
            'title': {'size': 18, 'weight': 'bold', 'family': 'sans-serif'},
            'legend': {'size': 12, 'weight': 'normal', 'family': 'sans-serif'},
            'labels': {'size': 10, 'weight': 'normal', 'family': 'sans-serif'},
            'measurements': {'size': 8, 'weight': 'normal', 'family': 'monospace'},
            'annotations': {'size': 9, 'weight': 'normal', 'family': 'sans-serif'}
        }
        
        # Îlot category colors
        self.ilot_colors = {
            'small': {'fill': '#10B981', 'outline': '#059669'},
            'medium': {'fill': '#059669', 'outline': '#047857'},
            'large': {'fill': '#047857', 'outline': '#065F46'},
            'extra_large': {'fill': '#065F46', 'outline': '#064E3B'}
        }
    
    def render_production_floorplan(self, geometry: Dict[str, Any], layout: Dict[str, Any], 
                                  output_path: str, title: str = "Professional Floor Plan",
                                  dpi: int = 300) -> str:
        """Render production-quality floor plan with pixel-perfect precision"""
        
        try:
            logger.info(f"Rendering production floor plan: {output_path}")
            
            # Calculate optimal figure size and layout
            fig_size, plot_bounds = self._calculate_optimal_layout(geometry, layout)
            
            # Create high-resolution figure
            fig, ax = plt.subplots(figsize=fig_size, dpi=dpi)
            
            # Setup professional styling
            self._setup_professional_styling(ax, plot_bounds)
            
            # Render architectural elements in proper order (back to front)
            self._render_architectural_grid(ax, plot_bounds)
            self._render_walls(ax, geometry)
            self._render_restricted_areas(ax, geometry)
            self._render_entrances_with_swings(ax, geometry)
            self._render_doors_and_windows(ax, geometry)
            self._render_intelligent_islands(ax, layout)
            self._render_corridor_network(ax, layout)
            
            # Add professional annotations
            self._add_measurements_and_dimensions(ax, geometry, layout)
            self._add_interactive_legend(ax, layout)
            self._add_title_and_metadata(ax, title, layout)
            self._add_scale_and_north_arrow(ax, plot_bounds)
            
            # Save with professional quality settings
            self._save_production_quality(fig, output_path, dpi)
            
            plt.close(fig)
            
            logger.info(f"Production floor plan rendered successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Rendering error: {str(e)}")
            raise e
    
    def _calculate_optimal_layout(self, geometry: Dict[str, Any], layout: Dict[str, Any]) -> Tuple[Tuple[float, float], Tuple[float, float, float, float]]:
        """Calculate optimal figure size and plot bounds"""
        
        # Determine plot bounds from geometry
        bounds = None
        
        if 'walls' in geometry and geometry['walls'] is not None:
            bounds = geometry['walls'].bounds
        elif 'usable_area' in geometry and geometry['usable_area'] is not None:
            bounds = geometry['usable_area'].bounds
        elif 'islands' in layout and layout['islands']:
            # Calculate bounds from islands
            all_coords = []
            for island in layout['islands']:
                island_bounds = island['geometry'].bounds
                all_coords.extend([(island_bounds[0], island_bounds[1]), (island_bounds[2], island_bounds[3])])
            
            if all_coords:
                xs, ys = zip(*all_coords)
                bounds = (min(xs), min(ys), max(xs), max(ys))
        
        if not bounds:
            bounds = (0, 0, 20, 20)  # Default bounds
        
        # Add margins
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        margin_x = width * 0.1
        margin_y = height * 0.1
        
        plot_bounds = (bounds[0] - margin_x, bounds[1] - margin_y, 
                      bounds[2] + margin_x, bounds[3] + margin_y)
        
        # Calculate figure size maintaining aspect ratio
        plot_width = plot_bounds[2] - plot_bounds[0]
        plot_height = plot_bounds[3] - plot_bounds[1]
        aspect_ratio = plot_width / plot_height
        
        # Target figure size
        if aspect_ratio > 1.5:
            fig_width = 16
            fig_height = fig_width / aspect_ratio
        elif aspect_ratio < 0.67:
            fig_height = 12
            fig_width = fig_height * aspect_ratio
        else:
            fig_width = 14
            fig_height = fig_width / aspect_ratio
        
        # Ensure minimum size
        fig_width = max(10, fig_width)
        fig_height = max(8, fig_height)
        
        return (fig_width, fig_height), plot_bounds
    
    def _setup_professional_styling(self, ax, plot_bounds: Tuple[float, float, float, float]):
        """Setup professional architectural styling"""
        
        # Set plot bounds
        ax.set_xlim(plot_bounds[0], plot_bounds[2])
        ax.set_ylim(plot_bounds[1], plot_bounds[3])
        
        # Equal aspect ratio for accurate measurements
        ax.set_aspect('equal', adjustable='box')
        
        # Professional background
        ax.set_facecolor(self.colors['background'])
        
        # Remove axes for clean architectural look
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)
    
    def _render_architectural_grid(self, ax, plot_bounds: Tuple[float, float, float, float]):
        """Render professional architectural grid system"""
        
        min_x, min_y, max_x, max_y = plot_bounds
        
        # Major grid (5m spacing)
        major_spacing = 5.0
        x_major = np.arange(
            math.floor(min_x / major_spacing) * major_spacing,
            math.ceil(max_x / major_spacing) * major_spacing + major_spacing,
            major_spacing
        )
        y_major = np.arange(
            math.floor(min_y / major_spacing) * major_spacing,
            math.ceil(max_y / major_spacing) * major_spacing + major_spacing,
            major_spacing
        )
        
        # Draw major grid
        for x in x_major:
            ax.axvline(x, color=self.colors['grid_major'], 
                      linewidth=self.line_weights['grid_major'], 
                      alpha=0.6, zorder=0)
        
        for y in y_major:
            ax.axhline(y, color=self.colors['grid_major'], 
                      linewidth=self.line_weights['grid_major'], 
                      alpha=0.6, zorder=0)
        
        # Minor grid (1m spacing)
        minor_spacing = 1.0
        x_minor = np.arange(min_x, max_x, minor_spacing)
        y_minor = np.arange(min_y, max_y, minor_spacing)
        
        # Draw minor grid
        for x in x_minor:
            if x not in x_major:
                ax.axvline(x, color=self.colors['grid_minor'], 
                          linewidth=self.line_weights['grid_minor'], 
                          alpha=0.4, zorder=0)
        
        for y in y_minor:
            if y not in y_major:
                ax.axhline(y, color=self.colors['grid_minor'], 
                          linewidth=self.line_weights['grid_minor'], 
                          alpha=0.4, zorder=0)
    
    def _render_walls(self, ax, geometry: Dict[str, Any]):
        """Render walls with professional architectural styling"""
        
        if 'walls' not in geometry or geometry['walls'] is None:
            return
        
        walls = geometry['walls']
        
        if walls.is_empty:
            return
        
        # Render walls as thick gray lines
        self._plot_geometry(ax, walls, 
                           facecolor='none',
                           edgecolor=self.colors['walls'],
                           linewidth=self.line_weights['walls_exterior'],
                           alpha=0.9,
                           zorder=5)
    
    def _render_restricted_areas(self, ax, geometry: Dict[str, Any]):
        """Render restricted areas in blue with professional styling"""
        
        if 'restricted_areas' not in geometry or geometry['restricted_areas'] is None:
            return
        
        restricted = geometry['restricted_areas']
        
        if restricted.is_empty:
            return
        
        # Render restricted areas with blue fill and outline
        self._plot_geometry(ax, restricted,
                           facecolor=self.colors['restricted_areas'],
                           edgecolor=self.colors['restricted_areas'],
                           linewidth=self.line_weights['restricted_areas'],
                           alpha=0.3,
                           zorder=3)
    
    def _render_entrances_with_swings(self, ax, geometry: Dict[str, Any]):
        """Render entrances/exits in red with curved door swings"""
        
        if 'entrances' not in geometry or geometry['entrances'] is None:
            return
        
        entrances = geometry['entrances']
        
        if entrances.is_empty:
            return
        
        # Render entrance areas
        self._plot_geometry(ax, entrances,
                           facecolor=self.colors['entrances'],
                           edgecolor=self.colors['entrances'],
                           linewidth=self.line_weights['entrances'],
                           alpha=0.7,
                           zorder=7)
    
    def _render_doors_and_windows(self, ax, geometry: Dict[str, Any]):
        """Render doors with swing arcs and windows"""
        
        # Render doors with swing directions
        if 'doors' in geometry:
            for door in geometry['doors']:
                self._render_door_swing(ax, door)
        
        # Render windows
        if 'windows' in geometry:
            for window in geometry['windows']:
                self._render_window(ax, window)
    
    def _render_door_swing(self, ax, door: Dict[str, Any]):
        """Render individual door with swing arc"""
        
        try:
            center = door['center']
            radius = door['radius']
            start_angle = door['start_angle']
            end_angle = door['end_angle']
            
            # Door hinge point
            hinge = Circle(center, 0.1, 
                          facecolor=self.colors['entrances'],
                          edgecolor=self.colors['entrances'],
                          linewidth=2,
                          zorder=9)
            ax.add_patch(hinge)
            
            # Door swing arc
            swing_arc = Arc(center, radius * 2, radius * 2,
                           angle=0, theta1=start_angle, theta2=end_angle,
                           color=self.colors['entrances'],
                           linewidth=self.line_weights['entrances'],
                           alpha=0.8,
                           zorder=8)
            ax.add_patch(swing_arc)
            
            # Door leaf line
            end_angle_rad = math.radians(end_angle)
            leaf_end_x = center[0] + radius * math.cos(end_angle_rad)
            leaf_end_y = center[1] + radius * math.sin(end_angle_rad)
            
            ax.plot([center[0], leaf_end_x], [center[1], leaf_end_y],
                   color=self.colors['entrances'],
                   linewidth=self.line_weights['entrances'],
                   alpha=0.8,
                   zorder=8)
            
        except Exception as e:
            logger.warning(f"Door rendering error: {str(e)}")
    
    def _render_window(self, ax, window: Dict[str, Any]):
        """Render individual window"""
        
        try:
            if 'geometry' in window:
                geom = window['geometry']
                x, y = geom.xy
                
                # Window line (thicker than walls)
                ax.plot(x, y, color=self.colors['walls'],
                       linewidth=self.line_weights['walls_exterior'] * 1.5,
                       alpha=0.7,
                       zorder=6)
                
                # Window sill indicators (parallel lines)
                if len(x) >= 2:
                    # Calculate perpendicular offset
                    dx = x[1] - x[0]
                    dy = y[1] - y[0]
                    length = math.sqrt(dx*dx + dy*dy)
                    
                    if length > 0:
                        offset_x = -dy / length * 0.1
                        offset_y = dx / length * 0.1
                        
                        # Parallel lines
                        x_offset1 = [xi + offset_x for xi in x]
                        y_offset1 = [yi + offset_y for yi in y]
                        x_offset2 = [xi - offset_x for xi in x]
                        y_offset2 = [yi - offset_y for yi in y]
                        
                        ax.plot(x_offset1, y_offset1, color=self.colors['walls'],
                               linewidth=self.line_weights['walls_interior'],
                               alpha=0.5, zorder=6)
                        ax.plot(x_offset2, y_offset2, color=self.colors['walls'],
                               linewidth=self.line_weights['walls_interior'],
                               alpha=0.5, zorder=6)
            
        except Exception as e:
            logger.warning(f"Window rendering error: {str(e)}")
    
    def _render_intelligent_islands(self, ax, layout: Dict[str, Any]):
        """Render îlots with intelligent color coding and professional styling"""
        
        if 'islands' not in layout or not layout['islands']:
            return
        
        for island in layout['islands']:
            try:
                geometry = island['geometry']
                category = island.get('category', 'medium')
                
                # Get colors for category
                colors = self.ilot_colors.get(category, self.ilot_colors['medium'])
                
                # Render island with professional styling
                self._plot_geometry(ax, geometry,
                                   facecolor=colors['fill'],
                                   edgecolor=colors['outline'],
                                   linewidth=self.line_weights['islands_outline'],
                                   alpha=0.8,
                                   zorder=10)
                
                # Add island label with dimensions and area
                centroid = geometry.centroid
                width = island.get('width', 0)
                height = island.get('height', 0)
                area = island.get('area', geometry.area)
                
                label_text = f"{width:.1f}×{height:.1f}m\n{area:.1f}m²"
                
                ax.text(centroid.x, centroid.y, label_text,
                       ha='center', va='center',
                       fontsize=self.fonts['labels']['size'],
                       fontweight=self.fonts['labels']['weight'],
                       color='white',
                       zorder=11,
                       bbox=dict(boxstyle='round,pad=0.2', 
                               facecolor=colors['outline'], 
                               alpha=0.8, 
                               edgecolor='none'))
                
            except Exception as e:
                logger.warning(f"Island rendering error: {str(e)}")
    
    def _render_corridor_network(self, ax, layout: Dict[str, Any]):
        """Render corridor network with area labels and professional styling"""
        
        if 'corridors' not in layout or not layout['corridors']:
            return
        
        for i, corridor in enumerate(layout['corridors']):
            try:
                if 'geometry' in corridor:
                    geometry = corridor['geometry']
                    width = corridor.get('width', 1.2)
                    area = corridor.get('area', geometry.area)
                    
                    # Render corridor
                    self._plot_geometry(ax, geometry,
                                       facecolor=self.colors['corridors'],
                                       edgecolor=self.colors['corridors'],
                                       linewidth=self.line_weights['corridors'],
                                       alpha=0.6,
                                       zorder=4)
                    
                    # Add corridor label
                    centroid = geometry.centroid
                    label_text = f"Corridor {i+1}\n{area:.2f}m²\nWidth: {width:.1f}m"
                    
                    ax.text(centroid.x, centroid.y, label_text,
                           ha='center', va='center',
                           fontsize=self.fonts['measurements']['size'],
                           fontweight=self.fonts['measurements']['weight'],
                           color=self.colors['text_primary'],
                           zorder=12,
                           bbox=dict(boxstyle='round,pad=0.3',
                                   facecolor=self.colors['background'],
                                   edgecolor=self.colors['corridors'],
                                   alpha=0.9))
                
            except Exception as e:
                logger.warning(f"Corridor rendering error: {str(e)}")
    
    def _add_measurements_and_dimensions(self, ax, geometry: Dict[str, Any], layout: Dict[str, Any]):
        """Add professional measurements and dimensions"""
        
        # Overall building dimensions
        if 'walls' in geometry and geometry['walls'] is not None:
            bounds = geometry['walls'].bounds
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            
            # Horizontal dimension line
            self._add_dimension_line(ax, 
                                   (bounds[0], bounds[1] - 1.0),
                                   (bounds[2], bounds[1] - 1.0),
                                   f"{width:.1f}m",
                                   horizontal=True)
            
            # Vertical dimension line
            self._add_dimension_line(ax,
                                   (bounds[0] - 1.0, bounds[1]),
                                   (bounds[0] - 1.0, bounds[3]),
                                   f"{height:.1f}m",
                                   horizontal=False)
    
    def _add_dimension_line(self, ax, start: Tuple[float, float], end: Tuple[float, float], 
                          label: str, horizontal: bool = True):
        """Add professional dimension line with arrows and label"""
        
        x1, y1 = start
        x2, y2 = end
        
        # Dimension line
        ax.plot([x1, x2], [y1, y2],
               color=self.colors['measurements'],
               linewidth=self.line_weights['measurements'],
               alpha=0.8,
               zorder=15)
        
        # Dimension arrows
        arrow_size = 0.2
        
        if horizontal:
            # Horizontal arrows
            ax.annotate('', xy=(x1, y1), xytext=(x1 + arrow_size, y1),
                       arrowprops=dict(arrowstyle='<-', 
                                     color=self.colors['measurements'],
                                     lw=self.line_weights['measurements']),
                       zorder=15)
            ax.annotate('', xy=(x2, y2), xytext=(x2 - arrow_size, y2),
                       arrowprops=dict(arrowstyle='<-', 
                                     color=self.colors['measurements'],
                                     lw=self.line_weights['measurements']),
                       zorder=15)
            
            # Extension lines
            ax.plot([x1, x1], [y1 - 0.3, y1 + 0.3],
                   color=self.colors['measurements'],
                   linewidth=self.line_weights['measurements'],
                   alpha=0.8, zorder=15)
            ax.plot([x2, x2], [y2 - 0.3, y2 + 0.3],
                   color=self.colors['measurements'],
                   linewidth=self.line_weights['measurements'],
                   alpha=0.8, zorder=15)
        else:
            # Vertical arrows
            ax.annotate('', xy=(x1, y1), xytext=(x1, y1 + arrow_size),
                       arrowprops=dict(arrowstyle='<-', 
                                     color=self.colors['measurements'],
                                     lw=self.line_weights['measurements']),
                       zorder=15)
            ax.annotate('', xy=(x2, y2), xytext=(x2, y2 - arrow_size),
                       arrowprops=dict(arrowstyle='<-', 
                                     color=self.colors['measurements'],
                                     lw=self.line_weights['measurements']),
                       zorder=15)
            
            # Extension lines
            ax.plot([x1 - 0.3, x1 + 0.3], [y1, y1],
                   color=self.colors['measurements'],
                   linewidth=self.line_weights['measurements'],
                   alpha=0.8, zorder=15)
            ax.plot([x2 - 0.3, x2 + 0.3], [y2, y2],
                   color=self.colors['measurements'],
                   linewidth=self.line_weights['measurements'],
                   alpha=0.8, zorder=15)
        
        # Dimension label
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        rotation = 90 if not horizontal else 0
        
        ax.text(mid_x, mid_y, label,
               ha='center', va='center',
               fontsize=self.fonts['measurements']['size'],
               fontweight=self.fonts['measurements']['weight'],
               fontfamily=self.fonts['measurements']['family'],
               color=self.colors['measurements'],
               rotation=rotation,
               bbox=dict(boxstyle='round,pad=0.2',
                       facecolor=self.colors['background'],
                       edgecolor='none',
                       alpha=0.9),
               zorder=16)
    
    def _add_interactive_legend(self, ax, layout: Dict[str, Any]):
        """Add professional interactive legend"""
        
        # Legend elements
        legend_elements = [
            {'label': 'Walls', 'color': self.colors['walls'], 'type': 'line'},
            {'label': 'Restricted Zones', 'color': self.colors['restricted_areas'], 'type': 'fill'},
            {'label': 'Entrances/Exits', 'color': self.colors['entrances'], 'type': 'fill'},
            {'label': 'Corridors', 'color': self.colors['corridors'], 'type': 'fill'}
        ]
        
        # Add îlot categories
        if 'islands' in layout and layout['islands']:
            categories_used = set()
            for island in layout['islands']:
                category = island.get('category', 'medium')
                if category not in categories_used:
                    categories_used.add(category)
                    colors = self.ilot_colors.get(category, self.ilot_colors['medium'])
                    legend_elements.append({
                        'label': f'Îlots ({category.replace("_", " ").title()})',
                        'color': colors['fill'],
                        'type': 'fill'
                    })
        
        # Position legend
        ax_bounds = ax.get_xlim(), ax.get_ylim()
        legend_x = ax_bounds[0][1] - (ax_bounds[0][1] - ax_bounds[0][0]) * 0.02
        legend_y = ax_bounds[1][1] - (ax_bounds[1][1] - ax_bounds[1][0]) * 0.05
        
        # Legend background
        legend_height = len(legend_elements) * 0.8 + 1.5
        legend_width = 4.5
        
        legend_bg = FancyBboxPatch(
            (legend_x - legend_width, legend_y - legend_height),
            legend_width, legend_height,
            boxstyle="round,pad=0.1",
            facecolor=self.colors['legend_bg'],
            edgecolor=self.colors['text_secondary'],
            linewidth=1,
            alpha=0.95,
            zorder=20
        )
        ax.add_patch(legend_bg)
        
        # Legend title
        ax.text(legend_x - legend_width/2, legend_y - 0.4, 'Legend',
               ha='center', va='center',
               fontsize=self.fonts['legend']['size'],
               fontweight='bold',
               color=self.colors['text_primary'],
               zorder=21)
        
        # Legend items
        for i, element in enumerate(legend_elements):
            item_y = legend_y - 1.2 - i * 0.6
            
            # Color indicator
            if element['type'] == 'line':
                ax.plot([legend_x - legend_width + 0.2, legend_x - legend_width + 0.6],
                       [item_y, item_y],
                       color=element['color'],
                       linewidth=3,
                       zorder=21)
            else:
                indicator = Rectangle(
                    (legend_x - legend_width + 0.2, item_y - 0.1),
                    0.4, 0.2,
                    facecolor=element['color'],
                    edgecolor=element['color'],
                    alpha=0.8,
                    zorder=21
                )
                ax.add_patch(indicator)
            
            # Label
            ax.text(legend_x - legend_width + 0.8, item_y, element['label'],
                   ha='left', va='center',
                   fontsize=self.fonts['legend']['size'],
                   fontweight=self.fonts['legend']['weight'],
                   color=self.colors['text_primary'],
                   zorder=21)
    
    def _add_title_and_metadata(self, ax, title: str, layout: Dict[str, Any]):
        """Add professional title and metadata"""
        
        # Main title
        ax_bounds = ax.get_xlim(), ax.get_ylim()
        title_x = (ax_bounds[0][0] + ax_bounds[0][1]) / 2
        title_y = ax_bounds[1][1] - (ax_bounds[1][1] - ax_bounds[1][0]) * 0.02
        
        ax.text(title_x, title_y, title,
               ha='center', va='top',
               fontsize=self.fonts['title']['size'],
               fontweight=self.fonts['title']['weight'],
               fontfamily=self.fonts['title']['family'],
               color=self.colors['text_primary'],
               zorder=25)
        
        # Metadata
        metadata_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if 'islands' in layout:
            metadata_text += f" | Îlots: {len(layout['islands'])}"
        if 'corridors' in layout:
            metadata_text += f" | Corridors: {len(layout['corridors'])}"
        
        metadata_x = ax_bounds[0][0] + (ax_bounds[0][1] - ax_bounds[0][0]) * 0.02
        metadata_y = ax_bounds[1][0] + (ax_bounds[1][1] - ax_bounds[1][0]) * 0.02
        
        ax.text(metadata_x, metadata_y, metadata_text,
               ha='left', va='bottom',
               fontsize=self.fonts['annotations']['size'],
               fontweight=self.fonts['annotations']['weight'],
               color=self.colors['text_secondary'],
               zorder=25)
    
    def _add_scale_and_north_arrow(self, ax, plot_bounds: Tuple[float, float, float, float]):
        """Add professional scale bar and north arrow"""
        
        # Scale bar
        scale_length = 5.0  # 5 meters
        scale_x = plot_bounds[0] + (plot_bounds[2] - plot_bounds[0]) * 0.05
        scale_y = plot_bounds[1] + (plot_bounds[3] - plot_bounds[1]) * 0.05
        
        # Scale bar line
        ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y],
               color=self.colors['text_primary'],
               linewidth=3,
               zorder=25)
        
        # Scale bar ticks
        tick_height = 0.3
        ax.plot([scale_x, scale_x], [scale_y - tick_height/2, scale_y + tick_height/2],
               color=self.colors['text_primary'], linewidth=2, zorder=25)
        ax.plot([scale_x + scale_length, scale_x + scale_length], 
               [scale_y - tick_height/2, scale_y + tick_height/2],
               color=self.colors['text_primary'], linewidth=2, zorder=25)
        
        # Scale label
        ax.text(scale_x + scale_length/2, scale_y - 0.8, f'{scale_length:.0f}m',
               ha='center', va='top',
               fontsize=self.fonts['measurements']['size'],
               fontweight=self.fonts['measurements']['weight'],
               color=self.colors['text_primary'],
               zorder=25)
        
        # North arrow
        north_x = plot_bounds[2] - (plot_bounds[2] - plot_bounds[0]) * 0.05
        north_y = plot_bounds[3] - (plot_bounds[3] - plot_bounds[1]) * 0.05
        
        # Arrow
        ax.annotate('', xy=(north_x, north_y), xytext=(north_x, north_y - 2),
                   arrowprops=dict(arrowstyle='->', 
                                 color=self.colors['text_primary'],
                                 lw=2),
                   zorder=25)
        
        # North label
        ax.text(north_x + 0.5, north_y - 1, 'N',
               ha='left', va='center',
               fontsize=14, fontweight='bold',
               color=self.colors['text_primary'],
               zorder=25)
    
    def _plot_geometry(self, ax, geometry, **kwargs):
        """Plot Shapely geometry with proper handling of different types"""
        
        if geometry is None or geometry.is_empty:
            return
        
        try:
            if hasattr(geometry, 'geoms'):  # MultiPolygon or MultiLineString
                for geom in geometry.geoms:
                    self._plot_single_geometry(ax, geom, **kwargs)
            else:
                self._plot_single_geometry(ax, geometry, **kwargs)
                
        except Exception as e:
            logger.warning(f"Geometry plotting error: {str(e)}")
    
    def _plot_single_geometry(self, ax, geometry, **kwargs):
        """Plot single Shapely geometry"""
        
        try:
            if hasattr(geometry, 'exterior'):  # Polygon
                x, y = geometry.exterior.xy
                polygon_patch = patches.Polygon(list(zip(x, y)), **kwargs)
                ax.add_patch(polygon_patch)
                
                # Handle holes
                for interior in geometry.interiors:
                    x_int, y_int = interior.xy
                    hole_patch = patches.Polygon(list(zip(x_int, y_int)),
                                               facecolor=kwargs.get('facecolor', 'white'),
                                               edgecolor=kwargs.get('edgecolor', 'black'),
                                               zorder=kwargs.get('zorder', 1) + 0.1)
                    ax.add_patch(hole_patch)
                    
            elif hasattr(geometry, 'xy'):  # LineString
                x, y = geometry.xy
                ax.plot(x, y, 
                       color=kwargs.get('edgecolor', 'black'),
                       linewidth=kwargs.get('linewidth', 1),
                       alpha=kwargs.get('alpha', 1),
                       zorder=kwargs.get('zorder', 1))
                       
            elif hasattr(geometry, 'x'):  # Point
                ax.plot(geometry.x, geometry.y, 'o',
                       color=kwargs.get('edgecolor', 'black'),
                       markersize=kwargs.get('linewidth', 1) * 2,
                       alpha=kwargs.get('alpha', 1),
                       zorder=kwargs.get('zorder', 1))
                       
        except Exception as e:
            logger.warning(f"Single geometry plotting error: {str(e)}")
    
    def _save_production_quality(self, fig, output_path: str, dpi: int):
        """Save figure with production quality settings"""
        
        # Tight layout
        plt.tight_layout()
        
        # Save with high quality
        fig.savefig(output_path,
                   dpi=dpi,
                   bbox_inches='tight',
                   pad_inches=0.1,
                   facecolor=self.colors['background'],
                   edgecolor='none',
                   format='png',
                   quality=95,
                   optimize=True)