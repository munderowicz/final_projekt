import os
import pandas as pd
import requests
from flask import Flask, render_template_string, jsonify
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from datetime import datetime
from jinja2 import Template
 
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
 
# Funkcja do klasyfikacji poziomów wód
def classify_water_levels(data):
    alarm_state = []
    warning_state = []
    normal_state = []
    for row in data:
        try:
            if row['stan'] is not None:
                level = float(row['stan'])
                if level >= 500:
                    alarm_state.append(row)
                elif 450 <= level < 500:
                    warning_state.append(row)
                else:
                    normal_state.append(row)
        except (ValueError, TypeError):
            continue
    return alarm_state, warning_state, normal_state
 
# Funkcja do generowania raportu HTML
def generate_html_from_csv(csv_file='hydro_data.csv', output_file='hydro_table.html'):
    # Wczytaj dane z pliku CSV
    data = []
    with open(csv_file, mode='r', encoding='utf-8-sig') as file:
        reader = pd.read_csv(file, delimiter=';')
        for row in reader:
            # Konwersja pustych wartości na None dla lepszego wyświetlania
            cleaned_row = {k: (v if v != '' else None) for k, v in row.items()}
            data.append(cleaned_row)
 
    # Klasyfikacja stanów wód
    alarm_state, warning_state, normal_state = classify_water_levels(data)
 
    # Szablon HTML z tabelami danych
    html_template = Template("""
<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dane hydrologiczne IMGW (hydro2)</title>
<style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            h1, h2 {
                color: #2c3e50;
                text-align: center;
            }
            .table-container {
                overflow-x: auto;
                margin: 20px 0;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.9em;
                margin-bottom: 20px;
            }
            th, td {
                padding: 10px 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #3498db;
                color: white;
                position: sticky;
                top: 0;
            }
            .footer {
                text-align: center;
                margin-top: 20px;
                color: #7f8c8d;
                font-size: 0.9em;
            }
            .summary {
                display: flex;
                justify-content: space-around;
                margin-bottom: 20px;
            }
            .summary-box {
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                color: white;
            }
            .alarm-summary {
                background-color: #ff4444;
            }
            .warning-summary {
                background-color: #ffc107;
            }
            .normal-summary {
                background-color: #28a745;
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
</style>
</head>
<body>
<h1>Dane hydrologiczne IMGW (hydro2)</h1>
 
        <div class="summary">
<div class="summary-box alarm-summary">
                Stany alarmowe (≥500): {{ alarm_state|length }}
</div>
<div class="summary-box warning-summary">
                Stany ostrzegawcze (450-499): {{ warning_state|length }}
</div>
<div class="summary-box normal-summary">
                Stany normalne (<450): {{ normal_state|length }}
</div>
</div>
 
        <button id="refresh-button" onclick="window.location.href='/refresh'">Odśwież dane</button>
 
        <h2>⚠️ Stany alarmowe (≥500)</h2>
<div class="table-container alarm">
<table>
<thead>
<tr>
<th>Kod stacji</th>
<th>Nazwa stacji</th>
<th>Współrzędne</th>
<th>Stan wody</th>
</tr>
</thead>
<tbody>
                    {% for row in alarm_state %}
<tr>
<td>{{ row['kod_stacji'] }}</td>
<td>{{ row['nazwa_stacji'] }}</td>
<td>{{ row['lon'] }}, {{ row['lat'] }}</td>
<td>{{ row['stan'] }}</td>
</tr>
                    {% endfor %}
</tbody>
</table>
</div>
 
        <h2>⚠ Stany ostrzegawcze (450-499)</h2>
<div class="table-container warning">
<table>
<thead>
<tr>
<th>Kod stacji</th>
<th>Nazwa stacji</th>
<th>Współrzędne</th>
<th>Stan wody</th>
</tr>
</thead>
<tbody>
                    {% for row in warning_state %}
<tr>
<td>{{ row['kod_stacji'] }}</td>
<td>{{ row['nazwa_stacji'] }}</td>
<td>{{ row['lon'] }}, {{ row['lat'] }}</td>
<td>{{ row['stan'] }}</td>
</tr>
                    {% endfor %}
</tbody>
</table>
</div>
 
        <div class="footer">
            Ostatnia aktualizacja: {{ timestamp }} | Liczba rekordów: {{ data|length }}
</div>
</body>
</html>
    """)
 
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_html = html_template.render(
        data=data,
        alarm_state=alarm_state,
        warning_state=warning_state,
        normal_state=normal_state,
        timestamp=timestamp
    )
 
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
 
    print(f"✅ Wygenerowano plik HTML: {output_file}")
 
# Strona główna
@app.route('/')
def index():
    data = pd.read_csv(CSV_FILE, delimiter=';')
    generate_html_from_csv()
    return render_template_string("{{ html }}")
 
# Trasa do odświeżania danych
@app.route('/refresh')
def refresh():
    new_data = refresh_and_save_data()
    if new_data:
        return jsonify(message="Dane zostały zaktualizowane", status="success")
    else:
        return jsonify(message="Nie udało się pobrać nowych danych", status="error")
 
if __name__ == '__main__':
    app.run(debug=True)
