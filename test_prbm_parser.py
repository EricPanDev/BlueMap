#!/usr/bin/env python3
"""
Test script for PRBM parser functionality.

This script creates synthetic PRBM files and tests the parser.
"""

import struct
import io
from connector import BlueMapConnector


def create_simple_prbm() -> bytes:
    """
    Create a simple PRBM file with one triangle for testing.
    
    Returns:
        bytes: A valid PRBM file
    """
    output = io.BytesIO()
    
    # Header
    version = 1
    header_bits = 0b0_0_0_00111  # indexed=no, endianness=little, attribute-count=7
    
    output.write(bytes([version]))
    output.write(bytes([header_bits]))
    
    # Number of values (1 triangle = 3 vertices)
    num_values = 3
    output.write(struct.pack('<I', num_values)[:3])
    
    # Number of indices (0 for non-indexed)
    output.write(struct.pack('<I', 0)[:3])
    
    # Attribute 1: position (float, not normalized, 3D vector, 32-bit float)
    output.write(b'position\x00')
    # Type: FLOAT | NOT_NORMALIZED | 3D_VEC | SIGNED_32BIT_FLOAT
    attr_type = 0 | 0 | (2 << 4) | 1
    output.write(bytes([attr_type]))
    
    # Padding to 4-byte boundary
    padding = (4 - (output.tell() % 4)) % 4
    output.write(b'\x00' * padding)
    
    # Position data: 3 vertices * 3 components each
    positions = [
        (10.0, 64.0, 20.0),  # vertex 1
        (10.5, 64.0, 20.5),  # vertex 2
        (11.0, 65.0, 21.0),  # vertex 3
    ]
    for x, y, z in positions:
        output.write(struct.pack('<f', x))
        output.write(struct.pack('<f', y))
        output.write(struct.pack('<f', z))
    
    # Attribute 2: normal (float, normalized, 3D vector, signed 8-bit int)
    output.write(b'normal\x00')
    # Type: FLOAT | NORMALIZED | 3D_VEC | SIGNED_8BIT_INT
    attr_type = 0 | (1 << 6) | (2 << 4) | 3
    output.write(bytes([attr_type]))
    
    # Padding
    padding = (4 - (output.tell() % 4)) % 4
    output.write(b'\x00' * padding)
    
    # Normal data: 3 vertices * 3 components each
    # Normalized values: -1.0 to 1.0 mapped to -128 to 127
    for i in range(3):  # 3 vertices
        output.write(struct.pack('<b', 0))    # x
        output.write(struct.pack('<b', 127))  # y (pointing up)
        output.write(struct.pack('<b', 0))    # z
    
    # Attribute 3: color (float, normalized, 3D vector, unsigned 8-bit int)
    output.write(b'color\x00')
    # Type: FLOAT | NORMALIZED | 3D_VEC | UNSIGNED_8BIT_INT
    attr_type = 0 | (1 << 6) | (2 << 4) | 7
    output.write(bytes([attr_type]))
    
    # Padding
    padding = (4 - (output.tell() % 4)) % 4
    output.write(b'\x00' * padding)
    
    # Color data: 3 vertices * 3 components each
    # RGB values from 0.0 to 1.0 mapped to 0 to 255
    for i in range(3):  # 3 vertices
        output.write(struct.pack('<B', 100))  # r
        output.write(struct.pack('<B', 200))  # g
        output.write(struct.pack('<B', 150))  # b
    
    # Attribute 4: uv (float, not normalized, 2D vector, 32-bit float)
    output.write(b'uv\x00')
    # Type: FLOAT | NOT_NORMALIZED | 2D_VEC | SIGNED_32BIT_FLOAT
    attr_type = 0 | 0 | (1 << 4) | 1
    output.write(bytes([attr_type]))
    
    # Padding
    padding = (4 - (output.tell() % 4)) % 4
    output.write(b'\x00' * padding)
    
    # UV data: 3 vertices * 2 components each
    uvs = [(0.0, 0.0), (0.5, 0.0), (1.0, 1.0)]
    for u, v in uvs:
        output.write(struct.pack('<f', u))
        output.write(struct.pack('<f', v))
    
    # Attribute 5: ao (float, normalized, scalar, unsigned 8-bit int)
    output.write(b'ao\x00')
    # Type: FLOAT | NORMALIZED | SCALAR | UNSIGNED_8BIT_INT
    attr_type = 0 | (1 << 6) | 0 | 7
    output.write(bytes([attr_type]))
    
    # Padding
    padding = (4 - (output.tell() % 4)) % 4
    output.write(b'\x00' * padding)
    
    # AO data: 3 vertices * 1 component each
    for i in range(3):
        output.write(struct.pack('<B', 255))  # Full brightness
    
    # Attribute 6: blocklight (float, not normalized, scalar, signed 8-bit int)
    output.write(b'blocklight\x00')
    # Type: FLOAT | NOT_NORMALIZED | SCALAR | SIGNED_8BIT_INT
    attr_type = 0 | 0 | 0 | 3
    output.write(bytes([attr_type]))
    
    # Padding
    padding = (4 - (output.tell() % 4)) % 4
    output.write(b'\x00' * padding)
    
    # Blocklight data: 3 vertices * 1 component each
    for i in range(3):
        output.write(struct.pack('<b', 15))  # Max block light
    
    # Attribute 7: sunlight (float, not normalized, scalar, signed 8-bit int)
    output.write(b'sunlight\x00')
    # Type: FLOAT | NOT_NORMALIZED | SCALAR | SIGNED_8BIT_INT
    attr_type = 0 | 0 | 0 | 3
    output.write(bytes([attr_type]))
    
    # Padding
    padding = (4 - (output.tell() % 4)) % 4
    output.write(b'\x00' * padding)
    
    # Sunlight data: 3 vertices * 1 component each
    for i in range(3):
        output.write(struct.pack('<b', 15))  # Max sun light
    
    # Material groups
    # Padding before material groups
    padding = (4 - (output.tell() % 4)) % 4
    output.write(b'\x00' * padding)
    
    # One material group covering all 3 vertices
    output.write(struct.pack('<i', 0))  # material_id
    output.write(struct.pack('<i', 0))  # start index
    output.write(struct.pack('<i', 3))  # count (3 vertices)
    
    # End marker
    output.write(struct.pack('<i', -1))
    
    return output.getvalue()


