#!/usr/bin/env python3
"""
Block Search Tool for BlueMap

This script uses the BlueMap connector to search for blocks on a BlueMap web server
and yields their in-game coordinates.

IMPORTANT LIMITATION:
The PRBM format used by BlueMap contains rendered geometry data (vertices, colors, triangles)
but does not include block type information. This means we can find WHERE blocks are located,
but we cannot identify WHAT TYPE of blocks they are (e.g., oak_log vs stone vs diamond_ore).

For example, if searching for "oak logs":
- We can find all blocks in a given area
- We can filter by height range (trees are typically at surface level, y >= 60)
- We can filter by world position
- But we CANNOT distinguish oak logs from other block types in the PRBM data

The material IDs in PRBM files correspond to textures used for rendering, not block types.
To identify specific block types, you would need access to the original world data files
(e.g., Minecraft region files) rather than the rendered BlueMap tiles.

Usage:
    # Search for all blocks in an area around spawn
    python search.py http://localhost:8100 world --radius 5
    
    # Search with height filter (surface blocks where trees grow)
    python search.py http://localhost:8100 world --radius 3 --min-y 60 --max-y 100
    
    # Search specific tile range
    python search.py http://localhost:8100 world --tile-range "-2,-2" "2,2"
"""

import sys
import argparse
from typing import Generator, Tuple, Optional
from connector import BlueMapConnector


def search_blocks_in_area(
    connector: BlueMapConnector,
    map_id: str,
    min_tile_x: int,
    max_tile_x: int,
    min_tile_z: int,
    max_tile_z: int,
    min_y: Optional[int] = None,
    max_y: Optional[int] = None,
    verbose: bool = False
) -> Generator[Tuple[int, int, int], None, None]:
    """
    Search for blocks in a rectangular tile area and yield their in-game coordinates.
    
    This function downloads and parses PRBM tiles in the specified area, extracting
    block positions from the geometry data. The positions are yielded as they are
    found, allowing for efficient processing of large areas.
    
    Args:
        connector: BlueMapConnector instance
        map_id: Map ID to search (e.g., "world", "world_nether")
        min_tile_x, max_tile_x: X tile coordinate range (inclusive)
        min_tile_z, max_tile_z: Z tile coordinate range (inclusive)
        min_y: Minimum Y coordinate filter (inclusive), None for no limit
        max_y: Maximum Y coordinate filter (inclusive), None for no limit
        verbose: If True, print progress messages
        
    Yields:
        Tuples of (x, y, z) block positions in world coordinates
        
    Note:
        Block positions are yielded as unique coordinates, but duplicates may occur
        if blocks appear in multiple tiles (at tile boundaries). Consider using a
        set to track unique positions if needed.
    """
    tiles_processed = 0
    tiles_skipped = 0
    blocks_yielded = 0
    
    if verbose:
        print(f"Searching for blocks in map '{map_id}'")
        print(f"  Tile range: X[{min_tile_x}, {max_tile_x}], Z[{min_tile_z}, {max_tile_z}]")
        if min_y is not None or max_y is not None:
            y_range = f"Y[{min_y if min_y is not None else '-∞'}, {max_y if max_y is not None else '∞'}]"
            print(f"  Height filter: {y_range}")
        print()
    
    for tile_x in range(min_tile_x, max_tile_x + 1):
        for tile_z in range(min_tile_z, max_tile_z + 1):
            try:
                # Fetch and parse the tile
                result = connector.find_blocks(map_id, tile_x, tile_z)
                blocks = result['block_positions']
                
                tiles_processed += 1
                tile_block_count = 0
                
                # Yield blocks, applying height filter if specified
                for x, y, z in blocks:
                    # Apply height filter
                    if min_y is not None and y < min_y:
                        continue
                    if max_y is not None and y > max_y:
                        continue
                    
                    yield (x, y, z)
                    blocks_yielded += 1
                    tile_block_count += 1
                
                if verbose:
                    print(f"  Tile ({tile_x:3d}, {tile_z:3d}): "
                          f"{tile_block_count:5d} blocks (filtered), "
                          f"{len(blocks):5d} total, "
                          f"{result['num_triangles']:5d} triangles")
                
            except Exception as e:
                tiles_skipped += 1
                if verbose:
                    print(f"  Tile ({tile_x:3d}, {tile_z:3d}): Skipped - {str(e)[:50]}")
    
    if verbose:
        print(f"\nSearch complete:")
        print(f"  Tiles processed: {tiles_processed}")
        print(f"  Tiles skipped: {tiles_skipped}")
        print(f"  Blocks yielded: {blocks_yielded}")


def search_blocks_in_radius(
    connector: BlueMapConnector,
    map_id: str,
    center_x: int,
    center_z: int,
    radius: int,
    min_y: Optional[int] = None,
    max_y: Optional[int] = None,
    verbose: bool = False
) -> Generator[Tuple[int, int, int], None, None]:
    """
    Search for blocks in a square radius around a center point.
    
    Args:
        connector: BlueMapConnector instance
        map_id: Map ID to search
        center_x: Center X tile coordinate
        center_z: Center Z tile coordinate
        radius: Search radius in tiles (creates a square of (2*radius+1)x(2*radius+1) tiles)
        min_y: Minimum Y coordinate filter (inclusive), None for no limit
        max_y: Maximum Y coordinate filter (inclusive), None for no limit
        verbose: If True, print progress messages
        
    Yields:
        Tuples of (x, y, z) block positions in world coordinates
    """
    min_tile_x = center_x - radius
    max_tile_x = center_x + radius
    min_tile_z = center_z - radius
    max_tile_z = center_z + radius
    
    if verbose:
        print(f"Searching radius {radius} around tile ({center_x}, {center_z})")
        print(f"  Total area: {(2*radius+1)*(2*radius+1)} tiles")
        print()
    
    yield from search_blocks_in_area(
        connector, map_id,
        min_tile_x, max_tile_x,
        min_tile_z, max_tile_z,
        min_y, max_y,
        verbose
    )


