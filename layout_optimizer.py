import numpy as np
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
import networkx as nx
from scipy.spatial.distance import cdist
import random
import math

class LayoutOptimizer:
    def __init__(self):
        self.corridor_width = 1.2
        self.min_island_spacing = 0.5
        self.wall_clearance = 0.3
        self.entrance_clearance = 2.0
        
    def optimize_layout(self, usable_area, island_dimensions, corridor_width=1.2, coverage_profile=0.25):
        """Intelligent îlot placement with corridor network generation"""
        print(f"Optimizing layout with {coverage_profile*100}% coverage profile...")
        
        self.corridor_width = corridor_width
        
        if not usable_area or usable_area.is_empty:
            return {"islands": [], "corridors": [], "stats": {}}
        
        # Calculate target coverage area
        total_area = usable_area.area
        target_island_area = total_area * coverage_profile
        
        # Generate island sizes based on profile and dimensions
        islands_to_place = self._generate_island_sizes(island_dimensions, target_island_area)
        
        # Place islands using advanced algorithms
        placed_islands = self._place_islands_optimized(usable_area, islands_to_place)
        
        # Generate corridor network
        corridors = self._generate_corridor_network(usable_area, placed_islands)
        
        # Calculate statistics
        stats = self._calculate_stats(usable_area, placed_islands, corridors)
        
        return {
            "islands": placed_islands,
            "corridors": corridors,
            "stats": stats
        }
    
    def _generate_island_sizes(self, base_dimensions, target_area):
        """Generate island sizes to achieve target coverage"""
        if not base_dimensions:
            # Default island sizes if none provided
            base_dimensions = [(3, 2), (4, 3), (5, 4), (2, 2)]
        
        islands = []
        current_area = 0
        
        # Sort by area (largest first for better packing)
        sorted_dims = sorted(base_dimensions, key=lambda d: d[0] * d[1], reverse=True)
        
        while current_area < target_area and len(islands) < 100:  # Prevent infinite loop
            for width, height in sorted_dims:
                island_area = width * height
                if current_area + island_area <= target_area * 1.1:  # Allow 10% overage
                    islands.append((width, height))
                    current_area += island_area
                    
                if current_area >= target_area:
                    break
            
            # If we can't fit any more standard sizes, break
            if current_area < target_area and not any(
                current_area + w * h <= target_area * 1.1 for w, h in sorted_dims
            ):
                break
        
        print(f"Generated {len(islands)} islands for target area {target_area:.1f}m²")
        return islands
    
    def _place_islands_optimized(self, usable_area, islands_to_place):
        """Advanced island placement using multiple algorithms"""
        placed_islands = []
        
        if not islands_to_place:
            return placed_islands
        
        # Get usable area bounds
        min_x, min_y, max_x, max_y = usable_area.bounds
        
        # Try different placement strategies
        strategies = [
            self._place_grid_based,
            self._place_random_optimized,
            self._place_edge_following
        ]
        
        best_result = []
        best_coverage = 0
        
        for strategy in strategies:
            result = strategy(usable_area, islands_to_place.copy())
            coverage = sum(island.area for island in result) / usable_area.area
            
            if coverage > best_coverage:
                best_coverage = coverage
                best_result = result
        
        print(f"Best placement achieved {best_coverage*100:.1f}% coverage with {len(best_result)} islands")
        return best_result
    
    def _place_grid_based(self, usable_area, islands_to_place):
        """Grid-based placement algorithm"""
        placed = []
        occupied_space = Polygon()
        
        min_x, min_y, max_x, max_y = usable_area.bounds
        grid_size = 0.5  # 50cm grid
        
        # Sort islands by area (largest first)
        islands_to_place.sort(key=lambda d: d[0] * d[1], reverse=True)
        
        for width, height in islands_to_place:
            best_position = None
            best_score = -1
            
            # Try different orientations
            for w, h in [(width, height), (height, width)]:
                y = min_y
                while y + h <= max_y:
                    x = min_x
                    while x + w <= max_x:
                        candidate = box(x, y, x + w, y + h)
                        
                        if (candidate.within(usable_area) and 
                            not candidate.intersects(occupied_space)):
                            
                            # Score based on position (prefer corners and edges)
                            score = self._calculate_position_score(candidate, usable_area, placed)
                            
                            if score > best_score:
                                best_score = score
                                best_position = candidate
                        
                        x += grid_size
                    y += grid_size
            
            if best_position:
                placed.append(best_position)
                occupied_space = unary_union([occupied_space, best_position.buffer(self.min_island_spacing)])
        
        return placed
    
    def _place_random_optimized(self, usable_area, islands_to_place):
        """Random placement with optimization"""
        placed = []
        occupied_space = Polygon()
        
        min_x, min_y, max_x, max_y = usable_area.bounds
        max_attempts = 1000
        
        for width, height in islands_to_place:
            best_position = None
            best_score = -1
            
            for attempt in range(max_attempts):
                # Random position
                x = random.uniform(min_x, max_x - width)
                y = random.uniform(min_y, max_y - height)
                
                # Try both orientations
                for w, h in [(width, height), (height, width)]:
                    if x + w > max_x or y + h > max_y:
                        continue
                        
                    candidate = box(x, y, x + w, y + h)
                    
                    if (candidate.within(usable_area) and 
                        not candidate.intersects(occupied_space)):
                        
                        score = self._calculate_position_score(candidate, usable_area, placed)
                        
                        if score > best_score:
                            best_score = score
                            best_position = candidate
            
            if best_position:
                placed.append(best_position)
                occupied_space = unary_union([occupied_space, best_position.buffer(self.min_island_spacing)])
        
        return placed
    
    def _place_edge_following(self, usable_area, islands_to_place):
        """Edge-following placement algorithm"""
        placed = []
        occupied_space = Polygon()
        
        # Get boundary coordinates
        if hasattr(usable_area.boundary, 'coords'):
            boundary_coords = list(usable_area.boundary.coords)
        else:
            return []  # Can't follow edge of complex geometry
        
        for width, height in islands_to_place:
            best_position = None
            best_score = -1
            
            # Try placing along the boundary
            for i in range(0, len(boundary_coords) - 1, 5):  # Sample every 5th point
                x, y = boundary_coords[i]
                
                # Try different offsets from the boundary
                for offset in [0.5, 1.0, 1.5, 2.0]:
                    for w, h in [(width, height), (height, width)]:
                        candidate = box(x + offset, y + offset, x + offset + w, y + offset + h)
                        
                        if (candidate.within(usable_area) and 
                            not candidate.intersects(occupied_space)):
                            
                            score = self._calculate_position_score(candidate, usable_area, placed)
                            
                            if score > best_score:
                                best_score = score
                                best_position = candidate
            
            if best_position:
                placed.append(best_position)
                occupied_space = unary_union([occupied_space, best_position.buffer(self.min_island_spacing)])
        
        return placed
    
    def _calculate_position_score(self, candidate, usable_area, existing_islands):
        """Calculate score for island position"""
        score = 0
        
        # Prefer positions away from center (better for circulation)
        centroid = usable_area.centroid
        distance_from_center = candidate.centroid.distance(centroid)
        score += distance_from_center * 0.1
        
        # Prefer positions that create regular spacing
        if existing_islands:
            min_distance = min(candidate.centroid.distance(island.centroid) for island in existing_islands)
            score += min_distance * 0.2
        
        # Prefer positions near walls (realistic furniture placement)
        boundary_distance = candidate.distance(usable_area.boundary)
        if boundary_distance < 1.0:
            score += (1.0 - boundary_distance) * 0.3
        
        return score
    
    def _generate_corridor_network(self, usable_area, islands):
        """Generate corridor network using graph algorithms"""
        if len(islands) < 2:
            return []
        
        print("Generating corridor network...")
        
        # Create graph of island positions
        G = nx.Graph()
        
        # Add nodes (island centroids)
        for i, island in enumerate(islands):
            G.add_node(i, pos=island.centroid)
        
        # Add edges between nearby islands
        positions = [island.centroid for island in islands]
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                distance = positions[i].distance(positions[j])
                if distance < 10.0:  # Only connect nearby islands
                    G.add_edge(i, j, weight=distance)
        
        # Find minimum spanning tree for efficient corridor network
        if G.edges():
            mst = nx.minimum_spanning_tree(G)
            corridors = self._create_corridors_from_graph(mst, islands, usable_area)
        else:
            corridors = []
        
        print(f"Generated {len(corridors)} corridor segments")
        return corridors
    
    def _create_corridors_from_graph(self, graph, islands, usable_area):
        """Create corridor geometries from graph"""
        corridors = []
        
        for edge in graph.edges():
            i, j = edge
            island1 = islands[i]
            island2 = islands[j]
            
            # Create corridor between islands
            corridor = self._create_corridor_between_islands(island1, island2, usable_area)
            if corridor and not corridor.is_empty:
                corridors.append(corridor)
        
        return corridors
    
    def _create_corridor_between_islands(self, island1, island2, usable_area):
        """Create a corridor between two islands"""
        # Find closest points between islands
        p1 = island1.centroid
        p2 = island2.centroid
        
        # Create corridor line
        corridor_line = LineString([p1, p2])
        
        # Buffer to create corridor polygon
        corridor_poly = corridor_line.buffer(self.corridor_width / 2)
        
        # Clip to usable area
        corridor_clipped = corridor_poly.intersection(usable_area)
        
        # Remove intersections with islands
        corridor_final = corridor_clipped.difference(unary_union([island1, island2]))
        
        return corridor_final
    
    def _calculate_stats(self, usable_area, islands, corridors):
        """Calculate layout statistics"""
        total_area = usable_area.area
        island_area = sum(island.area for island in islands)
        corridor_area = sum(corridor.area for corridor in corridors)
        
        return {
            'total_area': total_area,
            'island_area': island_area,
            'corridor_area': corridor_area,
            'free_area': total_area - island_area - corridor_area,
            'island_coverage': island_area / total_area if total_area > 0 else 0,
            'corridor_coverage': corridor_area / total_area if total_area > 0 else 0,
            'islands_placed': len(islands),
            'corridors_created': len(corridors)
        }

def optimize_layout(usable_area, island_dimensions, corridor_width=1.2):
    """Main optimization function for backward compatibility"""
    optimizer = LayoutOptimizer()
    return optimizer.optimize_layout(usable_area, island_dimensions, corridor_width)