import os
import pandas as pd
import requests
from flask import Flask, render_template_string, jsonify
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from datetime import datetime
 
app = Flask(__name__)
 
# URL API hydro2 (przykładowy URL, zastąp rzeczywistym)
API_URL = "https://danepubliczne.imgw.pl/api/data/hydro2"
 
# Plik, w którym przechowywane są dane
CSV_FILE = 'hydro_data.csv'
 
# Funkcja do pobierania nowych danych z API
def fetch_new_data():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()  # Zwraca dane w formacie JSON
    else:
        return None
 
# Funkcja do zapisywania nowych danych do pliku CSV
def save_new_data(data, csv_file=CSV_FILE):
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
 
# Funkcja do usuwania starych danych w pliku
def refresh_and_save_data():
    # Pobieramy nowe dane z API
    new_data = fetch_new_data()
    if new_data:
        # Usuwamy stare dane
        with open(CSV_FILE, 'w', encoding='utf-8-sig') as f:
            f.truncate(0)
        # Zapisujemy nowe dane
        save_new_data(new_data)
        return new_data
    return None
 
# Funkcja do generowania wizualizacji
def generate_visualization(data):
    warning_data = data[data['stan'].between(450, 499, inclusive='left')]
    alarm_data = data[data['stan'] >= 500]
 
    warning_geometry = [Point(xy) for xy in zip(warning_data['lon'], warning_data['lat'])]
    alarm_geometry = [Point(xy) for xy in zip(alarm_data['lon'], alarm_data['lat'])]
 
    warning_gdf = gpd.GeoDataFrame(warning_data, geometry=warning_geometry, crs="EPSG:4326")
    alarm_gdf = gpd.GeoDataFrame(alarm_data, geometry=alarm_geometry, crs="EPSG:4326")
 
    # Załaduj granice Polski (GeoJSON)
    poland = gpd.read_file('/path/to/poland.geojson')
 
    # Rysowanie mapy
    fig, ax = plt.subplots(figsize=(10, 10))
    poland.plot(ax=ax, color='lightgray')
    warning_gdf.plot(ax=ax, marker='o', color='orange', markersize=5, label='Poziom Ostrzegawczy')
    alarm_gdf.plot(ax=ax, marker='o', color='red', markersize=5, label='Poziom Alarmowy')
 
    plt.legend()
    plt.title('Stacje z poziomem ostrzegawczym i alarmowym na mapie Polski')
    plt.show()
 
# Trasa główna strony
@app.route('/')
def index():
    data = pd.read_csv(CSV_FILE, delimiter=';')
    generate_visualization(data)
    return render_template_string("""
<html>
<head>
<style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                    }
                    h1 {
                        text-align: center;
                        margin-top: 20px;
                    }
                    #refresh-button {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        padding: 15px 30px;
                        background-color: #3498db;
                        color: white;
                        font-size: 16px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    }
                    #refresh-button:hover {
                        background-color: #2980b9;
                    }
                    p {
                        text-align: center;
                    }
</style>
</head>
<body>
<h1>Hydrologiczne dane IMGW</h1>
<button id="refresh-button" onclick="window.location.href='/refresh'">Odśwież dane</button>
<p>Ostatnia aktualizacja: {{ timestamp }}</p>
</body>
</html>
    """, timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
 
# Trasa do odświeżenia danych
@app.route('/refresh')
def refresh():
    new_data = refresh_and_save_data()
    if new_data:
        return jsonify(message="Dane zostały zaktualizowane", status="success")
    else:
        return jsonify(message="Nie udało się pobrać nowych danych", status="error")
 
if __name__ == '__main__':
    app.run(debug=True)
