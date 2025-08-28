import numpy as np
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
import networkx as nx
import random
import math

class IntelligentIlotOptimizer:
    def __init__(self):
        self.corridor_width = 1.2
        self.min_island_spacing = 0.8
        self.wall_clearance = 0.3
        self.entrance_clearance = 2.0
        
        self.coverage_profiles = {
            'low': 0.10, 'medium': 0.25, 'high': 0.30, 'maximum': 0.35
        }
        
        self.ilot_categories = {
            'small': {'max_area': 6, 'color': '#22C55E', 'outline': '#16A34A'},
            'medium': {'max_area': 12, 'color': '#3B82F6', 'outline': '#2563EB'},
            'large': {'max_area': 20, 'color': '#F59E0B', 'outline': '#D97706'},
            'xlarge': {'max_area': float('inf'), 'color': '#EF4444', 'outline': '#DC2626'}
        }
    
    def optimize_intelligent_layout(self, usable_area, island_dimensions, corridor_width=1.2, 
                                  coverage_profile='medium', wall_geometry=None, entrance_geometry=None):
        """Intelligent îlot placement with accessibility optimization"""
        
        if not usable_area or usable_area.is_empty:
            return {"islands": [], "corridors": [], "stats": {}, "categories": {}}
        
        self.corridor_width = corridor_width
        coverage = self.coverage_profiles.get(coverage_profile, 0.25)
        
        islands_to_place = self._generate_intelligent_island_sizes(
            island_dimensions, usable_area.area * coverage
        )
        
        placed_islands = self._intelligent_placement_algorithm(
            usable_area, islands_to_place, wall_geometry, entrance_geometry
        )
        
        corridors = self._generate_mandatory_corridor_network(
            usable_area, placed_islands, corridor_width
        )
        
        categorized_islands = self._categorize_islands_by_size(placed_islands)
        
        stats = self._calculate_optimization_stats(
            usable_area, placed_islands, corridors, coverage
        )
        
        return {
            "islands": placed_islands,
            "corridors": corridors,
            "categories": categorized_islands,
            "stats": stats
        }
    
    def _generate_intelligent_island_sizes(self, base_dimensions, target_area):
        """Generate island sizes with intelligent distribution"""
        
        if not base_dimensions:
            base_dimensions = [(2, 2), (3, 2), (4, 2), (3, 3), (4, 3), (5, 3), (4, 4), (5, 4), (6, 4)]
        
        islands = []
        current_area = 0
        
        sorted_dims = sorted(base_dimensions, 
                           key=lambda d: (d[0] * d[1]) / (2 * (d[0] + d[1])), 
                           reverse=True)
        
        size_distribution = {'small': 0.4, 'medium': 0.35, 'large': 0.20, 'xlarge': 0.05}
        
        for size_category, ratio in size_distribution.items():
            category_target = target_area * ratio
            category_area = 0
            
            suitable_dims = self._filter_dims_by_category(sorted_dims, size_category)
            
            while category_area < category_target and current_area < target_area:
                for width, height in suitable_dims:
                    island_area = width * height
                    
                    if (category_area + island_area <= category_target * 1.2 and 
                        current_area + island_area <= target_area * 1.1):
                        
                        islands.append((width, height))
                        category_area += island_area
                        current_area += island_area
                        
                        if category_area >= category_target:
                            break
                
                if not suitable_dims or category_area >= category_target:
                    break
        
        return islands
    
    def _filter_dims_by_category(self, dimensions, category):
        """Filter dimensions by size category"""
        if category == 'small':
            return [(w, h) for w, h in dimensions if w * h <= 6]
        elif category == 'medium':
            return [(w, h) for w, h in dimensions if 6 < w * h <= 12]
        elif category == 'large':
            return [(w, h) for w, h in dimensions if 12 < w * h <= 20]
        else:
            return [(w, h) for w, h in dimensions if w * h > 20]
    
    def _intelligent_placement_algorithm(self, usable_area, islands_to_place, 
                                       wall_geometry, entrance_geometry):
        """Advanced placement algorithm with architectural awareness"""
        
        placed_islands = []
        occupied_space = Polygon()
        
        min_x, min_y, max_x, max_y = usable_area.bounds
        
        placement_grid = self._create_intelligent_grid(
            usable_area, wall_geometry, entrance_geometry
        )
        
        islands_to_place.sort(key=lambda d: d[0] * d[1], reverse=True)
        
        for width, height in islands_to_place:
            best_position = None
            best_score = -1
            
            for w, h in [(width, height), (height, width)]:
                
                for grid_point in placement_grid:
                    x, y = grid_point
                    
                    if x + w > max_x or y + h > max_y:
                        continue
                    
                    candidate = box(x, y, x + w, y + h)
                    
                    if (candidate.within(usable_area) and 
                        not self._intersects_with_buffer(candidate, occupied_space, self.min_island_spacing)):
                        
                        score = self._calculate_intelligent_placement_score(
                            candidate, usable_area, placed_islands, wall_geometry, entrance_geometry
                        )
                        
                        if score > best_score:
                            best_score = score
                            best_position = candidate
            
            if best_position:
                placed_islands.append(best_position)
                occupied_space = unary_union([
                    occupied_space, 
                    best_position.buffer(self.min_island_spacing)
                ])
        
        return placed_islands
    
    def _create_intelligent_grid(self, usable_area, wall_geometry, entrance_geometry):
        """Create placement grid with architectural awareness"""
        
        min_x, min_y, max_x, max_y = usable_area.bounds
        grid_size = 0.5
        
        grid_points = []
        
        y = min_y
        while y <= max_y:
            x = min_x
            while x <= max_x:
                point = Point(x, y)
                
                if usable_area.contains(point):
                    
                    wall_distance = self._calculate_wall_distance(point, wall_geometry)
                    entrance_distance = self._calculate_entrance_distance(point, entrance_geometry)
                    
                    if (wall_distance >= self.wall_clearance and 
                        entrance_distance >= self.entrance_clearance):
                        
                        grid_points.append((x, y))
                
                x += grid_size
            y += grid_size
        
        grid_points.sort(key=lambda p: self._calculate_grid_point_preference(
            Point(p), usable_area, wall_geometry, entrance_geometry
        ), reverse=True)
        
        return grid_points
    
    def _calculate_wall_distance(self, point, wall_geometry):
        """Calculate minimum distance to walls"""
        if not wall_geometry or not wall_geometry.get('lines'):
            return float('inf')
        
        min_distance = float('inf')
        for wall_line in wall_geometry['lines']:
            distance = point.distance(wall_line)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _calculate_entrance_distance(self, point, entrance_geometry):
        """Calculate minimum distance to entrances"""
        if not entrance_geometry or not entrance_geometry.get('points'):
            return float('inf')
        
        min_distance = float('inf')
        for entrance_point in entrance_geometry['points']:
            distance = point.distance(entrance_point)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _calculate_grid_point_preference(self, point, usable_area, wall_geometry, entrance_geometry):
        """Calculate preference score for grid point"""
        score = 0
        
        centroid = usable_area.centroid
        distance_from_center = point.distance(centroid)
        score += distance_from_center * 0.1
        
        wall_distance = self._calculate_wall_distance(point, wall_geometry)
        if 0.5 <= wall_distance <= 2.0:
            score += (2.0 - abs(wall_distance - 1.0)) * 0.3
        
        entrance_distance = self._calculate_entrance_distance(point, entrance_geometry)
        if entrance_distance > self.entrance_clearance:
            score += min(entrance_distance - self.entrance_clearance, 5.0) * 0.2
        
        return score
    
    def _intersects_with_buffer(self, candidate, occupied_space, buffer_distance):
        """Check if candidate intersects with buffered occupied space"""
        if occupied_space.is_empty:
            return False
        
        buffered_candidate = candidate.buffer(buffer_distance)
        return buffered_candidate.intersects(occupied_space)
    
    def _calculate_intelligent_placement_score(self, candidate, usable_area, existing_islands, 
                                             wall_geometry, entrance_geometry):
        """Calculate intelligent placement score"""
        score = 0
        
        if candidate.within(usable_area):
            score += 100
        
        wall_distance = self._calculate_wall_distance(candidate.centroid, wall_geometry)
        if wall_distance <= self.wall_clearance:
            entrance_distance = self._calculate_entrance_distance(candidate.centroid, entrance_geometry)
            if entrance_distance >= self.entrance_clearance:
                score += 50
        elif 0.3 <= wall_distance <= 1.0:
            score += 30
        
        entrance_distance = self._calculate_entrance_distance(candidate.centroid, entrance_geometry)
        if entrance_distance < self.entrance_clearance:
            score -= 100
        elif entrance_distance < self.entrance_clearance * 1.5:
            score -= 50
        
        if existing_islands:
            distances = [candidate.centroid.distance(island.centroid) for island in existing_islands]
            min_distance = min(distances)
            avg_distance = sum(distances) / len(distances)
            
            if 2.0 <= min_distance <= 4.0:
                score += 20
            
            if abs(min_distance - avg_distance) < 1.0:
                score += 10
        
        area_efficiency = candidate.area / (candidate.bounds[2] - candidate.bounds[0]) / (candidate.bounds[3] - candidate.bounds[1])
        score += area_efficiency * 10
        
        return score
    
    def _generate_mandatory_corridor_network(self, usable_area, islands, corridor_width):
        """Generate mandatory corridors between facing îlot rows"""
        
        if len(islands) < 2:
            return []
        
        island_rows = self._identify_island_rows(islands)
        
        corridors = []
        
        for i, row1 in enumerate(island_rows):
            for j, row2 in enumerate(island_rows[i+1:], i+1):
                
                if self._are_rows_facing(row1, row2):
                    
                    corridor = self._create_corridor_between_rows(
                        row1, row2, usable_area, corridor_width
                    )
                    
                    if corridor and not corridor.is_empty:
                        corridors.append({
                            'geometry': corridor,
                            'area': corridor.area,
                            'width': corridor_width,
                            'connects': [i, j]
                        })
        
        if len(corridors) < len(island_rows) - 1:
            additional_corridors = self._generate_mst_corridors(
                islands, usable_area, corridor_width, existing_corridors=corridors
            )
            corridors.extend(additional_corridors)
        
        return corridors
    
    def _identify_island_rows(self, islands):
        """Identify rows of islands for corridor generation"""
        
        if not islands:
            return []
        
        y_tolerance = 2.0
        
        island_centers = [(island.centroid.x, island.centroid.y, i) for i, island in enumerate(islands)]
        island_centers.sort(key=lambda x: x[1])
        
        rows = []
        current_row = [island_centers[0]]
        
        for center in island_centers[1:]:
            if abs(center[1] - current_row[-1][1]) <= y_tolerance:
                current_row.append(center)
            else:
                if len(current_row) >= 2:
                    rows.append(current_row)
                current_row = [center]
        
        if len(current_row) >= 2:
            rows.append(current_row)
        
        island_rows = []
        for row in rows:
            row_islands = [islands[center[2]] for center in row]
            island_rows.append(row_islands)
        
        return island_rows
    
    def _are_rows_facing(self, row1, row2):
        """Check if two rows are facing each other"""
        
        avg_y1 = sum(island.centroid.y for island in row1) / len(row1)
        avg_y2 = sum(island.centroid.y for island in row2) / len(row2)
        
        y_separation = abs(avg_y2 - avg_y1)
        
        min_x1 = min(island.bounds[0] for island in row1)
        max_x1 = max(island.bounds[2] for island in row1)
        min_x2 = min(island.bounds[0] for island in row2)
        max_x2 = max(island.bounds[2] for island in row2)
        
        x_overlap = min(max_x1, max_x2) - max(min_x1, min_x2)
        
        return y_separation >= 2.0 and x_overlap > 0
    
    def _create_corridor_between_rows(self, row1, row2, usable_area, corridor_width):
        """Create corridor between two facing rows"""
        
        try:
            min_y1 = min(island.bounds[1] for island in row1)
            max_y1 = max(island.bounds[3] for island in row1)
            min_y2 = min(island.bounds[1] for island in row2)
            max_y2 = max(island.bounds[3] for island in row2)
            
            if max_y1 < min_y2:
                corridor_y1 = max_y1
                corridor_y2 = min_y2
            else:
                corridor_y1 = max_y2
                corridor_y2 = min_y1
            
            min_x1 = min(island.bounds[0] for island in row1)
            max_x1 = max(island.bounds[2] for island in row1)
            min_x2 = min(island.bounds[0] for island in row2)
            max_x2 = max(island.bounds[2] for island in row2)
            
            corridor_x1 = max(min_x1, min_x2)
            corridor_x2 = min(max_x1, max_x2)
            
            if corridor_x2 <= corridor_x1:
                return None
            
            corridor_rect = box(corridor_x1, corridor_y1, corridor_x2, corridor_y2)
            corridor = corridor_rect.intersection(usable_area)
            
            if hasattr(corridor, 'bounds'):
                bounds = corridor.bounds
                actual_width = min(bounds[2] - bounds[0], bounds[3] - bounds[1])
                
                if actual_width < corridor_width:
                    center_x = (bounds[0] + bounds[2]) / 2
                    center_y = (bounds[1] + bounds[3]) / 2
                    
                    half_width = corridor_width / 2
                    
                    if bounds[2] - bounds[0] < corridor_width:
                        expanded_rect = box(center_x - half_width, bounds[1], 
                                          center_x + half_width, bounds[3])
                    else:
                        expanded_rect = box(bounds[0], center_y - half_width, 
                                          bounds[2], center_y + half_width)
                    
                    corridor = expanded_rect.intersection(usable_area)
            
            return corridor
            
        except Exception:
            return None
    
    def _generate_mst_corridors(self, islands, usable_area, corridor_width, existing_corridors):
        """Generate additional corridors using minimum spanning tree"""
        
        if len(islands) < 2:
            return []
        
        G = nx.Graph()
        
        for i, island in enumerate(islands):
            G.add_node(i, pos=island.centroid)
        
        for i in range(len(islands)):
            for j in range(i + 1, len(islands)):
                distance = islands[i].centroid.distance(islands[j].centroid)
                if distance < 15.0:
                    G.add_edge(i, j, weight=distance)
        
        if G.edges():
            mst = nx.minimum_spanning_tree(G)
            
            additional_corridors = []
            
            for edge in mst.edges():
                i, j = edge
                
                if not self._connection_exists(i, j, existing_corridors):
                    
                    corridor = self._create_simple_corridor(
                        islands[i], islands[j], usable_area, corridor_width
                    )
                    
                    if corridor and not corridor.is_empty:
                        additional_corridors.append({
                            'geometry': corridor,
                            'area': corridor.area,
                            'width': corridor_width,
                            'connects': [i, j]
                        })
            
            return additional_corridors
        
        return []
    
    def _connection_exists(self, i, j, existing_corridors):
        """Check if connection between islands i and j already exists"""
        for corridor in existing_corridors:
            connects = corridor.get('connects', [])
            if (i in connects and j in connects) or (j in connects and i in connects):
                return True
        return False
    
    def _create_simple_corridor(self, island1, island2, usable_area, corridor_width):
        """Create simple corridor between two islands"""
        
        try:
            p1 = island1.centroid
            p2 = island2.centroid
            
            corridor_line = LineString([p1, p2])
            corridor_poly = corridor_line.buffer(corridor_width / 2)
            
            corridor_clipped = corridor_poly.intersection(usable_area)
            corridor_final = corridor_clipped.difference(unary_union([island1, island2]))
            
            return corridor_final
            
        except Exception:
            return None
    
    def _categorize_islands_by_size(self, islands):
        """Categorize islands by size with color coding"""
        
        categorized = {
            'small': {'islands': [], 'color': '#22C55E', 'outline': '#16A34A'},
            'medium': {'islands': [], 'color': '#3B82F6', 'outline': '#2563EB'},
            'large': {'islands': [], 'color': '#F59E0B', 'outline': '#D97706'},
            'xlarge': {'islands': [], 'color': '#EF4444', 'outline': '#DC2626'}
        }
        
        for island in islands:
            area = island.area
            
            if area <= 6:
                category = 'small'
            elif area <= 12:
                category = 'medium'
            elif area <= 20:
                category = 'large'
            else:
                category = 'xlarge'
            
            categorized[category]['islands'].append(island)
        
        return categorized
    
    def _calculate_optimization_stats(self, usable_area, islands, corridors, target_coverage):
        """Calculate comprehensive optimization statistics"""
        
        total_usable_area = usable_area.area
        total_island_area = sum(island.area for island in islands)
        total_corridor_area = sum(corridor['area'] for corridor in corridors)
        
        actual_coverage = total_island_area / total_usable_area if total_usable_area > 0 else 0
        coverage_efficiency = actual_coverage / target_coverage if target_coverage > 0 else 0
        
        free_area = total_usable_area - total_island_area - total_corridor_area
        accessibility_ratio = (total_corridor_area + free_area) / total_usable_area if total_usable_area > 0 else 0
        
        if islands:
            island_areas = [island.area for island in islands]
            avg_island_area = sum(island_areas) / len(island_areas)
            island_area_variance = sum((area - avg_island_area) ** 2 for area in island_areas) / len(island_areas)
            placement_efficiency = 1.0 / (1.0 + island_area_variance / avg_island_area) if avg_island_area > 0 else 0
        else:
            placement_efficiency = 0
        
        return {
            'total_usable_area': total_usable_area,
            'total_island_area': total_island_area,
            'total_corridor_area': total_corridor_area,
            'free_area': free_area,
            'islands_placed': len(islands),
            'corridors_created': len(corridors),
            'target_coverage': target_coverage,
            'actual_coverage': actual_coverage,
            'coverage_efficiency': coverage_efficiency,
            'accessibility_ratio': accessibility_ratio,
            'placement_efficiency': placement_efficiency,
            'avg_corridor_width': sum(c['width'] for c in corridors) / len(corridors) if corridors else 0
        }

def optimize_intelligent_layout(usable_area, island_dimensions, corridor_width=1.2, 
                              coverage_profile='medium', wall_geometry=None, entrance_geometry=None):
    """Main intelligent optimization function"""
    optimizer = IntelligentIlotOptimizer()
    return optimizer.optimize_intelligent_layout(
        usable_area, island_dimensions, corridor_width, coverage_profile, 
        wall_geometry, entrance_geometry
    )