#!/usr/bin/env python3
"""
Test script for search.py functionality.

This script tests the search functions using synthetic PRBM data.
"""

import sys
from search import search_blocks_in_area, search_blocks_in_radius, export_to_csv
from connector import BlueMapConnector
from test_prbm_parser import create_simple_prbm
import tempfile
import os


def test_search_functions():
    """Test the search functions with synthetic data."""
    
    print("=" * 70)
    print("Testing search.py Functionality")
    print("=" * 70)
    print()
    
    # Test 1: Verify functions are importable and callable
    print("Test 1: Function imports and signatures")
    print("-" * 70)
    
    assert callable(search_blocks_in_area), "search_blocks_in_area should be callable"
    assert callable(search_blocks_in_radius), "search_blocks_in_radius should be callable"
    assert callable(export_to_csv), "export_to_csv should be callable"
    
    print("✓ All functions are importable and callable")
    print()
    
    # Test 2: Verify PRBM parsing integration
    print("Test 2: PRBM parsing integration")
    print("-" * 70)
    
    connector = BlueMapConnector("http://test.invalid:8100", timeout=1)
    prbm_data = create_simple_prbm()
    parsed = connector.parse_prbm_tile(prbm_data)
    
    assert 'positions' in parsed, "Parsed data should contain positions"
    assert len(parsed['positions']) == 3, "Should have 3 vertex positions"
    
    print(f"✓ PRBM parsing works: {len(parsed['positions'])} vertices")
    print()
    
    # Test 3: Verify coordinate conversion
    print("Test 3: Coordinate conversion")
    print("-" * 70)
    
    # Test tile to world coordinates
    bounds = connector.tile_to_world_coordinates(0, 0, grid_size=16)
    assert bounds == ((0, 0), (15, 15)), f"Tile (0,0) should map to bounds ((0,0), (15,15)), got {bounds}"
    
    bounds = connector.tile_to_world_coordinates(1, 1, grid_size=16)
    assert bounds == ((16, 16), (31, 31)), f"Tile (1,1) should map to bounds ((16,16), (31,31)), got {bounds}"
    
    # Test world to tile coordinates
    tile = connector.world_to_tile_coordinates(0, 0, grid_size=16)
    assert tile == (0, 0), f"World (0,0) should map to tile (0,0), got {tile}"
    
    tile = connector.world_to_tile_coordinates(20, 25, grid_size=16)
    assert tile == (1, 1), f"World (20,25) should map to tile (1,1), got {tile}"
    
    tile = connector.world_to_tile_coordinates(-5, -10, grid_size=16)
    assert tile == (-1, -1), f"World (-5,-10) should map to tile (-1,-1), got {tile}"
    
    print("✓ Coordinate conversion works correctly")
    print()
    
    # Test 4: Verify CSV export
    print("Test 4: CSV export functionality")
    print("-" * 70)
    
    # Use mkstemp for clearer intent when manual cleanup is required
    import tempfile
    fd, temp_csv = tempfile.mkstemp(suffix='.csv', text=True)
    os.close(fd)  # Close the file descriptor, we'll open it normally
    
    try:
        # Test data
        test_coords = [
            (10, 64, 20),
            (11, 65, 21),
            (12, 66, 22)
        ]
        
        export_to_csv(test_coords, temp_csv)
        
        # Verify file was created and has correct content
        assert os.path.exists(temp_csv), "CSV file should be created"
        
        with open(temp_csv, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 4, f"Should have 4 lines (header + 3 data), got {len(lines)}"
        assert lines[0].strip() == "x,y,z", "First line should be header"
        assert lines[1].strip() == "10,64,20", "Second line should be first coordinate"
        assert lines[2].strip() == "11,65,21", "Third line should be second coordinate"
        assert lines[3].strip() == "12,66,22", "Fourth line should be third coordinate"
        
        print(f"✓ CSV export works correctly")
        print(f"  Created file with {len(lines)} lines")
        print(f"  Sample: {lines[1].strip()}")
    
    finally:
        # Clean up
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
    
    print()
    
    # Test 5: Verify generator behavior
    print("Test 5: Generator behavior")
    print("-" * 70)
    
    # Verify that search functions return generators
    # (We can't actually test with real data without a server)
    import types
    
    # Note: We can't actually call these without a real server connection
    # But we can verify they're generator functions
    from inspect import isgeneratorfunction
    
    assert isgeneratorfunction(search_blocks_in_area), "search_blocks_in_area should be a generator"
    assert isgeneratorfunction(search_blocks_in_radius), "search_blocks_in_radius should be a generator"
    
    print("✓ Search functions are generators (will yield coordinates)")
    print()
    
    # Summary
    print("=" * 70)
    print("All Tests Passed!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  ✓ Functions are properly defined and importable")
    print("  ✓ PRBM parsing integration works")
    print("  ✓ Coordinate conversion is accurate")
    print("  ✓ CSV export creates valid files")
    print("  ✓ Generator functions are properly defined")
    print()
    print("Note: Full integration testing requires a running BlueMap server.")
    print("=" * 70)


def test_height_filtering():
    """Test height filtering logic."""
    
    print()
    print("Test 6: Height filtering logic")
    print("-" * 70)
    
    # Simulate height filtering
    test_blocks = [
        (0, -64, 0),   # Bedrock level
        (0, 0, 0),     # Ground level
        (0, 64, 0),    # Surface
        (0, 100, 0),   # Above surface
        (0, 256, 0),   # Build height
    ]
    
    # Filter min_y=60, max_y=100
    filtered = []
    for x, y, z in test_blocks:
        if 60 <= y <= 100:
            filtered.append((x, y, z))
    
    assert len(filtered) == 2, f"Should filter to 2 blocks, got {len(filtered)}"
    assert (0, 64, 0) in filtered, "Should include y=64"
    assert (0, 100, 0) in filtered, "Should include y=100"
    assert (0, -64, 0) not in filtered, "Should exclude y=-64"
    
    print("✓ Height filtering logic works correctly")
    print(f"  Input: {len(test_blocks)} blocks")
    print(f"  Filtered (60 <= y <= 100): {len(filtered)} blocks")
    print()


if __name__ == "__main__":
    try:
        test_search_functions()
        test_height_filtering()
        
        print("\n" + "=" * 70)
        print("SUCCESS: All tests completed successfully!")
        print("=" * 70)
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
