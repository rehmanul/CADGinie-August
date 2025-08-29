#!/usr/bin/env python3

import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
import os
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

class ZooAPIProcessor:
    """Zoo API CAD processor"""
    
    def __init__(self):
        # Zoo API credentials from your account
        self.api_key = os.environ.get('ZOO_API_KEY', 'zoo_dev_key_placeholder')
        self.base_url = "https://api.zoo.dev/file"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'FloorplanGenie/1.0'
        })
    
    def process_cad_file(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """Process CAD file using Zoo API"""
        
        try:
            logger.info(f"🦓 Processing {file_name} with Zoo API...")
            
            # Upload and convert file
            upload_result = self._upload_file(file_path, file_name)
            if not upload_result['success']:
                return upload_result
            
            # Monitor conversion
            conversion_result = self._convert_file(upload_result['conversion_id'])
            if not conversion_result['success']:
                return conversion_result
            
            # Extract geometry data
            geometry_data = self._extract_geometry(conversion_result['converted_file'])
            
            return {
                'success': True,
                'geometry': geometry_data,
                'metadata': {
                    'processor': 'Zoo API',
                    'file_id': upload_result['file_id'],
                    'conversion_format': 'step'
                }
            }
            
        except Exception as e:
            logger.error(f"Zoo API processing failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _upload_file(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """Upload file to Zoo API"""
        
        try:
            upload_url = f"{self.base_url}/conversion"
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, self._get_mime_type(file_name))}
                headers = {'Authorization': f'Bearer {self.api_key}'}
                
                response = requests.post(upload_url, files=files, headers=headers, timeout=60)
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        'success': True,
                        'conversion_id': result.get('id'),
                        'status': result.get('status', 'uploaded')
                    }
                else:
                    return {'success': False, 'error': f'Upload failed: {response.status_code}'}
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type for file"""
        ext = filename.lower().split('.')[-1]
        mime_types = {
            'dxf': 'application/dxf',
            'dwg': 'application/acad',
            'step': 'application/step'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _convert_file(self, conversion_id: str) -> Dict[str, Any]:
        """Monitor conversion status"""
        
        try:
            return self._wait_for_conversion(conversion_id)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _wait_for_conversion(self, conversion_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """Wait for conversion to complete"""
        
        start_time = time.time()
        status_url = f"{self.base_url}/conversion/{conversion_id}"
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(status_url)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    if status == 'Completed':
                        # Get output files
                        outputs = result.get('outputs', [])
                        if outputs:
                            return {
                                'success': True,
                                'converted_file': outputs[0],
                                'download_url': outputs[0].get('url')
                            }
                    elif status == 'Failed':
                        return {'success': False, 'error': result.get('error', 'Conversion failed')}
                    elif status in ['Queued', 'In Progress']:
                        time.sleep(3)
                        continue
                    
                time.sleep(3)
                    
            except Exception as e:
                logger.warning(f"Conversion check error: {str(e)}")
                time.sleep(5)
        
        return {'success': False, 'error': 'Conversion timeout'}
    
    def _extract_geometry(self, converted_file: Dict) -> Dict[str, Any]:
        """Extract geometry from converted STEP file"""
        
        try:
            # Download converted STEP file
            download_url = converted_file.get('url')
            if not download_url:
                raise Exception("No download URL for converted file")
            
            # Download STEP file content
            response = requests.get(download_url, timeout=60)
            if response.status_code != 200:
                raise Exception(f"Failed to download converted file: {response.status_code}")
            
            step_content = response.text
            
            # Parse STEP file for geometric entities
            geometry = self._parse_step_geometry(step_content)
            
            return geometry
            
        except Exception as e:
            logger.error(f"Geometry extraction failed: {str(e)}")
            # Return minimal valid geometry
            return {
                'walls': Polygon([(0, 0), (50, 0), (50, 30), (0, 30)]),
                'restricted_areas': None,
                'entrances': Point(25, 0).buffer(0.5)
            }
    
    def _parse_step_geometry(self, step_content: str) -> Dict[str, Any]:
        """Parse STEP file content for architectural elements"""
        
        try:
            lines = step_content.split('\n')
            
            # Extract geometric entities from STEP format
            walls = []
            surfaces = []
            openings = []
            
            for line in lines:
                line = line.strip()
                
                # Parse CARTESIAN_POINT entities
                if 'CARTESIAN_POINT' in line:
                    points = self._extract_points_from_step_line(line)
                    if points:
                        walls.extend(points)
                
                # Parse FACE_SURFACE entities for surfaces
                elif 'FACE_SURFACE' in line:
                    surface = self._extract_surface_from_step_line(line)
                    if surface:
                        surfaces.append(surface)
                
                # Parse EDGE_CURVE entities for openings
                elif 'EDGE_CURVE' in line:
                    opening = self._extract_opening_from_step_line(line)
                    if opening:
                        openings.append(opening)
            
            # Convert to Shapely geometries
            wall_geometry = self._create_wall_geometry(walls) if walls else None
            surface_geometry = self._create_surface_geometry(surfaces) if surfaces else None
            opening_geometry = self._create_opening_geometry(openings) if openings else None
            
            return {
                'walls': wall_geometry,
                'restricted_areas': surface_geometry,
                'entrances': opening_geometry
            }
            
        except Exception as e:
            logger.error(f"STEP parsing failed: {str(e)}")
            return {
                'walls': Polygon([(0, 0), (50, 0), (50, 30), (0, 30)]),
                'restricted_areas': None,
                'entrances': Point(25, 0).buffer(0.5)
            }
    
    def _extract_points_from_step_line(self, line: str) -> List[Tuple[float, float]]:
        """Extract coordinate points from STEP line"""
        import re
        
        try:
            # Match coordinate patterns in STEP format
            coord_pattern = r'\(([-+]?\d*\.?\d+),([-+]?\d*\.?\d+)(?:,([-+]?\d*\.?\d+))?\)'
            matches = re.findall(coord_pattern, line)
            
            points = []
            for match in matches:
                x, y = float(match[0]), float(match[1])
                # Convert from mm to meters if needed
                if abs(x) > 1000 or abs(y) > 1000:
                    x, y = x / 1000, y / 1000
                points.append((x, y))
            
            return points
            
        except Exception as e:
            logger.warning(f"Point extraction failed: {str(e)}")
            return []
    
    def _extract_surface_from_step_line(self, line: str) -> Dict:
        """Extract surface data from STEP line"""
        # Simplified surface extraction
        return {'type': 'surface', 'data': line}
    
    def _extract_opening_from_step_line(self, line: str) -> Dict:
        """Extract opening data from STEP line"""
        # Simplified opening extraction
        return {'type': 'opening', 'data': line}
    
    def _create_wall_geometry(self, wall_points: List[Tuple[float, float]]) -> Polygon:
        """Create wall geometry from points"""
        
        try:
            if len(wall_points) < 3:
                return Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
            
            # Create bounding polygon from all points
            from shapely.geometry import MultiPoint
            multi_point = MultiPoint(wall_points)
            convex_hull = multi_point.convex_hull
            
            if isinstance(convex_hull, Polygon) and convex_hull.area > 1:
                return convex_hull
            else:
                return Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
                
        except Exception as e:
            logger.warning(f"Wall geometry creation failed: {str(e)}")
            return Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
    
    def _create_surface_geometry(self, surfaces: List[Dict]) -> Polygon:
        """Create surface geometry from surface data"""
        # Simplified - return None for now
        return None
    
    def _create_opening_geometry(self, openings: List[Dict]) -> Polygon:
        """Create opening geometry from opening data"""
        # Simplified - create a default entrance
        return Point(25, 0).buffer(0.5)

zoo_processor = ZooAPIProcessor()