def export_to_csv(coordinates, filename: str):
    """
    Export block coordinates to a CSV file.
    
    Args:
        coordinates: Iterable of (x, y, z) tuples
        filename: Output filename
    """
    with open(filename, 'w') as f:
        f.write("x,y,z\n")
        count = 0
        for x, y, z in coordinates:
            f.write(f"{x},{y},{z}\n")
            count += 1
    print(f"\nExported {count} coordinates to {filename}")


def main():
    """Main entry point for the search tool."""
    parser = argparse.ArgumentParser(
        description='Search for blocks on a BlueMap server and yield their in-game coordinates.\n\n'
                    'IMPORTANT: This tool cannot identify specific block types (e.g., oak logs)\n'
                    'because PRBM files only contain geometry, not block metadata.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Search 5 tile radius around spawn (0,0)
  python search.py http://localhost:8100 world --radius 5
  
  # Search with height filter (surface level where trees grow)
  python search.py http://localhost:8100 world --radius 3 --min-y 60 --max-y 100
  
  # Search specific tile range
  python search.py http://localhost:8100 world --tile-range "-2,-2" "2,2"
  
  # Export results to CSV
  python search.py http://localhost:8100 world --radius 2 --output blocks.csv
  
  # Search underground (diamond level)
  python search.py http://localhost:8100 world --radius 5 --min-y -64 --max-y 16

Note: To find specific block types like oak logs, you need access to the world
data files, not just the rendered BlueMap tiles. This tool finds block positions
but cannot determine block types from PRBM geometry data.
        '''
    )
    
    parser.add_argument('url', help='BlueMap server URL (e.g., http://localhost:8100)')
    parser.add_argument('map_id', help='Map ID to search (e.g., world, world_nether)')
    
    # Search area options
    area_group = parser.add_mutually_exclusive_group(required=True)
    area_group.add_argument('--radius', type=int, metavar='N',
                           help='Search radius in tiles around center (default center: 0,0)')
    area_group.add_argument('--tile-range', nargs=2, metavar=('MIN', 'MAX'),
                           help='Tile range as "x1,z1" "x2,z2"')
    
    parser.add_argument('--center', default='0,0', metavar='X,Z',
                       help='Center tile coordinates for radius search (default: 0,0)')
    
    # Filters
    parser.add_argument('--min-y', type=int, metavar='Y',
                       help='Minimum Y coordinate (height) filter')
    parser.add_argument('--max-y', type=int, metavar='Y',
                       help='Maximum Y coordinate (height) filter')
    
    # Output options
    parser.add_argument('--output', '-o', metavar='FILE',
                       help='Export coordinates to CSV file')
    parser.add_argument('--limit', type=int, metavar='N',
                       help='Maximum number of coordinates to return')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress progress messages')
    parser.add_argument('--timeout', type=int, default=30, metavar='SECONDS',
                       help='Request timeout in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # Parse center coordinates
    try:
        center_x, center_z = map(int, args.center.split(','))
    except ValueError:
        print("Error: Center must be in format 'x,z' (e.g., '0,0')")
        sys.exit(1)
    
    # Create connector
    verbose = not args.quiet
    connector = BlueMapConnector(args.url, timeout=args.timeout)
    
    # Verify connection
    try:
        if verbose:
            print(f"Connecting to BlueMap at {args.url}...")
        settings = connector.get_settings()
        if verbose:
            print(f"Connected! BlueMap version: {settings.get('version', 'unknown')}")
            print()
    except Exception as e:
        print(f"Error: Could not connect to BlueMap server: {e}")
        sys.exit(1)
    
    # Verify map exists
    try:
        maps = connector.get_maps()
        if args.map_id not in maps:
            print(f"Error: Map '{args.map_id}' not found")
            print(f"Available maps: {', '.join(maps.keys())}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: Could not fetch map list: {e}")
        sys.exit(1)
    
    # Determine search area
    if args.radius is not None:
        search_generator = search_blocks_in_radius(
            connector, args.map_id,
            center_x, center_z, args.radius,
            args.min_y, args.max_y,
            verbose
        )
    else:
        try:
            min_coords = args.tile_range[0].split(',')
            max_coords = args.tile_range[1].split(',')
            min_tile_x, min_tile_z = int(min_coords[0]), int(min_coords[1])
            max_tile_x, max_tile_z = int(max_coords[0]), int(max_coords[1])
        except (ValueError, IndexError):
            print("Error: Tile range must be in format 'x1,z1' 'x2,z2'")
            sys.exit(1)
        
        search_generator = search_blocks_in_area(
            connector, args.map_id,
            min_tile_x, max_tile_x,
            min_tile_z, max_tile_z,
            args.min_y, args.max_y,
            verbose
        )
    
    # Process results
    if args.output:
        # Collect all results and export to CSV
        coordinates = []
        for i, coord in enumerate(search_generator):
            coordinates.append(coord)
            if args.limit and i + 1 >= args.limit:
                break
        
        export_to_csv(coordinates, args.output)
    else:
        # Print coordinates to stdout
        count = 0
        for x, y, z in search_generator:
            print(f"{x},{y},{z}")
            count += 1
            if args.limit and count >= args.limit:
                break
        
        if verbose:
            print(f"\nTotal coordinates printed: {count}", file=sys.stderr)


if __name__ == "__main__":
    main()
