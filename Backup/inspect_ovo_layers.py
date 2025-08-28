#!/usr/bin/env python3

import ezdxf
from collections import Counter

def inspect_ovo_layers():
    """Inspect layers and entities in the OVO DXF file"""
    
    input_file = r"C:\Users\HP\Desktop\FLOORPLAN_GENIE\input_files\ovo DOSSIER COSTO - plan rdc rdj - cota.dxf"
    
    try:
        print("🔍 INSPECTING OVO DXF FILE STRUCTURE")
        print("=" * 50)
        
        doc = ezdxf.readfile(input_file)
        msp = doc.modelspace()
        
        # Get all layers
        layers = list(doc.layers)
        print(f"📋 LAYERS FOUND ({len(layers)}):")
        for layer in layers:
            print(f"  - {layer.dxf.name}")
        
        # Count entities by layer
        layer_counts = Counter()
        entity_types = Counter()
        
        for entity in msp:
            layer_counts[entity.dxf.layer] += 1
            entity_types[entity.dxftype()] += 1
        
        print(f"\n📊 ENTITIES BY LAYER:")
        for layer, count in layer_counts.most_common():
            print(f"  - {layer}: {count} entities")
        
        print(f"\n🏗️ ENTITY TYPES:")
        for etype, count in entity_types.most_common():
            print(f"  - {etype}: {count}")
        
        # Look for wall-like entities
        print(f"\n🧱 POTENTIAL WALL LAYERS:")
        wall_keywords = ['wall', 'mur', 'cloison', 'partition', 'structure']
        for layer_name in layer_counts.keys():
            if any(keyword in layer_name.lower() for keyword in wall_keywords):
                print(f"  ✓ {layer_name}: {layer_counts[layer_name]} entities")
        
        # Look for door/entrance entities  
        print(f"\n🚪 POTENTIAL DOOR/ENTRANCE LAYERS:")
        door_keywords = ['door', 'porte', 'entrance', 'entree', 'opening']
        for layer_name in layer_counts.keys():
            if any(keyword in layer_name.lower() for keyword in door_keywords):
                print(f"  ✓ {layer_name}: {layer_counts[layer_name]} entities")
                
        return layer_counts, entity_types
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None, None

if __name__ == "__main__":
    inspect_ovo_layers()