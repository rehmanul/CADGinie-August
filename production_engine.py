#!/usr/bin/env python3

import time
import logging
from typing import Dict, Any, Tuple
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
import numpy as np

logger = logging.getLogger(__name__)

class ProductionFloorPlanEngine:
    """Production-grade floor plan processing engine"""
    
    def __init__(self, cad_processor, layout_optimizer, renderer):
        self.cad_processor = cad_processor
        self.layout_optimizer = layout_optimizer
        self.renderer = renderer
        
        # Production configuration
        self.config = {
            'min_room_area': 4.0,  # m²
            'min_corridor_width': 0.8,  # m
            'max_corridor_width': 3.0,  # m
            'accessibility_clearance': 1.5,  # m
            'wall_thickness_tolerance': 0.1,  # m
            'geometric_precision': 0.01,  # m
            'coverage_profiles': {
                '10%': 0.10,
                '25%': 0.25,
                '30%': 0.30,
                '35%': 0.35
            }
        }
    
    def process_complete_floorplan(self, file_path: str, islands: str, 
                                 corridor_width: float, coverage_profile: str,
                                 wall_layer: str = '0', prohibited_layer: str = 'PROHIBITED',
                                 entrance_layer: str = 'DOORS') -> Dict[str, Any]:
        """Complete production floor plan processing pipeline"""
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting production processing: {file_path}")
            
            # Phase 1: Advanced CAD Processing
            logger.info("Phase 1: Advanced CAD file processing...")
            cad_result = self.cad_processor.process_advanced_cad(
                file_path=file_path,
                wall_layer=wall_layer,
                prohibited_layer=prohibited_layer,
                entrance_layer=entrance_layer
            )
            
            if not cad_result['success']:
                return {'success': False, 'error': f"CAD processing failed: {cad_result['error']}"}
            
            geometry = cad_result['geometry']
            
            # Phase 2: Geometry Validation and Enhancement
            logger.info("Phase 2: Geometry validation and enhancement...")
            geometry = self._validate_and_enhance_geometry(geometry)
            
            # Phase 3: Intelligent Layout Optimization
            logger.info("Phase 3: Intelligent îlot placement...")
            layout_result = self.layout_optimizer.optimize_intelligent_layout(
                geometry=geometry,
                islands=islands,
                coverage_profile=self.config['coverage_profiles'].get(coverage_profile, 0.25),
                corridor_width=corridor_width
            )
            
            if not layout_result['success']:
                return {'success': False, 'error': f"Layout optimization failed: {layout_result['error']}"}
            
            layout = layout_result['layout']
            
            # Phase 4: Corridor Network Generation
            logger.info("Phase 4: Corridor network generation...")
            corridor_result = self._generate_corridor_network(geometry, layout, corridor_width)
            
            if corridor_result['success']:
                layout['corridors'] = corridor_result['corridors']
                layout['circulation_graph'] = corridor_result['circulation_graph']
            
            # Phase 5: Quality Assurance and Validation
            logger.info("Phase 5: Quality assurance...")
            qa_result = self._perform_quality_assurance(geometry, layout)
            
            # Phase 6: Statistics and Metrics
            logger.info("Phase 6: Calculating statistics...")
            statistics = self._calculate_comprehensive_statistics(geometry, layout)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Production processing completed in {processing_time:.2f}s")
            
            return {
                'success': True,
                'geometry': geometry,
                'layout': layout,
                'statistics': statistics,
                'quality_assurance': qa_result,
                'processing_time': processing_time,
                'metadata': {
                    'file_path': file_path,
                    'coverage_profile': coverage_profile,
                    'corridor_width': corridor_width,
                    'timestamp': time.time()
                }
            }
            
        except Exception as e:
            logger.error(f"Production processing error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _validate_and_enhance_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance geometric data"""
        
        enhanced_geometry = geometry.copy()
        
        # Validate walls
        if 'walls' in geometry:
            walls = geometry['walls']
            if hasattr(walls, 'is_valid') and not walls.is_valid:
                logger.warning("Invalid wall geometry detected, attempting repair...")
                enhanced_geometry['walls'] = walls.buffer(0)  # Repair invalid geometry
        
        # Validate restricted areas
        if 'restricted_areas' in geometry:
            restricted = geometry['restricted_areas']
            if hasattr(restricted, 'is_valid') and not restricted.is_valid:
                logger.warning("Invalid restricted area geometry detected, attempting repair...")
                enhanced_geometry['restricted_areas'] = restricted.buffer(0)
        
        # Calculate usable area
        if 'walls' in enhanced_geometry and 'restricted_areas' in enhanced_geometry:
            walls = enhanced_geometry['walls']
            restricted = enhanced_geometry['restricted_areas']
            
            if hasattr(walls, 'area') and hasattr(restricted, 'area'):
                try:
                    usable_area = walls.difference(restricted) if not restricted.is_empty else walls
                    enhanced_geometry['usable_area'] = usable_area
                    enhanced_geometry['total_area'] = walls.area
                    enhanced_geometry['restricted_area'] = restricted.area
                    enhanced_geometry['usable_area_value'] = usable_area.area
                except Exception as e:
                    logger.warning(f"Error calculating usable area: {str(e)}")
        
        return enhanced_geometry
    
    def _generate_corridor_network(self, geometry: Dict[str, Any], 
                                 layout: Dict[str, Any], 
                                 corridor_width: float) -> Dict[str, Any]:
        """Generate intelligent corridor network"""
        
        try:
            corridors = []
            circulation_graph = {'nodes': [], 'edges': []}
            
            if 'islands' not in layout or not layout['islands']:
                return {'success': True, 'corridors': corridors, 'circulation_graph': circulation_graph}
            
            islands = layout['islands']
            
            # Group islands by proximity for corridor generation
            island_groups = self._group_islands_for_corridors(islands)
            
            corridor_id = 0
            for group in island_groups:
                if len(group) >= 2:
                    # Generate corridor between island groups
                    corridor = self._create_corridor_between_groups(group, corridor_width)
                    
                    if corridor and corridor.area > 0.5:  # Minimum corridor area
                        corridors.append({
                            'id': corridor_id,
                            'geometry': corridor,
                            'width': corridor_width,
                            'area': corridor.area,
                            'connected_islands': [island['id'] for island in group]
                        })
                        corridor_id += 1
            
            # Build circulation graph
            circulation_graph = self._build_circulation_graph(islands, corridors)
            
            return {
                'success': True,
                'corridors': corridors,
                'circulation_graph': circulation_graph
            }
            
        except Exception as e:
            logger.error(f"Corridor generation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _group_islands_for_corridors(self, islands: list) -> list:
        """Group islands that should be connected by corridors"""
        
        groups = []
        processed = set()
        
        for i, island1 in enumerate(islands):
            if i in processed:
                continue
            
            group = [island1]
            processed.add(i)
            
            # Find nearby islands
            for j, island2 in enumerate(islands):
                if j in processed:
                    continue
                
                # Calculate distance between island centers
                center1 = island1['geometry'].centroid
                center2 = island2['geometry'].centroid
                
                distance = center1.distance(center2)
                
                # If islands are close enough, group them
                if distance < 15:  # 15m maximum corridor length
                    group.append(island2)
                    processed.add(j)
            
            if len(group) >= 2:
                groups.append(group)
        
        return groups
    
    def _create_corridor_between_groups(self, island_group: list, width: float) -> Polygon:
        """Create corridor geometry between island groups"""
        
        try:
            # Find the two most distant islands in the group
            max_distance = 0
            island1, island2 = None, None
            
            for i in range(len(island_group)):
                for j in range(i + 1, len(island_group)):
                    center1 = island_group[i]['geometry'].centroid
                    center2 = island_group[j]['geometry'].centroid
                    distance = center1.distance(center2)
                    
                    if distance > max_distance:
                        max_distance = distance
                        island1, island2 = island_group[i], island_group[j]
            
            if not island1 or not island2:
                return None
            
            # Create corridor line between islands
            center1 = island1['geometry'].centroid
            center2 = island2['geometry'].centroid
            
            corridor_line = LineString([center1, center2])
            corridor_polygon = corridor_line.buffer(width / 2)
            
            return corridor_polygon
            
        except Exception as e:
            logger.error(f"Corridor creation error: {str(e)}")
            return None
    
    def _build_circulation_graph(self, islands: list, corridors: list) -> Dict[str, Any]:
        """Build circulation graph for pathfinding"""
        
        nodes = []
        edges = []
        
        # Add island nodes
        for island in islands:
            center = island['geometry'].centroid
            nodes.append({
                'id': island['id'],
                'type': 'island',
                'position': (center.x, center.y),
                'area': island['geometry'].area
            })
        
        # Add corridor edges
        for corridor in corridors:
            connected_islands = corridor['connected_islands']
            
            for i in range(len(connected_islands)):
                for j in range(i + 1, len(connected_islands)):
                    edges.append({
                        'from': connected_islands[i],
                        'to': connected_islands[j],
                        'corridor_id': corridor['id'],
                        'width': corridor['width'],
                        'length': corridor['area'] / corridor['width']
                    })
        
        return {'nodes': nodes, 'edges': edges}
    
    def _perform_quality_assurance(self, geometry: Dict[str, Any], 
                                 layout: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive quality assurance"""
        
        qa_results = {
            'accessibility_compliant': True,
            'building_code_compliant': True,
            'geometric_validity': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check accessibility compliance
            if 'corridors' in layout:
                for corridor in layout['corridors']:
                    if corridor['width'] < self.config['min_corridor_width']:
                        qa_results['accessibility_compliant'] = False
                        qa_results['warnings'].append(
                            f"Corridor width {corridor['width']:.2f}m below minimum {self.config['min_corridor_width']}m"
                        )
            
            # Check island placement
            if 'islands' in layout:
                for island in layout['islands']:
                    if not island['geometry'].is_valid:
                        qa_results['geometric_validity'] = False
                        qa_results['errors'].append(f"Invalid island geometry: {island['id']}")
            
            # Check for overlaps
            if 'islands' in layout and len(layout['islands']) > 1:
                for i, island1 in enumerate(layout['islands']):
                    for j, island2 in enumerate(layout['islands'][i+1:], i+1):
                        if island1['geometry'].intersects(island2['geometry']):
                            intersection_area = island1['geometry'].intersection(island2['geometry']).area
                            if intersection_area > 0.1:  # 0.1m² tolerance
                                qa_results['building_code_compliant'] = False
                                qa_results['errors'].append(
                                    f"Island overlap detected: {island1['id']} and {island2['id']}"
                                )
            
        except Exception as e:
            logger.error(f"Quality assurance error: {str(e)}")
            qa_results['errors'].append(f"QA process error: {str(e)}")
        
        return qa_results
    
    def _calculate_comprehensive_statistics(self, geometry: Dict[str, Any], 
                                          layout: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        
        stats = {
            'total_area': 0,
            'usable_area': 0,
            'restricted_area': 0,
            'islands_placed': 0,
            'total_island_area': 0,
            'corridors_created': 0,
            'total_corridor_area': 0,
            'coverage_percentage': 0,
            'efficiency_score': 0,
            'accessibility_score': 100
        }
        
        try:
            # Geometry statistics
            if 'total_area' in geometry:
                stats['total_area'] = geometry['total_area']
            
            if 'usable_area_value' in geometry:
                stats['usable_area'] = geometry['usable_area_value']
            
            if 'restricted_area' in geometry:
                stats['restricted_area'] = geometry['restricted_area']
            
            # Layout statistics
            if 'islands' in layout:
                stats['islands_placed'] = len(layout['islands'])
                stats['total_island_area'] = sum(
                    island['geometry'].area for island in layout['islands']
                )
            
            if 'corridors' in layout:
                stats['corridors_created'] = len(layout['corridors'])
                stats['total_corridor_area'] = sum(
                    corridor['area'] for corridor in layout['corridors']
                )
            
            # Calculate coverage percentage
            if stats['usable_area'] > 0:
                stats['coverage_percentage'] = (stats['total_island_area'] / stats['usable_area']) * 100
            
            # Calculate efficiency score
            stats['efficiency_score'] = min(100, stats['coverage_percentage'] * 2)
            
            # Accessibility score (based on corridor compliance)
            if 'corridors' in layout:
                compliant_corridors = sum(
                    1 for corridor in layout['corridors'] 
                    if corridor['width'] >= self.config['min_corridor_width']
                )
                if layout['corridors']:
                    stats['accessibility_score'] = (compliant_corridors / len(layout['corridors'])) * 100
            
        except Exception as e:
            logger.error(f"Statistics calculation error: {str(e)}")
        
        return stats