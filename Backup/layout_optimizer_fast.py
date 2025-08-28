import numpy as np
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
import random

class FastLayoutOptimizer:
    def __init__(self):
        self.corridor_width = 1.2
        self.min_spacing = 0.5
        
    def optimize_layout(self, usable_area, island_dimensions, corridor_width=1.2, coverage_profile=0.25):
        """Fast island placement - single optimized algorithm"""
        print(f"Fast optimization: {coverage_profile*100}% coverage...")
        
        if not usable_area or usable_area.is_empty:
            return {"islands": [], "corridors": [], "stats": {}}
        
        # Quick island generation
        target_area = usable_area.area * coverage_profile
        islands_to_place = self._quick_island_sizes(island_dimensions, target_area)
        
        # Fast placement
        placed_islands = self._fast_placement(usable_area, islands_to_place)
        
        # Simple corridors
        corridors = self._simple_corridors(usable_area, placed_islands, corridor_width)
        
        # Quick stats
        stats = self._quick_stats(usable_area, placed_islands, corridors)
        
        return {"islands": placed_islands, "corridors": corridors, "stats": stats}
    
    def _quick_island_sizes(self, base_dims, target_area):
        """Generate islands quickly"""
        if not base_dims:
            base_dims = [(3, 2), (4, 3), (2, 2)]
        
        islands = []
        current_area = 0
        
        # Simple approach - repeat largest islands
        largest = max(base_dims, key=lambda d: d[0] * d[1])
        
        while current_area < target_area and len(islands) < 50:
            for w, h in base_dims:
                if current_area + w * h <= target_area * 1.1:
                    islands.append((w, h))
                    current_area += w * h
                if current_area >= target_area:
                    break
            if not islands or current_area >= target_area:
                break
                
        return islands[:20]  # Limit for speed
    
    def _fast_placement(self, usable_area, islands_to_place):
        """Fast grid placement - single pass"""
        placed = []
        min_x, min_y, max_x, max_y = usable_area.bounds
        
        # Larger grid for speed
        grid_size = 1.0
        occupied = set()
        
        for width, height in islands_to_place:
            placed_island = False
            
            # Quick grid search
            y = min_y
            while y + height <= max_y and not placed_island:
                x = min_x
                while x + width <= max_x and not placed_island:
                    # Quick grid check
                    grid_x, grid_y = int(x), int(y)
                    if (grid_x, grid_y) not in occupied:
                        
                        candidate = box(x, y, x + width, y + height)
                        
                        if candidate.within(usable_area):
                            placed.append(candidate)
                            
                            # Mark grid cells as occupied
                            for gx in range(grid_x, grid_x + int(width) + 1):
                                for gy in range(grid_y, grid_y + int(height) + 1):
                                    occupied.add((gx, gy))
                            
                            placed_island = True
                    
                    x += grid_size
                y += grid_size
        
        print(f"Fast placement: {len(placed)} islands")
        return placed
    
    def _simple_corridors(self, usable_area, islands, corridor_width):
        """Simple corridor generation"""
        if len(islands) < 2:
            return []
        
        corridors = []
        
        # Create simple connecting corridors
        for i in range(len(islands) - 1):
            island1 = islands[i]
            island2 = islands[i + 1]
            
            # Simple rectangular corridor
            x1, y1 = island1.centroid.x, island1.centroid.y
            x2, y2 = island2.centroid.x, island2.centroid.y
            
            # L-shaped corridor
            corridor1 = box(min(x1, x2) - corridor_width/2, y1 - corridor_width/2,
                           max(x1, x2) + corridor_width/2, y1 + corridor_width/2)
            corridor2 = box(x2 - corridor_width/2, min(y1, y2) - corridor_width/2,
                           x2 + corridor_width/2, max(y1, y2) + corridor_width/2)
            
            for corridor in [corridor1, corridor2]:
                clipped = corridor.intersection(usable_area)
                if not clipped.is_empty:
                    corridors.append(clipped)
        
        return corridors[:10]  # Limit for speed
    
    def _quick_stats(self, usable_area, islands, corridors):
        """Quick statistics calculation"""
        total_area = usable_area.area
        island_area = sum(island.area for island in islands)
        corridor_area = sum(corridor.area for corridor in corridors)
        
        return {
            'total_area': total_area,
            'island_area': island_area,
            'corridor_area': corridor_area,
            'island_coverage': island_area / total_area if total_area > 0 else 0,
            'islands_placed': len(islands),
            'corridors_created': len(corridors)
        }

def optimize_layout(usable_area, island_dimensions, corridor_width=1.2):
    """Fast optimization function"""
    optimizer = FastLayoutOptimizer()
    return optimizer.optimize_layout(usable_area, island_dimensions, corridor_width)