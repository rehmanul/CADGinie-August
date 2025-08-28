#!/usr/bin/env python3

import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import networkx as nx
from scipy.spatial import distance_matrix
from scipy.optimize import differential_evolution
import logging
from typing import Dict, Any, List, Tuple
import random
import math

logger = logging.getLogger(__name__)

class IntelligentLayoutOptimizer:
    """Intelligent îlot placement and layout optimization engine"""
    
    def __init__(self):
        self.optimization_algorithms = {
            'genetic': self._genetic_algorithm,
            'grid_based': self._grid_based_placement,
            'force_directed': self._force_directed_placement,
            'accessibility_optimized': self._accessibility_optimized_placement
        }
        
        # Îlot size categories with colors
        self.ilot_categories = {
            'small': {'max_area': 6, 'color': '#10B981', 'outline': '#059669'},
            'medium': {'max_area': 15, 'color': '#059669', 'outline': '#047857'},
            'large': {'max_area': 30, 'color': '#047857', 'outline': '#065F46'},
            'extra_large': {'max_area': float('inf'), 'color': '#065F46', 'outline': '#064E3B'}
        }
        
        # Accessibility requirements
        self.accessibility_config = {
            'min_clearance': 1.5,  # meters
            'entrance_clearance': 2.0,  # meters
            'corridor_width': 1.2,  # meters
            'max_travel_distance': 30.0  # meters
        }
    
    def optimize_intelligent_layout(self, geometry: Dict[str, Any], islands: str, 
                                  coverage_profile: float, corridor_width: float) -> Dict[str, Any]:
        """Optimize îlot layout using intelligent algorithms"""
        
        try:
            logger.info(f"Starting intelligent layout optimization with {coverage_profile*100}% coverage")
            
            # Parse îlot specifications
            ilot_specs = self._parse_ilot_specifications(islands)
            
            # Prepare optimization space
            optimization_space = self._prepare_optimization_space(geometry)
            
            if not optimization_space or optimization_space.area < 0.1:
                logger.warning(f"Optimization space area: {optimization_space.area if optimization_space else 'None'}")
                # Create working space from file bounds
                from shapely.geometry import box
                if 'walls' in geometry and geometry['walls']:
                    bounds = geometry['walls'].bounds
                    optimization_space = box(bounds[0], bounds[1], bounds[2], bounds[3])
                else:
                    optimization_space = box(0, 0, 50, 30)  # Standard room size
                logger.info(f"Using fallback optimization space: {optimization_space.area:.1f}m²")
            
            # Run multiple optimization algorithms
            optimization_results = []
            
            for algorithm_name, algorithm_func in self.optimization_algorithms.items():
                try:
                    result = algorithm_func(
                        optimization_space, ilot_specs, coverage_profile, 
                        geometry, corridor_width
                    )
                    
                    if result['success']:
                        result['algorithm'] = algorithm_name
                        optimization_results.append(result)
                        logger.info(f"{algorithm_name} algorithm: {len(result['islands'])} îlots placed")
                        
                except Exception as e:
                    logger.warning(f"{algorithm_name} algorithm failed: {str(e)}")
            
            if not optimization_results:
                return {'success': False, 'error': 'All optimization algorithms failed'}
            
            # Select best result based on multiple criteria
            best_result = self._select_best_layout(optimization_results, coverage_profile)
            
            # Enhance layout with intelligent features
            enhanced_layout = self._enhance_layout_intelligence(best_result['layout'], geometry)
            
            return {
                'success': True,
                'layout': enhanced_layout,
                'optimization_stats': {
                    'algorithms_tried': len(self.optimization_algorithms),
                    'successful_algorithms': len(optimization_results),
                    'best_algorithm': best_result['algorithm'],
                    'coverage_achieved': best_result['coverage_achieved'],
                    'accessibility_score': best_result['accessibility_score']
                }
            }
            
        except Exception as e:
            logger.error(f"Layout optimization error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _parse_ilot_specifications(self, islands: str) -> List[Dict[str, Any]]:
        """Parse îlot specifications from string"""
        
        ilot_specs = []
        
        try:
            # Parse format: "3x2,4x3,5x4"
            for spec in islands.split(','):
                spec = spec.strip()
                if 'x' in spec:
                    width, height = map(float, spec.split('x'))
                    area = width * height
                    
                    # Categorize îlot
                    category = 'extra_large'
                    for cat_name, cat_info in self.ilot_categories.items():
                        if area <= cat_info['max_area']:
                            category = cat_name
                            break
                    
                    ilot_specs.append({
                        'width': width,
                        'height': height,
                        'area': area,
                        'category': category,
                        'color': self.ilot_categories[category]['color'],
                        'outline': self.ilot_categories[category]['outline']
                    })
            
            logger.info(f"Parsed {len(ilot_specs)} îlot specifications")
            
        except Exception as e:
            logger.error(f"Error parsing îlot specifications: {str(e)}")
        
        return ilot_specs
    
    def _prepare_optimization_space(self, geometry: Dict[str, Any]) -> Polygon:
        """Prepare optimization space by removing restricted areas"""
        
        try:
            # Start with walls as base space
            if 'walls' not in geometry or geometry['walls'] is None:
                return None
            
            usable_space = geometry['walls']
            
            # Remove restricted areas
            if 'restricted_areas' in geometry and geometry['restricted_areas'] is not None:
                restricted = geometry['restricted_areas']
                if not restricted.is_empty:
                    usable_space = usable_space.difference(restricted)
            
            # Remove entrance clearance zones
            if 'entrances' in geometry and geometry['entrances'] is not None:
                entrances = geometry['entrances']
                if not entrances.is_empty:
                    # Create clearance buffer around entrances
                    entrance_clearance = entrances.buffer(self.accessibility_config['entrance_clearance'])
                    usable_space = usable_space.difference(entrance_clearance)
            
            # Ensure result is valid
            if hasattr(usable_space, 'is_valid') and not usable_space.is_valid:
                usable_space = usable_space.buffer(0)
            
            logger.info(f"Optimization space prepared: {usable_space.area:.2f}m²")
            
            return usable_space
            
        except Exception as e:
            logger.error(f"Error preparing optimization space: {str(e)}")
            return None
    
    def _genetic_algorithm(self, optimization_space: Polygon, ilot_specs: List[Dict], 
                          coverage_profile: float, geometry: Dict, corridor_width: float) -> Dict[str, Any]:
        """Genetic algorithm for îlot placement optimization"""
        
        try:
            # Calculate target number of îlots
            total_ilot_area = sum(spec['area'] for spec in ilot_specs)
            target_coverage_area = optimization_space.area * coverage_profile
            num_ilots_target = int(target_coverage_area / (total_ilot_area / len(ilot_specs)))
            
            # Generate initial population
            population_size = 50
            generations = 100
            
            population = []
            for _ in range(population_size):
                individual = self._generate_random_layout(
                    optimization_space, ilot_specs, num_ilots_target
                )
                population.append(individual)
            
            # Evolution loop
            for generation in range(generations):
                # Evaluate fitness
                fitness_scores = []
                for individual in population:
                    fitness = self._evaluate_layout_fitness(
                        individual, optimization_space, coverage_profile, geometry
                    )
                    fitness_scores.append(fitness)
                
                # Selection and reproduction
                new_population = []
                
                # Keep best individuals (elitism)
                sorted_indices = np.argsort(fitness_scores)[::-1]
                elite_size = population_size // 10
                
                for i in range(elite_size):
                    new_population.append(population[sorted_indices[i]])
                
                # Generate offspring
                while len(new_population) < population_size:
                    parent1 = self._tournament_selection(population, fitness_scores)
                    parent2 = self._tournament_selection(population, fitness_scores)
                    
                    offspring = self._crossover(parent1, parent2, optimization_space)
                    offspring = self._mutate(offspring, optimization_space, ilot_specs)
                    
                    new_population.append(offspring)
                
                population = new_population
            
            # Return best solution
            final_fitness = [self._evaluate_layout_fitness(ind, optimization_space, coverage_profile, geometry) 
                           for ind in population]
            best_index = np.argmax(final_fitness)
            best_layout = population[best_index]
            
            return {
                'success': True,
                'layout': {'islands': best_layout},
                'coverage_achieved': sum(island['geometry'].area for island in best_layout) / optimization_space.area,
                'accessibility_score': self._calculate_accessibility_score(best_layout, geometry)
            }
            
        except Exception as e:
            logger.error(f"Genetic algorithm error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _grid_based_placement(self, optimization_space: Polygon, ilot_specs: List[Dict], 
                            coverage_profile: float, geometry: Dict, corridor_width: float) -> Dict[str, Any]:
        """Grid-based îlot placement algorithm"""
        
        try:
            placed_islands = []
            
            # Get optimization space bounds
            bounds = optimization_space.bounds
            min_x, min_y, max_x, max_y = bounds
            
            # Calculate grid spacing
            avg_ilot_size = np.mean([spec['width'] for spec in ilot_specs])
            grid_spacing = avg_ilot_size + corridor_width
            
            # Generate grid points
            x_points = np.arange(min_x + avg_ilot_size/2, max_x - avg_ilot_size/2, grid_spacing)
            y_points = np.arange(min_y + avg_ilot_size/2, max_y - avg_ilot_size/2, grid_spacing)
            
            island_id = 0
            target_area = optimization_space.area * coverage_profile
            current_area = 0
            
            # Place îlots on grid
            for x in x_points:
                for y in y_points:
                    if current_area >= target_area:
                        break
                    
                    # Select îlot specification
                    spec = ilot_specs[island_id % len(ilot_specs)]
                    
                    # Create îlot geometry
                    ilot_center = Point(x, y)
                    ilot_rect = box(
                        x - spec['width']/2, y - spec['height']/2,
                        x + spec['width']/2, y + spec['height']/2
                    )
                    
                    # Check placement validity
                    if self._is_valid_placement(ilot_rect, optimization_space, placed_islands, geometry):
                        island = {
                            'id': island_id,
                            'geometry': ilot_rect,
                            'center': (x, y),
                            'width': spec['width'],
                            'height': spec['height'],
                            'area': spec['area'],
                            'category': spec['category'],
                            'color': spec['color'],
                            'outline': spec['outline']
                        }
                        
                        placed_islands.append(island)
                        current_area += spec['area']
                        island_id += 1
                
                if current_area >= target_area:
                    break
            
            return {
                'success': True,
                'layout': {'islands': placed_islands},
                'coverage_achieved': current_area / optimization_space.area,
                'accessibility_score': self._calculate_accessibility_score(placed_islands, geometry)
            }
            
        except Exception as e:
            logger.error(f"Grid-based placement error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _force_directed_placement(self, optimization_space: Polygon, ilot_specs: List[Dict], 
                                coverage_profile: float, geometry: Dict, corridor_width: float) -> Dict[str, Any]:
        """Force-directed îlot placement algorithm"""
        
        try:
            # Start with random placement
            initial_layout = self._generate_random_layout(
                optimization_space, ilot_specs, 
                int(optimization_space.area * coverage_profile / np.mean([spec['area'] for spec in ilot_specs]))
            )
            
            # Apply force-directed optimization
            optimized_layout = self._apply_force_directed_optimization(
                initial_layout, optimization_space, corridor_width
            )
            
            return {
                'success': True,
                'layout': {'islands': optimized_layout},
                'coverage_achieved': sum(island['geometry'].area for island in optimized_layout) / optimization_space.area,
                'accessibility_score': self._calculate_accessibility_score(optimized_layout, geometry)
            }
            
        except Exception as e:
            logger.error(f"Force-directed placement error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _accessibility_optimized_placement(self, optimization_space: Polygon, ilot_specs: List[Dict], 
                                         coverage_profile: float, geometry: Dict, corridor_width: float) -> Dict[str, Any]:
        """Accessibility-optimized îlot placement algorithm"""
        
        try:
            placed_islands = []
            
            # Identify high-accessibility zones
            accessibility_zones = self._identify_accessibility_zones(optimization_space, geometry)
            
            # Sort zones by accessibility score
            sorted_zones = sorted(accessibility_zones, key=lambda z: z['accessibility_score'], reverse=True)
            
            island_id = 0
            target_area = optimization_space.area * coverage_profile
            current_area = 0
            
            # Place îlots in high-accessibility zones first
            for zone in sorted_zones:
                if current_area >= target_area:
                    break
                
                zone_islands = self._place_islands_in_zone(
                    zone, ilot_specs, island_id, corridor_width
                )
                
                for island in zone_islands:
                    if current_area >= target_area:
                        break
                    
                    if self._is_valid_placement(island['geometry'], optimization_space, placed_islands, geometry):
                        placed_islands.append(island)
                        current_area += island['area']
                        island_id += 1
            
            return {
                'success': True,
                'layout': {'islands': placed_islands},
                'coverage_achieved': current_area / optimization_space.area,
                'accessibility_score': self._calculate_accessibility_score(placed_islands, geometry)
            }
            
        except Exception as e:
            logger.error(f"Accessibility-optimized placement error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_random_layout(self, optimization_space: Polygon, ilot_specs: List[Dict], 
                              num_ilots: int) -> List[Dict]:
        """Generate random îlot layout"""
        
        placed_islands = []
        bounds = optimization_space.bounds
        
        attempts = 0
        max_attempts = num_ilots * 50
        
        while len(placed_islands) < num_ilots and attempts < max_attempts:
            attempts += 1
            
            # Random position
            x = random.uniform(bounds[0], bounds[2])
            y = random.uniform(bounds[1], bounds[3])
            
            # Random îlot specification
            spec = random.choice(ilot_specs)
            
            # Create îlot geometry
            ilot_rect = box(
                x - spec['width']/2, y - spec['height']/2,
                x + spec['width']/2, y + spec['height']/2
            )
            
            # Check placement validity
            if self._is_valid_placement(ilot_rect, optimization_space, placed_islands, {}):
                island = {
                    'id': len(placed_islands),
                    'geometry': ilot_rect,
                    'center': (x, y),
                    'width': spec['width'],
                    'height': spec['height'],
                    'area': spec['area'],
                    'category': spec['category'],
                    'color': spec['color'],
                    'outline': spec['outline']
                }
                
                placed_islands.append(island)
        
        return placed_islands
    
    def _is_valid_placement(self, ilot_geometry: Polygon, optimization_space: Polygon, 
                          existing_islands: List[Dict], geometry: Dict) -> bool:
        """Check if îlot placement is valid"""
        
        try:
            # Check if îlot is within optimization space
            if not optimization_space.contains(ilot_geometry):
                return False
            
            # Check for overlaps with existing îlots
            for existing_island in existing_islands:
                if ilot_geometry.intersects(existing_island['geometry']):
                    intersection_area = ilot_geometry.intersection(existing_island['geometry']).area
                    if intersection_area > 0.01:  # 1cm² tolerance
                        return False
            
            # Check clearance from entrances
            if 'entrances' in geometry and geometry['entrances'] is not None:
                entrances = geometry['entrances']
                if not entrances.is_empty:
                    min_distance = ilot_geometry.distance(entrances)
                    if min_distance < self.accessibility_config['entrance_clearance']:
                        return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Placement validation error: {str(e)}")
            return False
    
    def _evaluate_layout_fitness(self, layout: List[Dict], optimization_space: Polygon, 
                               coverage_profile: float, geometry: Dict) -> float:
        """Evaluate layout fitness for genetic algorithm"""
        
        try:
            fitness = 0.0
            
            # Coverage score
            total_area = sum(island['geometry'].area for island in layout)
            target_area = optimization_space.area * coverage_profile
            coverage_score = 1.0 - abs(total_area - target_area) / target_area
            fitness += coverage_score * 0.4
            
            # Accessibility score
            accessibility_score = self._calculate_accessibility_score(layout, geometry)
            fitness += accessibility_score * 0.3
            
            # Distribution score (avoid clustering)
            distribution_score = self._calculate_distribution_score(layout)
            fitness += distribution_score * 0.2
            
            # Overlap penalty
            overlap_penalty = self._calculate_overlap_penalty(layout)
            fitness -= overlap_penalty * 0.1
            
            return max(0.0, fitness)
            
        except Exception as e:
            logger.warning(f"Fitness evaluation error: {str(e)}")
            return 0.0
    
    def _calculate_accessibility_score(self, layout: List[Dict], geometry: Dict) -> float:
        """Calculate accessibility score for layout"""
        
        try:
            if not layout:
                return 0.0
            
            accessibility_score = 1.0
            
            # Check entrance accessibility
            if 'entrances' in geometry and geometry['entrances'] is not None:
                entrances = geometry['entrances']
                
                for island in layout:
                    min_distance = island['geometry'].distance(entrances)
                    if min_distance < self.accessibility_config['entrance_clearance']:
                        accessibility_score -= 0.1
            
            # Check inter-îlot clearances
            for i, island1 in enumerate(layout):
                for island2 in layout[i+1:]:
                    distance = island1['geometry'].distance(island2['geometry'])
                    if distance < self.accessibility_config['min_clearance']:
                        accessibility_score -= 0.05
            
            return max(0.0, accessibility_score)
            
        except Exception as e:
            logger.warning(f"Accessibility score calculation error: {str(e)}")
            return 0.0
    
    def _calculate_distribution_score(self, layout: List[Dict]) -> float:
        """Calculate distribution score (higher for better distribution)"""
        
        try:
            if len(layout) < 2:
                return 1.0
            
            # Calculate center points
            centers = [island['center'] for island in layout]
            
            # Calculate pairwise distances
            distances = []
            for i, center1 in enumerate(centers):
                for center2 in centers[i+1:]:
                    dist = math.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
                    distances.append(dist)
            
            # Score based on distance variance (lower variance = better distribution)
            if distances:
                mean_distance = np.mean(distances)
                variance = np.var(distances)
                normalized_variance = variance / (mean_distance**2) if mean_distance > 0 else 1.0
                return max(0.0, 1.0 - normalized_variance)
            
            return 1.0
            
        except Exception as e:
            logger.warning(f"Distribution score calculation error: {str(e)}")
            return 0.0
    
    def _calculate_overlap_penalty(self, layout: List[Dict]) -> float:
        """Calculate overlap penalty"""
        
        try:
            penalty = 0.0
            
            for i, island1 in enumerate(layout):
                for island2 in layout[i+1:]:
                    if island1['geometry'].intersects(island2['geometry']):
                        intersection_area = island1['geometry'].intersection(island2['geometry']).area
                        penalty += intersection_area / min(island1['area'], island2['area'])
            
            return penalty
            
        except Exception as e:
            logger.warning(f"Overlap penalty calculation error: {str(e)}")
            return 0.0
    
    def _tournament_selection(self, population: List, fitness_scores: List) -> List[Dict]:
        """Tournament selection for genetic algorithm"""
        
        tournament_size = 3
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        
        winner_index = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_index]
    
    def _crossover(self, parent1: List[Dict], parent2: List[Dict], optimization_space: Polygon) -> List[Dict]:
        """Crossover operation for genetic algorithm"""
        
        try:
            # Simple crossover: take random îlots from each parent
            offspring = []
            
            all_islands = parent1 + parent2
            random.shuffle(all_islands)
            
            # Select non-overlapping îlots
            for island in all_islands:
                if self._is_valid_placement(island['geometry'], optimization_space, offspring, {}):
                    offspring.append(island.copy())
                    offspring[-1]['id'] = len(offspring) - 1
            
            return offspring
            
        except Exception as e:
            logger.warning(f"Crossover error: {str(e)}")
            return parent1
    
    def _mutate(self, individual: List[Dict], optimization_space: Polygon, ilot_specs: List[Dict]) -> List[Dict]:
        """Mutation operation for genetic algorithm"""
        
        try:
            mutation_rate = 0.1
            mutated = individual.copy()
            
            for i, island in enumerate(mutated):
                if random.random() < mutation_rate:
                    # Small random displacement
                    bounds = optimization_space.bounds
                    
                    new_x = island['center'][0] + random.uniform(-2, 2)
                    new_y = island['center'][1] + random.uniform(-2, 2)
                    
                    # Ensure within bounds
                    new_x = max(bounds[0] + island['width']/2, min(bounds[2] - island['width']/2, new_x))
                    new_y = max(bounds[1] + island['height']/2, min(bounds[3] - island['height']/2, new_y))
                    
                    # Update geometry
                    new_geometry = box(
                        new_x - island['width']/2, new_y - island['height']/2,
                        new_x + island['width']/2, new_y + island['height']/2
                    )
                    
                    # Check validity
                    other_islands = [mutated[j] for j in range(len(mutated)) if j != i]
                    if self._is_valid_placement(new_geometry, optimization_space, other_islands, {}):
                        mutated[i]['geometry'] = new_geometry
                        mutated[i]['center'] = (new_x, new_y)
            
            return mutated
            
        except Exception as e:
            logger.warning(f"Mutation error: {str(e)}")
            return individual
    
    def _select_best_layout(self, optimization_results: List[Dict], coverage_profile: float) -> Dict[str, Any]:
        """Select best layout from optimization results"""
        
        best_result = None
        best_score = -1
        
        for result in optimization_results:
            # Calculate composite score
            coverage_score = 1.0 - abs(result['coverage_achieved'] - coverage_profile)
            accessibility_score = result['accessibility_score']
            
            composite_score = coverage_score * 0.6 + accessibility_score * 0.4
            
            if composite_score > best_score:
                best_score = composite_score
                best_result = result
        
        return best_result
    
    def _enhance_layout_intelligence(self, layout: Dict[str, Any], geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance layout with intelligent features"""
        
        enhanced_layout = layout.copy()
        
        # Add intelligent routing paths
        if 'islands' in layout:
            enhanced_layout['routing_graph'] = self._create_routing_graph(layout['islands'])
            enhanced_layout['accessibility_paths'] = self._calculate_accessibility_paths(layout['islands'], geometry)
            enhanced_layout['optimization_metrics'] = self._calculate_optimization_metrics(layout['islands'], geometry)
        
        return enhanced_layout
    
    def _create_routing_graph(self, islands: List[Dict]) -> Dict[str, Any]:
        """Create routing graph between îlots"""
        
        graph = nx.Graph()
        
        # Add nodes
        for island in islands:
            graph.add_node(island['id'], pos=island['center'], area=island['area'])
        
        # Add edges based on proximity
        for i, island1 in enumerate(islands):
            for island2 in islands[i+1:]:
                distance = math.sqrt(
                    (island1['center'][0] - island2['center'][0])**2 +
                    (island1['center'][1] - island2['center'][1])**2
                )
                
                if distance < 20:  # Maximum connection distance
                    graph.add_edge(island1['id'], island2['id'], weight=distance)
        
        return {
            'nodes': list(graph.nodes(data=True)),
            'edges': list(graph.edges(data=True)),
            'connectivity': nx.is_connected(graph) if graph.nodes else False
        }
    
    def _calculate_accessibility_paths(self, islands: List[Dict], geometry: Dict[str, Any]) -> List[Dict]:
        """Calculate accessibility paths"""
        
        paths = []
        
        if 'entrances' in geometry and geometry['entrances'] is not None:
            entrances = geometry['entrances']
            
            for island in islands:
                # Find shortest path to nearest entrance
                min_distance = island['geometry'].distance(entrances)
                
                paths.append({
                    'island_id': island['id'],
                    'entrance_distance': min_distance,
                    'accessible': min_distance >= self.accessibility_config['entrance_clearance']
                })
        
        return paths
    
    def _calculate_optimization_metrics(self, islands: List[Dict], geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimization metrics"""
        
        metrics = {
            'total_islands': len(islands),
            'total_area': sum(island['area'] for island in islands),
            'average_area': np.mean([island['area'] for island in islands]) if islands else 0,
            'area_variance': np.var([island['area'] for island in islands]) if islands else 0,
            'spatial_efficiency': 0.0,
            'accessibility_compliance': 0.0
        }
        
        # Calculate spatial efficiency
        if islands:
            # Convex hull efficiency
            centers = [Point(island['center']) for island in islands]
            if len(centers) >= 3:
                from shapely.ops import unary_union
                convex_hull = unary_union(centers).convex_hull
                total_island_area = sum(island['area'] for island in islands)
                metrics['spatial_efficiency'] = total_island_area / convex_hull.area if convex_hull.area > 0 else 0
        
        # Calculate accessibility compliance
        accessible_islands = 0
        for island in islands:
            if 'entrances' in geometry and geometry['entrances'] is not None:
                distance = island['geometry'].distance(geometry['entrances'])
                if distance >= self.accessibility_config['entrance_clearance']:
                    accessible_islands += 1
        
        metrics['accessibility_compliance'] = accessible_islands / len(islands) if islands else 0
        
        return metrics
    
    def _identify_accessibility_zones(self, optimization_space: Polygon, geometry: Dict[str, Any]) -> List[Dict]:
        """Identify high-accessibility zones"""
        
        zones = []
        
        # Simple grid-based zone identification
        bounds = optimization_space.bounds
        zone_size = 10  # 10m x 10m zones
        
        x_zones = int((bounds[2] - bounds[0]) / zone_size) + 1
        y_zones = int((bounds[3] - bounds[1]) / zone_size) + 1
        
        for i in range(x_zones):
            for j in range(y_zones):
                zone_x = bounds[0] + i * zone_size
                zone_y = bounds[1] + j * zone_size
                
                zone_rect = box(zone_x, zone_y, zone_x + zone_size, zone_y + zone_size)
                zone_intersection = optimization_space.intersection(zone_rect)
                
                if zone_intersection.area > zone_size * zone_size * 0.5:  # At least 50% overlap
                    accessibility_score = self._calculate_zone_accessibility(zone_intersection, geometry)
                    
                    zones.append({
                        'geometry': zone_intersection,
                        'center': (zone_x + zone_size/2, zone_y + zone_size/2),
                        'accessibility_score': accessibility_score
                    })
        
        return zones
    
    def _calculate_zone_accessibility(self, zone: Polygon, geometry: Dict[str, Any]) -> float:
        """Calculate accessibility score for a zone"""
        
        score = 1.0
        
        # Distance to entrances
        if 'entrances' in geometry and geometry['entrances'] is not None:
            distance = zone.distance(geometry['entrances'])
            # Closer to entrances is better, but not too close
            if distance < self.accessibility_config['entrance_clearance']:
                score -= 0.5
            elif distance > self.accessibility_config['max_travel_distance']:
                score -= 0.3
        
        # Distance to restricted areas
        if 'restricted_areas' in geometry and geometry['restricted_areas'] is not None:
            distance = zone.distance(geometry['restricted_areas'])
            if distance < self.accessibility_config['min_clearance']:
                score -= 0.4
        
        return max(0.0, score)
    
    def _place_islands_in_zone(self, zone: Dict, ilot_specs: List[Dict], 
                             start_id: int, corridor_width: float) -> List[Dict]:
        """Place îlots within a specific zone"""
        
        islands = []
        zone_bounds = zone['geometry'].bounds
        
        # Simple grid placement within zone
        avg_size = np.mean([spec['width'] for spec in ilot_specs])
        spacing = avg_size + corridor_width
        
        x_positions = np.arange(zone_bounds[0] + avg_size/2, zone_bounds[2] - avg_size/2, spacing)
        y_positions = np.arange(zone_bounds[1] + avg_size/2, zone_bounds[3] - avg_size/2, spacing)
        
        island_id = start_id
        
        for x in x_positions:
            for y in y_positions:
                spec = ilot_specs[island_id % len(ilot_specs)]
                
                ilot_rect = box(
                    x - spec['width']/2, y - spec['height']/2,
                    x + spec['width']/2, y + spec['height']/2
                )
                
                if zone['geometry'].contains(ilot_rect):
                    island = {
                        'id': island_id,
                        'geometry': ilot_rect,
                        'center': (x, y),
                        'width': spec['width'],
                        'height': spec['height'],
                        'area': spec['area'],
                        'category': spec['category'],
                        'color': spec['color'],
                        'outline': spec['outline']
                    }
                    
                    islands.append(island)
                    island_id += 1
        
        return islands
    
    def _apply_force_directed_optimization(self, layout: List[Dict], optimization_space: Polygon, 
                                         corridor_width: float) -> List[Dict]:
        """Apply force-directed optimization to layout"""
        
        try:
            optimized_layout = [island.copy() for island in layout]
            
            # Optimization parameters
            iterations = 100
            learning_rate = 0.1
            
            for iteration in range(iterations):
                forces = {}
                
                # Calculate forces for each îlot
                for i, island in enumerate(optimized_layout):
                    force_x, force_y = 0.0, 0.0
                    
                    # Repulsion from other îlots
                    for j, other_island in enumerate(optimized_layout):
                        if i != j:
                            dx = island['center'][0] - other_island['center'][0]
                            dy = island['center'][1] - other_island['center'][1]
                            distance = math.sqrt(dx*dx + dy*dy)
                            
                            if distance > 0:
                                # Repulsion force (inverse square law)
                                force_magnitude = corridor_width**2 / distance**2
                                force_x += force_magnitude * dx / distance
                                force_y += force_magnitude * dy / distance
                    
                    # Attraction to center of optimization space
                    bounds = optimization_space.bounds
                    center_x = (bounds[0] + bounds[2]) / 2
                    center_y = (bounds[1] + bounds[3]) / 2
                    
                    dx_center = center_x - island['center'][0]
                    dy_center = center_y - island['center'][1]
                    
                    force_x += 0.01 * dx_center
                    force_y += 0.01 * dy_center
                    
                    forces[i] = (force_x, force_y)
                
                # Apply forces
                for i, (force_x, force_y) in forces.items():
                    island = optimized_layout[i]
                    
                    new_x = island['center'][0] + learning_rate * force_x
                    new_y = island['center'][1] + learning_rate * force_y
                    
                    # Create new geometry
                    new_geometry = box(
                        new_x - island['width']/2, new_y - island['height']/2,
                        new_x + island['width']/2, new_y + island['height']/2
                    )
                    
                    # Check if new position is valid
                    other_islands = [optimized_layout[j] for j in range(len(optimized_layout)) if j != i]
                    if self._is_valid_placement(new_geometry, optimization_space, other_islands, {}):
                        optimized_layout[i]['center'] = (new_x, new_y)
                        optimized_layout[i]['geometry'] = new_geometry
            
            return optimized_layout
            
        except Exception as e:
            logger.error(f"Force-directed optimization error: {str(e)}")
            return layout