#!/usr/bin/env python3
"""
Demonstration of the PRBM parser and find_blocks functionality.

This script creates a synthetic PRBM file and demonstrates:
1. Parsing PRBM files
2. Extracting block positions
3. Converting coordinates
4. Getting in-game coordinates from tiles
"""

import math
from connector import BlueMapConnector
from test_prbm_parser import create_simple_prbm


def demonstrate_full_workflow():
    """Demonstrate the complete workflow from PRBM to block positions."""
    
    print("=" * 70)
    print("PRBM Parser - Complete Workflow Demonstration")
    print("=" * 70)
    
    # Step 1: Create a synthetic PRBM tile
    print("\n1. Creating synthetic PRBM tile...")
    prbm_data = create_simple_prbm()
    print(f"   Created {len(prbm_data)} bytes of PRBM data")
    print(f"   This represents a tile with 1 triangle (3 vertices)")
    
    # Step 2: Parse the PRBM file
    print("\n2. Parsing PRBM file...")
    connector = BlueMapConnector("http://localhost:8100")
    parsed = connector.parse_prbm_tile(prbm_data)
    
    print(f"   ✓ Version: {parsed['version']}")
    print(f"   ✓ Triangles: {parsed['num_triangles']}")
    print(f"   ✓ Vertices: {parsed['num_values']}")
    
    # Step 3: Display vertex positions
    print("\n3. Vertex positions in world coordinates:")
    for i, (x, y, z) in enumerate(parsed['positions']):
        color = parsed['colors'][i]
        print(f"   Vertex {i+1}: ({x:.2f}, {y:.2f}, {z:.2f}) "
              f"RGB({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")
    
    # Step 4: Convert to block positions
    print("\n4. Converting vertices to unique block positions...")
    block_positions = set()
    for x, y, z in parsed['positions']:
        block_x = math.floor(x)
        block_y = math.floor(y)
        block_z = math.floor(z)
        block_positions.add((block_x, block_y, block_z))
    
    print(f"   Found {len(block_positions)} unique block positions:")
    for bx, by, bz in sorted(block_positions):
        print(f"   - Block at ({bx}, {by}, {bz})")
    
    # Step 5: Demonstrate coordinate conversion
    print("\n5. Coordinate conversion examples:")
    
    # Assuming these blocks came from tile (0, 0)
    tile_x, tile_z = 0, 0
    bounds = connector.tile_to_world_coordinates(tile_x, tile_z, grid_size=16)
    print(f"   Tile ({tile_x}, {tile_z}) with grid_size=16")
    print(f"   - World bounds: {bounds[0]} to {bounds[1]}")
    
    # Convert a block position to tile
    for bx, by, bz in list(block_positions)[:1]:
        tile = connector.world_to_tile_coordinates(bx, bz, grid_size=16)
        print(f"   Block at ({bx}, {by}, {bz})")
        print(f"   - Belongs to tile: {tile}")
    
    # Step 6: Demonstrate find_blocks workflow (conceptual)
    print("\n6. Complete find_blocks workflow (conceptual):")
    print("   When connected to a real BlueMap server, you would:")
    print("   ")
    print("   result = connector.find_blocks(")
    print("       map_id='world',")
    print("       tile_x=0,")
    print("       tile_z=0")
    print("   )")
    print("   ")
    print("   This would return:")
    print(f"   - tile_coords: (0, 0)")
    print(f"   - world_bounds: ((0, 0), (15, 15))")
    print(f"   - num_triangles: {parsed['num_triangles']}")
    print(f"   - num_vertices: {parsed['num_values']}")
    print(f"   - block_positions: {sorted(list(block_positions))}")
    print(f"   - vertex_positions: [list of all vertex positions]")
    print(f"   - materials: [material group info]")
    print(f"   - colors: [vertex colors]")
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print("✓ Successfully parsed PRBM format")
    print("✓ Extracted vertex positions and attributes")
    print("✓ Converted vertices to unique block positions")
    print("✓ Demonstrated coordinate conversion")
    print("✓ All block positions are in in-game world coordinates")
    print()
    print("The find_blocks() function automates this entire workflow!")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_full_workflow()
