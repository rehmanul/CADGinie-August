#!/usr/bin/env python3

import requests
import json
import hmac
import hashlib
import base64
import time
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

class OnshapeAPIProcessor:
    """Onshape API CAD processor"""
    
    def __init__(self):
        self.access_key = "on_PyORcNYDukpBv5Kv15kXT"
        self.secret_key = "Pc1g9Hrf4QvbfKVOPBGoYADh2zh1t6CPaTL4UUy20rTFh6Xj"
        self.base_url = "https://cad.onshape.com"
        
    def process_cad_file(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """Process CAD file using Onshape API"""
        
        try:
            logger.info(f"🔧 Processing {file_name} with Onshape API...")
            
            # Upload and create document
            document_result = self._create_document(file_path, file_name)
            if not document_result['success']:
                return document_result
            
            # Get document elements
            elements = self._get_document_elements(document_result['document_id'])
            
            # Extract geometry from parts
            geometry_data = self._extract_geometry_from_parts(
                document_result['document_id'], 
                elements
            )
            
            return {
                'success': True,
                'geometry': geometry_data,
                'metadata': {
                    'processor': 'Onshape API',
                    'document_id': document_result['document_id'],
                    'elements_count': len(elements)
                }
            }
            
        except Exception as e:
            logger.error(f"Onshape API processing failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_document(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """Create Onshape document from uploaded file"""
        
        try:
            # Create document
            create_url = f"{self.base_url}/api/documents"
            create_data = {
                'name': f"FloorPlan_{int(time.time())}",
                'ownerType': 0,
                'isPublic': False
            }
            
            headers = self._get_auth_headers('POST', create_url, create_data)
            
            response = requests.post(create_url, json=create_data, headers=headers)
            
            if response.status_code == 200:
                doc_data = response.json()
                document_id = doc_data['id']
                
                # Upload file to document
                upload_result = self._upload_file_to_document(document_id, file_path, file_name)
                
                if upload_result['success']:
                    return {
                        'success': True,
                        'document_id': document_id,
                        'workspace_id': doc_data['defaultWorkspace']['id']
                    }
                else:
                    return upload_result
            else:
                return {'success': False, 'error': f'Document creation failed: {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _upload_file_to_document(self, document_id: str, file_path: str, file_name: str) -> Dict[str, Any]:
        """Upload file to Onshape document"""
        
        try:
            upload_url = f"{self.base_url}/api/documents/{document_id}/workspaces/w/upload"
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, 'application/octet-stream')}
                
                headers = self._get_auth_headers('POST', upload_url)
                
                response = requests.post(upload_url, files=files, headers=headers)
                
                if response.status_code == 200:
                    return {'success': True}
                else:
                    return {'success': False, 'error': f'Upload failed: {response.status_code}'}
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_document_elements(self, document_id: str) -> list:
        """Get document elements"""
        
        try:
            elements_url = f"{self.base_url}/api/documents/{document_id}/workspaces/w/elements"
            headers = self._get_auth_headers('GET', elements_url)
            
            response = requests.get(elements_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting elements: {str(e)}")
            return []
    
    def _extract_geometry_from_parts(self, document_id: str, elements: list) -> Dict[str, Any]:
        """Extract geometry from Onshape parts"""
        
        geometry = {
            'walls': None,
            'restricted_areas': None,
            'entrances': None
        }
        
        try:
            for element in elements:
                if element.get('type') == 'Part Studio':
                    element_id = element['id']
                    
                    # Get part geometry
                    part_geometry = self._get_part_geometry(document_id, element_id)
                    
                    # Classify geometry based on part properties
                    classified = self._classify_onshape_geometry(part_geometry)
                    
                    # Merge with existing geometry
                    for key, geom in classified.items():
                        if geom and geometry[key]:
                            geometry[key] = unary_union([geometry[key], geom])
                        elif geom:
                            geometry[key] = geom
            
            return geometry
            
        except Exception as e:
            logger.error(f"Geometry extraction error: {str(e)}")
            return geometry
    
    def _get_part_geometry(self, document_id: str, element_id: str) -> Dict[str, Any]:
        """Get part geometry from Onshape"""
        
        try:
            # Get part faces
            faces_url = f"{self.base_url}/api/parts/d/{document_id}/w/w/e/{element_id}/faces"
            headers = self._get_auth_headers('GET', faces_url)
            
            response = requests.get(faces_url, headers=headers)
            
            if response.status_code == 200:
                faces_data = response.json()
                
                # Get tessellated geometry
                tessellation_url = f"{self.base_url}/api/parts/d/{document_id}/w/w/e/{element_id}/tessellatedfaces"
                tess_response = requests.get(tessellation_url, headers=headers)
                
                if tess_response.status_code == 200:
                    return {
                        'faces': faces_data,
                        'tessellation': tess_response.json()
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Part geometry error: {str(e)}")
            return {}
    
    def _classify_onshape_geometry(self, part_geometry: Dict) -> Dict[str, Any]:
        """Classify Onshape geometry into architectural elements"""
        
        classified = {
            'walls': None,
            'restricted_areas': None,
            'entrances': None
        }
        
        try:
            tessellation = part_geometry.get('tessellation', {})
            faces = tessellation.get('faces', [])
            
            # Extract 2D profiles from 3D tessellation
            wall_polygons = []
            
            for face in faces:
                vertices = face.get('vertices', [])
                if len(vertices) >= 3:
                    # Project to 2D (assume Z=0 plane)
                    points_2d = [(v[0], v[1]) for v in vertices if len(v) >= 2]
                    
                    if len(points_2d) >= 3:
                        try:
                            polygon = Polygon(points_2d)
                            if polygon.is_valid and polygon.area > 1:  # Minimum area threshold
                                wall_polygons.append(polygon)
                        except:
                            pass
            
            if wall_polygons:
                classified['walls'] = unary_union(wall_polygons)
            
            return classified
            
        except Exception as e:
            logger.error(f"Geometry classification error: {str(e)}")
            return classified
    
    def _get_auth_headers(self, method: str, url: str, data: Dict = None) -> Dict[str, str]:
        """Generate Onshape API authentication headers"""
        
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            query = parsed_url.query
            
            # Create auth string
            auth_date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
            nonce = base64.b64encode(str(time.time()).encode()).decode()
            
            content_type = 'application/json' if data else ''
            
            # Build string to sign
            string_to_sign = f"{method}\n{nonce}\n{auth_date}\n{content_type}\n{path}"
            if query:
                string_to_sign += f"?{query}"
            
            # Create signature
            signature = base64.b64encode(
                hmac.new(
                    self.secret_key.encode(),
                    string_to_sign.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()
            
            # Build authorization header
            auth_header = f"On {self.access_key}:HmacSHA256:{signature}"
            
            return {
                'Authorization': auth_header,
                'Date': auth_date,
                'On-Nonce': nonce,
                'Content-Type': content_type,
                'Accept': 'application/json'
            }
            
        except Exception as e:
            logger.error(f"Auth header generation error: {str(e)}")
            return {}

onshape_processor = OnshapeAPIProcessor()