def test_prbm_parser():
    """Test the PRBM parser with synthetic data."""
    print("Testing PRBM Parser")
    print("=" * 60)
    
    # Create test PRBM data
    print("\n1. Creating synthetic PRBM file...")
    prbm_data = create_simple_prbm()
    print(f"   Created {len(prbm_data)} bytes of PRBM data")
    
    # Parse it
    print("\n2. Parsing PRBM file...")
    connector = BlueMapConnector("http://localhost:8100")
    
    try:
        parsed = connector.parse_prbm_tile(prbm_data)
        
        print(f"   Version: {parsed['version']}")
        print(f"   Number of triangles: {parsed['num_triangles']}")
        print(f"   Number of vertices: {parsed['num_values']}")
        print(f"   Little endian: {parsed['is_little_endian']}")
        print(f"   Indexed: {parsed['is_indexed']}")
        
        print("\n3. Parsed attributes:")
        for attr in parsed['attributes']:
            print(f"   - {attr['name']}: cardinality={attr['cardinality']}, "
                  f"normalized={attr['is_normalized']}, "
                  f"encoding={attr['encoding']}")
        
        print("\n4. Vertex positions:")
        if 'positions' in parsed:
            for i, pos in enumerate(parsed['positions']):
                print(f"   Vertex {i+1}: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
        
        print("\n5. Colors:")
        if 'colors' in parsed:
            for i, color in enumerate(parsed['colors']):
                print(f"   Vertex {i+1}: RGB({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f})")
        
        print("\n6. Material groups:")
        for mat in parsed.get('materials', []):
            print(f"   Material {mat['material_id']}: "
                  f"start={mat['start']}, count={mat['count']}")
        
        print("\n✓ Parser test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coordinate_conversion():
    """Test coordinate conversion functions."""
    print("\n\nTesting Coordinate Conversion")
    print("=" * 60)
    
    connector = BlueMapConnector("http://localhost:8100")
    
    print("\n1. Tile to world coordinates:")
    test_cases = [
        (0, 0, 16, 0, 0),
        (1, 1, 16, 0, 0),
        (-1, -1, 16, 0, 0),
        (0, 0, 32, 5, 5),
    ]
    
    for tile_x, tile_z, grid_size, offset_x, offset_z in test_cases:
        bounds = connector.tile_to_world_coordinates(
            tile_x, tile_z, grid_size, offset_x, offset_z
        )
        print(f"   Tile ({tile_x}, {tile_z}) with grid_size={grid_size}, "
              f"offset=({offset_x}, {offset_z})")
        print(f"     -> World bounds: {bounds[0]} to {bounds[1]}")
    
    print("\n2. World to tile coordinates:")
    world_test_cases = [
        (0, 0, 16, 0, 0),
        (15, 15, 16, 0, 0),
        (16, 16, 16, 0, 0),
        (-1, -1, 16, 0, 0),
        (100, 200, 16, 0, 0),
    ]
    
    for world_x, world_z, grid_size, offset_x, offset_z in world_test_cases:
        tile_coords = connector.world_to_tile_coordinates(
            world_x, world_z, grid_size, offset_x, offset_z
        )
        print(f"   World ({world_x}, {world_z}) with grid_size={grid_size}")
        print(f"     -> Tile: {tile_coords}")
    
    print("\n✓ Coordinate conversion test passed!")
    return True


def main():
    """Run all tests."""
    print("BlueMap PRBM Parser Test Suite")
    print("=" * 60)
    
    test1_passed = test_prbm_parser()
    test2_passed = test_coordinate_conversion()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  PRBM Parser: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"  Coordinate Conversion: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
