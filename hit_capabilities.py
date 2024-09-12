import requests
import os
import xml.etree.ElementTree as ET
import tempfile

def main():
    host = 'http://ogc-auth-proxy-internal.ogc-services:8000/'
    request = 'ogc/AFW_WMS?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities'
    url = f'{host}{request}'
    # Ping the request
    response = hit(url)
    # If you get a response, write it to a temporary file
    if response and response.status_code == 200:
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=True) as temp_file:
            temp_file.write(response.content)
            temp_file.flush()  # Ensure data is written to disk

            temp_filename = temp_file.name # get the filename

            layers = get_layers(temp_filename) # pass it into get_layers()
            print(layers)

    print(f'Response: {response.status_code}')  
    print(f"Response Time: {int(response.elapsed.total_seconds() * 1000)}ms")
    
    # for layer in layers:
    #     get_map(layer)
    

def hit(request):
    try:
        response = requests.get(request, stream=True)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def get_layers(filename):
    try:
        tree = ET.parse(filename)  
        root = tree.getroot()
        
        ns = {'xmlns': 'http://www.opengis.net/wms',
          'xlink': 'https://api.integr.afweather.mil/ogc/AFW_WMS'}
        
        capability = root.find("xmlns:Capability", ns)
        afw_layers = capability.find("xmlns:Layer", ns)
        
        print(afw_layers)
        
        for child in afw_layers:
            print(child.text)
        
        layers = []
        
        for layer in layers_root.findall("xmlns:Layer", ns):
            if not layer.find("xmlns:Name", ns).text =='Land':
                layer_name = layer.find("xmlns:Name", ns).text.split('_', 1)
                dims = layer.findall("xmlns:Dimension",ns)
                has_elevation = any(dim.attrib['name'] == "ELEVATION" for dim in dims)
                
                model = layer_name[0]
                layer_name = layer_name[1]
                
                layers.append((model, layer_name, has_elevation))
            continue
        
        return layers  
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None
    
def get_map(layer):
    
    DESTINATION = "ogc-auth-proxy-internal.ogc-services:8000"
    WIDTH = "900"
    HEIGHT= "600"
    IMG_FORMAT = "image/png"
    CONUS = "-133,23,-63,51"
    GLOBAL = '-180, -90, 180, 90'
    ELEVATION = "1000"
    
    print(f'Getting map {layer[0]}/{layer[1]}...')
    if not layer[1]: # if the layer does not have an elevation dimension
        request = (f'http://{DESTINATION}/WMS?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&FORMAT={IMG_FORMAT}&CRS=CRS:84&LAYERS=Land,{layer[0]}_{layer[1]}&STYLES=default&WIDTH={WIDTH}&HEIGHT={HEIGHT}&BBOX={CONUS}') 
        
    else: # if it does have the elevation dimension
        request = (f'http://{DESTINATION}/WMS?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&FORMAT={IMG_FORMAT}&CRS=CRS:84&LAYERS=Land,{layer[0]}_{layer[1]}&STYLES=default&WIDTH={WIDTH}&HEIGHT={HEIGHT}&BBOX={CONUS}&ELEVATION={ELEVATION}') 

    response = hit(request)
    path = f'{os.getcwd()}/maps/{layer[0]}'
    
    if not os.path.exists(path):
        os.mkdir(path)
    
    with open(f'{path}/{layer[1]}.png', 'wb') as file:
        file.write(response.content)

    

if __name__ == '__main__':
    main()
