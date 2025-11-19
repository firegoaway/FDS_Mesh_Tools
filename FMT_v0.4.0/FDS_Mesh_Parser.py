import re


def parse_fds_meshes(file_path):
    """
    Parse FDS file and extract mesh data.
    
    :param file_path: Path to the FDS file
    :return: List of mesh dictionaries with keys:
             'id', 'i', 'j', 'k', 'xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax'
    """
    meshes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        for i, line in enumerate(lines):
            # Look for MESH lines
            if line.strip().startswith('&MESH'):
                # Extract MESH parameters
                mesh_data = {}
                
                # Try to extract ID
                id_match = re.search(r"ID='([^']+)'", line)
                if id_match:
                    mesh_data['id'] = id_match.group(1)
                else:
                    # Generate an ID if not found
                    mesh_data['id'] = f'Mesh_{i}'
                
                # Extract IJK
                ijk_match = re.search(r'IJK=\s*(\d+),(\d+),(\d+)', line)
                if ijk_match:
                    mesh_data['i'] = int(ijk_match.group(1))
                    mesh_data['j'] = int(ijk_match.group(2))
                    mesh_data['k'] = int(ijk_match.group(3))
                else:
                    # Skip if IJK not found
                    continue
                    
                # Extract XB
                xb_match = re.search(r'XB=\s*([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+)', line)
                if xb_match:
                    mesh_data['xmin'] = float(xb_match.group(1))
                    mesh_data['xmax'] = float(xb_match.group(2))
                    mesh_data['ymin'] = float(xb_match.group(3))
                    mesh_data['ymax'] = float(xb_match.group(4))
                    mesh_data['zmin'] = float(xb_match.group(5))
                    mesh_data['zmax'] = float(xb_match.group(6))
                else:
                    # Skip if XB not found
                    continue
                    
                meshes.append(mesh_data)
                
    except Exception as e:
        print(f"Error parsing FDS file: {e}")
        raise
        
    return meshes


# Example usage
if __name__ == "__main__":
    # Test with the sample FDS file
    sample_file = "fds samples/fds6_sample.fds"
    try:
        meshes = parse_fds_meshes(sample_file)
        print(f"Found {len(meshes)} meshes:")
        for mesh in meshes:
            print(f"  {mesh}")
    except Exception as e:
        print(f"Error: {e}")