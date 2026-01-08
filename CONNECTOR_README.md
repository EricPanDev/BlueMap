# BlueMap Web API Connector

A Python API connector for interacting with hosted BlueMap instances. This tool allows you to programmatically access BlueMap data through the web API.

## Features

- Connect to any hosted BlueMap instance via URL
- Fetch map settings and metadata
- Request map tiles (both high-res and low-res)
- Search for blocks within chunks/tiles
- Check tile existence without full download
- Fetch multiple tiles in an area

## Installation

No additional dependencies are required beyond Python's standard library and `requests`:

```bash
pip install requests
```

## Quick Start

### Basic Usage

```python
from connector import BlueMapConnector

# Connect to your BlueMap instance
connector = BlueMapConnector("http://localhost:8100")

# Get available maps
maps = connector.get_maps()
print(f"Available maps: {list(maps.keys())}")

# Get map settings
map_settings = connector.get_map_settings("world")
print(f"Map name: {map_settings['name']}")
```

### Searching for Blocks

```python
# Search for tiles in an area (to find where blocks might be)
results = connector.search_block(
    "diamond_ore",
    map_id="world",
    center_x=0,
    center_z=0,
    radius=5
)

print(f"Found {len(results)} tiles in search area")
for x, z in results:
    print(f"  Tile at ({x}, {z})")
```

### Fetching Tiles

```python
# Get a specific tile
tile_data = connector.get_tile(map_id="world", x=0, z=0, lod=0)
print(f"Downloaded tile data: {len(tile_data)} bytes")

# Check if a tile exists
exists = connector.check_tile_exists(map_id="world", x=5, z=10)
print(f"Tile exists: {exists}")

# Get all tiles in an area
tiles = connector.get_tiles_in_area(
    map_id="world",
    min_x=-2, max_x=2,
    min_z=-2, max_z=2,
    lod=0
)
print(f"Downloaded {len(tiles)} tiles")
```

## Command-Line Usage

You can also run the connector directly from the command line:

```bash
python connector.py http://localhost:8100
```

This will:
1. Connect to the specified BlueMap instance
2. Display available maps and their settings
3. Perform an example tile search

## API Reference

### BlueMapConnector

#### `__init__(base_url, timeout=10)`

Initialize the connector.

- `base_url`: The base URL of the BlueMap web interface (e.g., "http://x.x.x.x:8100")
- `timeout`: Request timeout in seconds (default: 10)

#### `get_settings(force_refresh=False)`

Fetch the main settings.json from the BlueMap instance.

Returns: Dictionary containing BlueMap settings

#### `get_maps(force_refresh=False)`

Get information about all available maps.

Returns: Dictionary mapping map IDs to their metadata

#### `get_map_settings(map_id)`

Fetch the settings.json for a specific map.

- `map_id`: The ID of the map

Returns: Dictionary containing map-specific settings

#### `get_tile(map_id, x, z, lod=0)`

Fetch the raw data for a specific tile.

- `map_id`: The ID of the map
- `x`: Tile X coordinate
- `z`: Tile Z coordinate
- `lod`: Level of detail (0 for hires, 1+ for lowres)

Returns: Raw tile data as bytes

#### `check_tile_exists(map_id, x, z, lod=0)`

Check if a tile exists without downloading its full content.

Returns: True if the tile exists, False otherwise

#### `search_block(block_name, map_id, center_x=0, center_z=0, radius=10, lod=0, verbose=True)`

Search for chunks/tiles that may contain a specific block.

- `block_name`: The block name to search for (e.g., "diamond_ore")
- `map_id`: The ID of the map to search
- `center_x`: Center X tile coordinate
- `center_z`: Center Z tile coordinate
- `radius`: Search radius in tiles
- `lod`: Level of detail to use (0 for hires)
- `verbose`: If True, print progress messages (default: True)

Returns: List of (x, z) tile coordinates where tiles exist

**Note**: Since PRBM files are binary geometry data, this method can only determine which chunks exist (have been generated/rendered), not the exact block contents. A complete implementation would need to fully parse the PRBM format to identify specific blocks.

#### `get_tiles_in_area(map_id, min_x, max_x, min_z, max_z, lod=0)`

Fetch all tiles in a rectangular area.

Returns: List of tuples (x, z, tile_data) for each existing tile

## BlueMap Tile Structure

BlueMap organizes tiles using a hierarchical directory structure:

- High-resolution tiles: `maps/{map_id}/tiles/0/x{x_path}z{z_path}.prbm`
- Low-resolution tiles: `maps/{map_id}/tiles/{lod}/x{x_path}z{z_path}.png`

Where coordinates are split per digit:
- `x=123` becomes `x1/2/3/`
- `z=-45` becomes `z-4/5/`

Example: Tile at (123, -45) with LOD 0:
```
maps/world/tiles/0/x1/2/3/z-4/5.prbm
```

## Limitations

- **Block-level search**: The current implementation can only identify which tiles exist, not search within them for specific blocks. This is because PRBM files contain binary 3D geometry data that requires a full parser to extract block information.
  
- **PRBM parsing**: Full parsing of PRBM (BlueMap's proprietary format) would require implementing the complete format specification. The connector provides a basic framework but doesn't include complete geometry parsing.

- **Read-only**: This connector only supports reading data from BlueMap. It cannot modify or upload data.

## Advanced Example

```python
from connector import BlueMapConnector

# Connect
connector = BlueMapConnector("http://example.com:8100", timeout=30)

# Get all maps
maps = connector.get_maps()

# Search each map for tiles
for map_id in maps.keys():
    print(f"\nSearching map: {map_id}")
    
    # Search in a 10x10 tile area around spawn
    tiles = connector.search_block(
        "any_block",  # Placeholder name
        map_id=map_id,
        center_x=0,
        center_z=0,
        radius=5,
        lod=0
    )
    
    # Download the first few tiles
    for i, (x, z) in enumerate(tiles[:3]):
        tile_data = connector.get_tile(map_id, x, z, lod=0)
        print(f"  Tile ({x}, {z}): {len(tile_data)} bytes")
```

## Contributing

Contributions are welcome! Areas for improvement:

1. Complete PRBM parser implementation for full block-level search
2. Caching mechanisms for better performance
3. Async/parallel tile fetching
4. Additional utility functions for common operations
5. Better error handling and retry logic

## License

This connector is provided as part of the BlueMap project and follows the same MIT License.
