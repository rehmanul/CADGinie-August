import os
import sys
from pathlib import Path

# Ensure the script can find the custom modules
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from parsers.dwg_dxf_parser import parse_dwg_dxf
from parsers.pdf_parser import parse_pdf
from geometry_processor import process_geometry
from layout_optimizer import optimize_layout
from visualizer import visualize_plan

class FloorPlanEngine:
    def __init__(self):
        self.supported_formats = {'.dxf', '.dwg', '.pdf'}
        self.coverage_profiles = {
            'low': 0.10,
            'medium': 0.25,
            'high': 0.30,
            'maximum': 0.35
        }
    
    def generate_floorplan(self, input_path, output_path, islands_str="", corridor_width=1.2, 
                          wall_layer="0", prohibited_layer="PROHIBITED", entrance_layer="ENTRANCE",
                          coverage_profile="medium"):
        """
        Advanced floor plan generation with full CAD processing pipeline
        """
        print("=== FLOORPLAN GENIE - PRODUCTION ENGINE ===")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        
        # Validate input
        if not self._validate_input(input_path):
            return None
        
        # Parse file based on format
        classified_entities = self._parse_file(input_path)
        if not classified_entities:
            print("ERROR: Failed to parse input file")
            return None
        
        # Process geometry with architectural intelligence
        processed_geometry = self._process_geometry(
            classified_entities, wall_layer, prohibited_layer, entrance_layer
        )
        if not processed_geometry:
            print("ERROR: Failed to process geometry")
            return None
        
        # Optimize layout with intelligent placement
        island_dimensions = self._parse_island_dimensions(islands_str)
        coverage = self.coverage_profiles.get(coverage_profile, 0.25)
        
        optimized_layout = self._optimize_layout(
            processed_geometry, island_dimensions, corridor_width, coverage
        )
        
        # Generate professional visualization
        result_path = self._create_visualization(
            processed_geometry, optimized_layout, output_path
        )
        
        # Print summary
        self._print_summary(processed_geometry, optimized_layout)
        
        return result_path
    
    def _validate_input(self, input_path):
        """Validate input file"""
        if not os.path.exists(input_path):
            print(f"ERROR: Input file not found: {input_path}")
            return False
        
        file_ext = Path(input_path).suffix.lower()
        if file_ext not in self.supported_formats:
            print(f"ERROR: Unsupported file format: {file_ext}")
            print(f"Supported formats: {', '.join(self.supported_formats)}")
            return False
        
        return True
    
    def _parse_file(self, input_path):
        """Parse input file with appropriate parser"""
        file_ext = Path(input_path).suffix.lower()
        
        print(f"\n--- PARSING {file_ext.upper()} FILE ---")
        
        try:
            if file_ext in ['.dxf', '.dwg']:
                return parse_dwg_dxf(input_path)
            elif file_ext == '.pdf':
                return parse_pdf(input_path)
        except Exception as e:
            print(f"ERROR: Parsing failed: {e}")
            return None
    
    def _process_geometry(self, classified_entities, wall_layer, prohibited_layer, entrance_layer):
        """Process geometry with architectural intelligence"""
        print("\n--- PROCESSING GEOMETRY ---")
        
        try:
            return process_geometry(
                classified_entities, wall_layer, prohibited_layer, entrance_layer
            )
        except Exception as e:
            print(f"ERROR: Geometry processing failed: {e}")
            return None
    
    def _optimize_layout(self, geometry, island_dimensions, corridor_width, coverage):
        """Optimize layout with intelligent algorithms"""
        print("\n--- OPTIMIZING LAYOUT ---")
        
        try:
            usable_area = geometry.get('usable_area')
            if not usable_area or usable_area.is_empty:
                print("WARNING: No usable area available for placement")
                return {"islands": [], "corridors": [], "stats": {}}
            
            return optimize_layout(usable_area, island_dimensions, corridor_width)
        except Exception as e:
            print(f"ERROR: Layout optimization failed: {e}")
            return {"islands": [], "corridors": [], "stats": {}}
    
    def _create_visualization(self, geometry, layout, output_path):
        """Create professional visualization"""
        print("\n--- CREATING VISUALIZATION ---")
        
        try:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            return visualize_plan(geometry, layout, output_path)
        except Exception as e:
            print(f"ERROR: Visualization failed: {e}")
            return None
    
    def _parse_island_dimensions(self, dims_string):
        """Parse island dimensions string"""
        if not dims_string:
            return [(3, 2), (4, 3), (5, 4), (2, 2)]  # Default sizes
        
        dimensions = []
        try:
            parts = dims_string.split(',')
            for part in parts:
                w, h = part.strip().split('x')
                dimensions.append((float(w), float(h)))
        except (ValueError, IndexError):
            print(f"WARNING: Invalid island dimensions: '{dims_string}'. Using defaults.")
            return [(3, 2), (4, 3), (5, 4), (2, 2)]
        
        return dimensions
    
    def _print_summary(self, geometry, layout):
        """Print processing summary"""
        print("\n=== PROCESSING SUMMARY ===")
        
        # Geometry stats
        if geometry:
            total_area = geometry.get('total_area', 0)
            usable_ratio = geometry.get('usable_area_ratio', 0)
            print(f"Total Area: {total_area:.1f}m²")
            print(f"Usable Area: {usable_ratio*100:.1f}%")
        
        # Layout stats
        stats = layout.get('stats', {})
        if stats:
            print(f"Îlots Placed: {stats.get('islands_placed', 0)}")
            print(f"Coverage: {stats.get('island_coverage', 0)*100:.1f}%")
            print(f"Corridors: {stats.get('corridors_created', 0)}")
            print(f"Corridor Area: {stats.get('corridor_area', 0):.1f}m²")
        
        print("=== PROCESSING COMPLETE ===\n")

# Global instance for backward compatibility
_engine = FloorPlanEngine()

def generate_floorplan(input_path, output_path, islands_str="", corridor_width=1.2,
                      wall_layer="0", prohibited_layer="PROHIBITED", entrance_layer="ENTRANCE"):
    """Main generation function for backward compatibility"""
    return _engine.generate_floorplan(
        input_path, output_path, islands_str, corridor_width,
        wall_layer, prohibited_layer, entrance_layer
    )