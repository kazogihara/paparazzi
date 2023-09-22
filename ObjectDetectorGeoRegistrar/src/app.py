import io
from flask import Flask, request, jsonify
import requests
from PIL import Image, ExifTags
import torch

app = Flask(__name__)
app.config['APPLICATION_NAME'] = 'ObjectDetectorGeoRegistrar'

OBJECTS_API = "http://localhost:3000/api/objects"

# yolov5のセットアップ
model = torch.hub.load('ultralytics/yolov5:v7.0', 'yolov5s', pretrained=True)


@app.route('/detect', methods=['POST'])
def detect_objects():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        detected_objects = detect_with_yolo(image)
        lat, lon, alt = get_lat_lon(image)
        
        if lat is None or lon is None:
            return jsonify({'error': 'Could not get latitude or longitude from the image'}), 400
        
        for obj in detected_objects:
            data = {
                'name': obj,
                'latitude': lat,
                'longitude': lon,
                'altitude': alt
            }
            response = requests.post(OBJECTS_API, json=data)
            
            if response.status_code != 201:
                return jsonify({'error': 'Failed to register object'}), 500
        
        return jsonify({'message': 'Objects registered successfully'})


def detect_with_yolo(image):
    results = model(image)
    detected_objects = []
    df = results.pandas().xyxy[0]
    for index, row in df.iterrows():
        detected_objects.append(row['name'])
    return detected_objects


def get_lat_lon(image):
    try:
        exif_data = image._getexif()
        if exif_data is not None:
            for tag, value in exif_data.items():
                if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'GPSInfo':
                    gps_info = value
                    if gps_info is not None:
                        lat = gps_info.get(2, None)
                        lon = gps_info.get(4, None)
                        alt = gps_info.get(6, 0.0)
                        if lat and lon:
                            lat = convert_to_degrees(lat)
                            lon = convert_to_degrees(lon)
                            return float(lat), float(lon), float(alt)
    except Exception as e:
        app.logger.error(f"Error getting lat lon: {e}")
    return None, None, None


def convert_to_degrees(value):
    d, m, s = value
    d = float(d)
    m = float(m)
    s = float(s)
    return d + (m / 60.0) + (s / 3600.0)


if __name__ == '__main__':
    # app.run(port=4000)
    app.run(port=4000, debug=True, use_reloader=True, use_debugger=True) 
