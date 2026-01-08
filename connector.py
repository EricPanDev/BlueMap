#!/usr/bin/env python3
"""
BlueMap Web API Connector

This module provides a Python API to interact with a hosted BlueMap web interface.
It allows you to:
- Fetch map settings and metadata
- Request and parse map tiles
- Parse PRBM (high-resolution tile) files
- Find blocks within tiles and get their in-game coordinates
- Convert between tile and world coordinates

Usage:
    from connector import BlueMapConnector
    
    # Connect to a BlueMap instance
    connector = BlueMapConnector("http://localhost:8100")
    
    # Get available maps
    maps = connector.get_maps()
    print(f"Available maps: {list(maps.keys())}")
    
    # Find blocks in a tile and get in-game coordinates
    result = connector.find_blocks("world", tile_x=0, tile_z=0)
    print(f"Found {len(result['block_positions'])} unique blocks")
    for x, y, z in result['block_positions'][:5]:
        print(f"  Block at ({x}, {y}, {z})")
"""

import requests
import struct
import math
from typing import Dict, List, Tuple, Optional, Any, Set
from urllib.parse import urljoin


class BlueMapConnector:
    """
    A connector class to interact with the BlueMap web API.
    
    This class provides methods to fetch map data, tiles, and search for blocks
    using only the endpoints available on the BlueMap web interface.
    """
    
    def __init__(self, base_url: str, timeout: int = 10):
        """
        Initialize the BlueMap connector.
        
        Args:
            base_url: The base URL of the BlueMap web interface (e.g., "http://x.x.x.x:8100")
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._settings_cache = None
        self._maps_cache = None
        
    def _get(self, path: str) -> requests.Response:
        """
        Perform a GET request to the BlueMap API.
        
        Args:
            path: The API path (relative to base_url)
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If the request fails
        """
        url = urljoin(self.base_url + '/', path.lstrip('/'))
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response
    
    def get_settings(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch the main settings.json from the BlueMap instance.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dictionary containing BlueMap settings
        """
        if self._settings_cache is None or force_refresh:
            response = self._get('settings.json')
            self._settings_cache = response.json()
        return self._settings_cache
    
    def get_maps(self, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available maps.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dictionary mapping map IDs to their metadata
        """
        if self._maps_cache is None or force_refresh:
            settings = self.get_settings(force_refresh)
            maps = {}
            
            for map_id in settings.get('maps', []):
                try:
                    map_settings = self.get_map_settings(map_id)
                    maps[map_id] = map_settings
                except (requests.RequestException, KeyError) as e:
                    # Skip maps that can't be loaded (they may not exist or be misconfigured)
                    pass
                    
            self._maps_cache = maps
        return self._maps_cache
    
    def get_map_settings(self, map_id: str) -> Dict[str, Any]:
        """
        Fetch the settings.json for a specific map.
        
        Args:
            map_id: The ID of the map
            
        Returns:
            Dictionary containing map-specific settings
        """
        settings = self.get_settings()
        map_data_root = settings.get('mapDataRoot', 'maps')
        path = f"{map_data_root}/{map_id}/settings.json"
        response = self._get(path)
        return response.json()
    
    @staticmethod
    def _path_from_coords(x: int, z: int) -> str:
        """
        Convert tile coordinates to BlueMap's path format.
        
        BlueMap uses a directory structure where each digit of the coordinate
        is a separate directory level. Negative numbers are prefixed with '-'.
        
        Example: x=123, z=-45 becomes "x1/2/3/z-4/5"
        
        Args:
            x: X coordinate
            z: Z coordinate
            
        Returns:
            Path string for the tile
        """
        def split_number(num: int) -> str:
            """Split a number into path components."""
            path = ''
            if num < 0:
                path = '-'
                num = -num
            path += '/'.join(str(num))
            return path
        
        path = f"x{split_number(x)}/z{split_number(z)}"
        return path
    
    def get_tile_url(self, map_id: str, x: int, z: int, lod: int = 0) -> str:
        """
        Construct the URL for a specific tile.
        
        Args:
            map_id: The ID of the map
            x: Tile X coordinate
            z: Tile Z coordinate
            lod: Level of detail (0 for hires, 1+ for lowres)
            
        Returns:
            Full URL to the tile
        """
        settings = self.get_settings()
        map_data_root = settings.get('mapDataRoot', 'maps')
        
        path = self._path_from_coords(x, z)
        
        if lod == 0:
            # High-resolution tiles (.prbm format)
            tile_path = f"{map_data_root}/{map_id}/tiles/0/{path}.prbm"
        else:
            # Low-resolution tiles (.png format)
            tile_path = f"{map_data_root}/{map_id}/tiles/{lod}/{path}.png"
            
        return urljoin(self.base_url + '/', tile_path)
    
    def get_tile(self, map_id: str, x: int, z: int, lod: int = 0) -> bytes:
        """
        Fetch the raw data for a specific tile.
        
        Args:
            map_id: The ID of the map
            x: Tile X coordinate
            z: Tile Z coordinate
            lod: Level of detail (0 for hires, 1+ for lowres)
            
        Returns:
            Raw tile data as bytes
            
        Raises:
            requests.RequestException: If the tile cannot be fetched
        """
        settings = self.get_settings()
        map_data_root = settings.get('mapDataRoot', 'maps')
        
        path = self._path_from_coords(x, z)
        
        if lod == 0:
            tile_path = f"{map_data_root}/{map_id}/tiles/0/{path}.prbm"
        else:
            tile_path = f"{map_data_root}/{map_id}/tiles/{lod}/{path}.png"
            
        response = self._get(tile_path)
        return response.content
    
    def parse_prbm_tile(self, data: bytes) -> Dict[str, Any]:
        """
        Parse a PRBM (BlueMap high-res tile) file.
        
        This parser implements the PRBM format specification to extract
        geometry data including vertex positions, colors, lighting, etc.
        
        Args:
            data: Raw PRBM file data
            
        Returns:
            Dictionary with parsed tile information including:
            - version: Format version
            - num_triangles: Number of triangles
            - positions: List of (x, y, z) vertex positions
            - colors: List of (r, g, b) colors per vertex
            - materials: Material group information
            - Other attributes (uvs, ao, lighting, normals)
            
        Raises:
            ValueError: If the PRBM file is invalid or corrupted
        """
        if len(data) < 12:
            raise ValueError("Invalid PRBM file: too short")
        
        offset = 0
        
        # Read header (2 bytes)
        version = data[offset]
        offset += 1
        
        header_bits = data[offset]
        offset += 1
        
        # Parse header bits
        attribute_count = header_bits & 0b00111
        is_little_endian = not bool((header_bits >> 3) & 0b1)
        is_indexed = bool((header_bits >> 5) & 0b1)
        
        if version != 1:
            raise ValueError(f"Unsupported PRBM version: {version}")
        
        if not is_little_endian:
            raise ValueError("Big endian PRBM files not supported")
        
        # Read number of values (3 bytes, little endian)
        num_values = struct.unpack('<I', data[offset:offset+3] + b'\x00')[0]
        offset += 3
        
        # Read number of indices (3 bytes, little endian)
        num_indices = struct.unpack('<I', data[offset:offset+3] + b'\x00')[0]
        offset += 3
        
        if is_indexed and num_indices > 0:
            raise ValueError("Indexed PRBM files not yet supported")
        
        num_triangles = num_values // 3
        
        result = {
            'version': version,
            'num_triangles': num_triangles,
            'num_values': num_values,
            'is_little_endian': is_little_endian,
            'is_indexed': is_indexed,
            'attribute_count': attribute_count,
        }
        
        # Parse attributes based on the count in the header
        # BlueMap typically has 7 attributes, but we parse based on what the file says
        attributes = []
        for i in range(attribute_count):
            # Read attribute name (null-terminated string)
            name_end = data.find(b'\x00', offset)
            if name_end == -1:
                raise ValueError(f"Invalid attribute name at offset {offset}")
            
            attr_name = data[offset:name_end].decode('ascii')
            offset = name_end + 1
            
            # Read attribute type byte
            attr_type = data[offset]
            offset += 1
            
            # Parse attribute type
            is_float = not bool(attr_type & 0x80)
            is_normalized = bool(attr_type & 0x40)
            cardinality_bits = (attr_type >> 4) & 0x3
            # Cardinality: 0=scalar(1), 1=2D(2), 2=3D(3), 3=4D(4)
            cardinality = cardinality_bits + 1 if cardinality_bits > 0 else 1
            
            encoding = attr_type & 0x0F
            
            # Determine byte size per component
            if encoding == 1:  # SIGNED_32BIT_FLOAT
                component_size = 4
                component_type = 'f'
            elif encoding == 3:  # SIGNED_8BIT_INT
                component_size = 1
                component_type = 'b'
            elif encoding == 4:  # SIGNED_16BIT_INT
                component_size = 2
                component_type = 'h'
            elif encoding == 6:  # SIGNED_32BIT_INT
                component_size = 4
                component_type = 'i'
            elif encoding == 7:  # UNSIGNED_8BIT_INT
                component_size = 1
                component_type = 'B'
            elif encoding == 8:  # UNSIGNED_16BIT_INT
                component_size = 2
                component_type = 'H'
            elif encoding == 10:  # UNSIGNED_32BIT_INT
                component_size = 4
                component_type = 'I'
            else:
                raise ValueError(f"Unknown encoding: {encoding}")
            
            attributes.append({
                'name': attr_name,
                'is_float': is_float,
                'is_normalized': is_normalized,
                'cardinality': cardinality,
                'encoding': encoding,
                'component_size': component_size,
                'component_type': component_type
            })
            
            # Padding to 4-byte boundary
            padding = (4 - (offset % 4)) % 4
            offset += padding
            
            # Read attribute data
            values_per_vertex = cardinality
            total_values = num_values * values_per_vertex
            total_bytes = total_values * component_size
            
            # Bounds check before reading attribute data
            if offset + total_bytes > len(data):
                raise ValueError(f"Insufficient data for attribute '{attr_name}': "
                               f"need {total_bytes} bytes at offset {offset}, "
                               f"but only {len(data) - offset} bytes available")
            
            attr_data = []
            for j in range(total_values):
                val_offset = offset + j * component_size
                
                # Additional bounds check (redundant but explicit for safety)
                if val_offset + component_size > len(data):
                    raise ValueError(f"Buffer overrun reading attribute '{attr_name}' "
                                   f"at value {j}/{total_values}")
                
                # Unpack value based on type
                if component_type == 'f':
                    val = struct.unpack('<f', data[val_offset:val_offset+4])[0]
                elif component_type == 'b':
                    val = struct.unpack('<b', data[val_offset:val_offset+1])[0]
                    if is_normalized:
                        # Normalize signed byte: -128..127 -> -1.0..1.0
                        val = max(val / 127.0, -1.0)
                elif component_type == 'h':
                    val = struct.unpack('<h', data[val_offset:val_offset+2])[0]
                elif component_type == 'i':
                    val = struct.unpack('<i', data[val_offset:val_offset+4])[0]
                elif component_type == 'B':
                    val = struct.unpack('<B', data[val_offset:val_offset+1])[0]
                    if is_normalized:
                        val = val / 255.0
                elif component_type == 'H':
                    val = struct.unpack('<H', data[val_offset:val_offset+2])[0]
                elif component_type == 'I':
                    val = struct.unpack('<I', data[val_offset:val_offset+4])[0]
                else:
                    val = 0
                
                attr_data.append(val)
            
            offset += total_bytes
            
            # Store the parsed attribute data
            result[attr_name] = attr_data
        
        # Parse material groups
        # Padding to 4-byte boundary before material groups
        padding = (4 - (offset % 4)) % 4
        offset += padding
        
        materials = []
        while offset + 4 <= len(data):
            # Bounds check for material_id
            if offset + 4 > len(data):
                break
                
            material_id = struct.unpack('<i', data[offset:offset+4])[0]
            offset += 4
            
            if material_id == -1:
                break
            
            # Bounds check for start_idx and count
            if offset + 8 > len(data):
                raise ValueError(f"Insufficient data for material group: "
                               f"need 8 bytes at offset {offset}, "
                               f"but only {len(data) - offset} bytes available")
            
            start_idx = struct.unpack('<i', data[offset:offset+4])[0]
            offset += 4
            
            count = struct.unpack('<i', data[offset:offset+4])[0]
            offset += 4
            
            materials.append({
                'material_id': material_id,
                'start': start_idx,
                'count': count
            })
        
        result['materials'] = materials
        result['attributes'] = attributes
        
        # Extract positions as list of tuples for easier use
        if 'position' in result:
            pos_data = result['position']
            positions = []
            for i in range(0, len(pos_data), 3):
                positions.append((pos_data[i], pos_data[i+1], pos_data[i+2]))
            result['positions'] = positions
        
        # Extract colors as list of tuples
        if 'color' in result:
            color_data = result['color']
            colors = []
            for i in range(0, len(color_data), 3):
                colors.append((color_data[i], color_data[i+1], color_data[i+2]))
            result['colors'] = colors
        
        return result
    
    def check_tile_exists(self, map_id: str, x: int, z: int, lod: int = 0) -> bool:
        """
        Check if a tile exists without downloading its full content.
        
        Args:
            map_id: The ID of the map
            x: Tile X coordinate
            z: Tile Z coordinate
            lod: Level of detail (0 for hires, 1+ for lowres)
            
        Returns:
            True if the tile exists, False otherwise
        """
        try:
            settings = self.get_settings()
            map_data_root = settings.get('mapDataRoot', 'maps')
            path = self._path_from_coords(x, z)
            
            if lod == 0:
                tile_path = f"{map_data_root}/{map_id}/tiles/0/{path}.prbm"
            else:
                tile_path = f"{map_data_root}/{map_id}/tiles/{lod}/{path}.png"
                
            # If _get succeeds, the tile exists
            self._get(tile_path)
            return True
        except requests.RequestException:
            return False
    
    def search_block(
        self,
        block_name: str,
        map_id: str,
        center_x: int = 0,
        center_z: int = 0,
        radius: int = 10,
        lod: int = 0,
        verbose: bool = True
    ) -> List[Tuple[int, int]]:
        """
        Search for chunks/tiles that may contain a specific block.
        
        This method downloads tiles in a radius around a center point and checks
        if they exist (indicating that chunk has been generated/rendered).
        
        Note: Since PRBM files are binary geometry data, we can only determine
        which chunks exist, not the exact block contents without a full PRBM parser.
        A complete implementation would need to parse the geometry and check
        block types, which is beyond the scope of the web API.
        
        Args:
            block_name: The block name to search for (e.g., "diamond_ore")
            map_id: The ID of the map to search
            center_x: Center X tile coordinate
            center_z: Center Z tile coordinate
            radius: Search radius in tiles
            lod: Level of detail to use (0 for hires)
            verbose: If True, print progress messages (default: True)
            
        Returns:
            List of (x, z) tile coordinates where tiles exist
        """
        found_tiles = []
        
        if verbose:
            print(f"Searching for block '{block_name}' in map '{map_id}'")
            print(f"Center: ({center_x}, {center_z}), Radius: {radius} tiles")
            print("Note: This searches for existing tiles. Full block-level search")
            print("      requires parsing PRBM geometry data.")
        
        for x in range(center_x - radius, center_x + radius + 1):
            for z in range(center_z - radius, center_z + radius + 1):
                try:
                    if self.check_tile_exists(map_id, x, z, lod):
                        found_tiles.append((x, z))
                        if verbose:
                            print(f"  Found tile at ({x}, {z})")
                except requests.RequestException:
                    # Tile doesn't exist or couldn't be checked, skip it
                    pass
        
        if verbose:
            print(f"\nFound {len(found_tiles)} existing tiles in search area")
        return found_tiles
    
    def get_tiles_in_area(
        self,
        map_id: str,
        min_x: int,
        max_x: int,
        min_z: int,
        max_z: int,
        lod: int = 0
    ) -> List[Tuple[int, int, bytes]]:
        """
        Fetch all tiles in a rectangular area.
        
        Args:
            map_id: The ID of the map
            min_x: Minimum X tile coordinate
            max_x: Maximum X tile coordinate
            min_z: Minimum Z tile coordinate
            max_z: Maximum Z tile coordinate
            lod: Level of detail (0 for hires, 1+ for lowres)
            
        Returns:
            List of tuples (x, z, tile_data) for each existing tile
        """
        tiles = []
        
        for x in range(min_x, max_x + 1):
            for z in range(min_z, max_z + 1):
                try:
                    tile_data = self.get_tile(map_id, x, z, lod)
                    tiles.append((x, z, tile_data))
                except requests.RequestException:
                    # Tile doesn't exist, skip it
                    pass
        
        return tiles
    
    def tile_to_world_coordinates(
        self, 
        tile_x: int, 
        tile_z: int, 
        grid_size: int = 16, 
        offset_x: int = 0, 
        offset_z: int = 0
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Convert tile coordinates to world coordinate ranges.
        
        Based on BlueMap's Grid system, each tile covers a rectangular area
        in the world. This function returns the min and max world coordinates
        for a given tile.
        
        Args:
            tile_x: Tile X coordinate
            tile_z: Tile Z coordinate
            grid_size: Size of each tile in blocks (default: 16)
            offset_x: Grid offset in X direction (default: 0)
            offset_z: Grid offset in Z direction (default: 0)
            
        Returns:
            Tuple of ((min_x, min_z), (max_x, max_z)) world coordinates
        """
        min_x = tile_x * grid_size + offset_x
        min_z = tile_z * grid_size + offset_z
        max_x = (tile_x + 1) * grid_size + offset_x - 1
        max_z = (tile_z + 1) * grid_size + offset_z - 1
        
        return ((min_x, min_z), (max_x, max_z))
    
    def world_to_tile_coordinates(
        self,
        world_x: int,
        world_z: int,
        grid_size: int = 16,
        offset_x: int = 0,
        offset_z: int = 0
    ) -> Tuple[int, int]:
        """
        Convert world coordinates to tile coordinates.
        
        Args:
            world_x: World X coordinate
            world_z: World Z coordinate
            grid_size: Size of each tile in blocks (default: 16)
            offset_x: Grid offset in X direction (default: 0)
            offset_z: Grid offset in Z direction (default: 0)
            
        Returns:
            Tuple of (tile_x, tile_z) coordinates
        """
        tile_x = (world_x - offset_x) // grid_size
        tile_z = (world_z - offset_z) // grid_size
        
        return (tile_x, tile_z)
    
    def find_blocks(
        self,
        map_id: str,
        tile_x: int,
        tile_z: int,
        grid_size: int = 16,
        offset_x: int = 0,
        offset_z: int = 0,
        lod: int = 0
    ) -> Dict[str, Any]:
        """
        Find and return block positions from a PRBM tile in in-game coordinates.
        
        This function downloads a tile, parses it, and returns the unique block
        positions found in the tile geometry, converted to in-game world coordinates.
        
        Args:
            map_id: The ID of the map
            tile_x: Tile X coordinate
            tile_z: Tile Z coordinate
            grid_size: Size of each tile in blocks (default: 16)
            offset_x: Grid offset in X direction (default: 0)
            offset_z: Grid offset in Z direction (default: 0)
            lod: Level of detail (must be 0 for PRBM tiles)
            
        Returns:
            Dictionary containing:
            - tile_coords: (tile_x, tile_z) coordinates
            - world_bounds: ((min_x, min_z), (max_x, max_z)) world coordinate bounds
            - num_triangles: Number of triangles in the tile
            - num_vertices: Number of vertices
            - block_positions: List of unique (x, y, z) block positions in world coordinates (sorted)
            - vertex_positions: List of all (x, y, z) vertex positions in world coordinates
            
        Raises:
            ValueError: If lod is not 0 (only high-res tiles are PRBM format)
            requests.RequestException: If the tile cannot be fetched
        """
        if lod != 0:
            raise ValueError("find_blocks only works with high-resolution tiles (lod=0)")
        
        # Get tile data
        tile_data = self.get_tile(map_id, tile_x, tile_z, lod=0)
        
        # Parse PRBM file
        parsed = self.parse_prbm_tile(tile_data)
        
        # Get world coordinate bounds for this tile
        world_bounds = self.tile_to_world_coordinates(tile_x, tile_z, grid_size, offset_x, offset_z)
        
        # Convert vertex positions to world coordinates
        # Positions in PRBM are relative to the tile origin
        vertex_positions = []
        block_positions: Set[Tuple[int, int, int]] = set()
        
        if 'positions' in parsed:
            for pos in parsed['positions']:
                # PRBM positions are in world coordinates already
                world_x, world_y, world_z = pos
                vertex_positions.append((world_x, world_y, world_z))
                
                # Convert to block coordinates (floor to get the block position)
                block_x = math.floor(world_x)
                block_y = math.floor(world_y)
                block_z = math.floor(world_z)
                
                block_positions.add((block_x, block_y, block_z))
        
        return {
            'tile_coords': (tile_x, tile_z),
            'world_bounds': world_bounds,
            'num_triangles': parsed.get('num_triangles', 0),
            'num_vertices': len(vertex_positions),
            'block_positions': sorted(list(block_positions)),  # Convert set to sorted list
            'vertex_positions': vertex_positions,
            'materials': parsed.get('materials', []),
            'colors': parsed.get('colors', [])
        }


def main():
    """Example usage of the BlueMap connector."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python connector.py <bluemap_url>")
        print("Example: python connector.py http://localhost:8100")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print(f"Connecting to BlueMap at: {url}")
    connector = BlueMapConnector(url)
    
    try:
        # Get settings
        print("\n=== Settings ===")
        settings = connector.get_settings()
        print(f"Version: {settings.get('version', 'unknown')}")
        print(f"Available maps: {settings.get('maps', [])}")
        
        # Get map details
        print("\n=== Maps ===")
        maps = connector.get_maps()
        for map_id, map_info in maps.items():
            print(f"\nMap: {map_id}")
            print(f"  Name: {map_info.get('name', map_id)}")
            print(f"  Start Position: {map_info.get('startPos', 'unknown')}")
        
        # Example: Search for blocks (if maps exist)
        if maps:
            map_id = list(maps.keys())[0]
            print(f"\n=== Searching for tiles in map '{map_id}' ===")
            results = connector.search_block(
                "example_block",
                map_id=map_id,
                center_x=0,
                center_z=0,
                radius=2
            )
            
    except requests.RequestException as e:
        print(f"\nError connecting to BlueMap: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
