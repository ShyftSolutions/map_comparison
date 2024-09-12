import requests
import os
import xml.etree.ElementTree as ET
import tempfile

def main():
    host = 'http://ogc-auth-proxy-internal.ogc-services:8000/'
    request = 'ogc/AFW_WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities'
    url = f'{host}{request}'
    # Hit the request
    response = hit(url)
    
    print(f'Response: {response.status_code}')  
    print(f"Response Time: {int(response.elapsed.total_seconds() * 1000)}ms")
    
    # If you get a response, write it to a temporary file
    if response and response.status_code == 200:
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=True) as temp_file:
            temp_file.write(response.content)
            temp_file.flush()  # Ensure data is written to disk

            temp_filename = temp_file.name # get the filename

            get_layers_helper(temp_filename) # pass it into get_layers_helper()
            
def hit(request):
    try:
        response = requests.get(request, stream=True)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    
def get_layers_helper(filename):
    try:
        tree = ET.parse(filename)  
        root = tree.getroot()
        
        ns = {'xmlns': 'http://www.opengis.net/wms',
          'xlink': 'https://api.integr.afweather.mil/ogc/AFW_WMS'}
        
        root = root.find("xmlns:Capability", ns)
        root = root.find("xmlns:Layer", ns)
        get_layers(root, ns)
            
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None
    
def get_layers(node, ns, filepath = ''):
    # get all of the layers that are children of the current node
    layer_children = node.findall('xmlns:Layer', ns) 
    
    if len(layer_children) == 0: # if we are at the leaf nodes
        layer_name = node.find('xmlns:Name', ns).text
        
        # make the map request
        map = get_map(node, ns)
        
        # write the map to the filepath
        write_map(map, filepath, f'{layer_name}.png')
        
        return
    
    else: # if the node has children layers
        for child in layer_children: # iterate through the layers 
            get_layers(child, ns, filepath + (f'{node.find("xmlns:Title",ns).text}/')) # recursively pass each child into the function with its future filepath
            

def get_map(node, ns):
    DESTINATION = "ogc-auth-proxy-internal.ogc-services:8000"
    WIDTH = "900"
    HEIGHT= "600"
    IMG_FORMAT = "image/png"
    CONUS = "-133,23,-63,51"
    GLOBAL = '-180, -90, 180, 90'
    ELEVATION = "1000"
    layer_name = node.find('xmlns:Name', ns).text
    
    dims = node.findall('xmlns:Dimension',ns)
    has_elevation = any(dim.attrib['name'] == "ELEVATION" for dim in dims)
    
    if has_elevation:
        request = f'http://{DESTINATION}/ogc/AFW_WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT={IMG_FORMAT}&LAYERS={layer_name}&BBOX={CONUS}&WIDTH={WIDTH}&HEIGHT={HEIGHT}&CRS=CRS:84&STYLES=default&ELEVATION={ELEVATION}'
    else:
        request = f'http://{DESTINATION}/ogc/AFW_WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT={IMG_FORMAT}&LAYERS={layer_name}&BBOX={CONUS}&WIDTH={WIDTH}&HEIGHT={HEIGHT}&CRS=CRS:84&STYLES=default'

    print(f'Making request for {layer_name}...')
    response = hit(request)
    return response.content # return the map
    
def write_map(map, filepath, filename):
    path = os.path.join(os.getcwd(), filepath)
    
    if not os.path.exists(path): # check if the directory exists
        os.makedirs(path)  # if not, make it

    with open(os.path.join(path, filename), 'wb') as file:
        file.write(map)
    

if __name__ == '__main__':
    main()