#!/usr/bin/env python3
"""
BlueMap Web API Connector

This module provides a Python API to interact with a hosted BlueMap web interface.
It allows you to:
- Fetch map settings and metadata
- Request and parse map tiles
- Search for specific blocks within chunks

Usage:
    from connector import BlueMapConnector
    
    # Connect to a BlueMap instance
    connector = BlueMapConnector("http://localhost:8100")
    
    # Get available maps
    maps = connector.get_maps()
    print(f"Available maps: {list(maps.keys())}")
    
    # Search for a block
    results = connector.search_block("diamond_ore", map_id="world", 
                                    center_x=0, center_z=0, radius=5)
    print(f"Found {len(results)} chunks with diamond_ore")
"""

import requests
from typing import Dict, List, Tuple, Optional, Any
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
        
        Note: This is a basic parser that extracts metadata. Full geometry
        parsing would require implementing the complete PRBM format specification.
        
        Args:
            data: Raw PRBM file data
            
        Returns:
            Dictionary with parsed tile information
        """
        if len(data) < 12:
            raise ValueError("Invalid PRBM file: too short")
        
        # PRBM files are binary format used by BlueMap
        # This is a simplified parser - full implementation would need
        # to parse the entire geometry structure
        
        result = {
            'size': len(data),
            'raw_data': data,
            # Additional parsing would go here
        }
        
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
