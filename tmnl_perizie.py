#!/usr/bin/env python3
"""
Script per visualizzare perizie su TRMNL e-ink display
Legge da Google Sheet e invia dati via Webhook a TRMNL
"""

import os
import requests
from datetime import datetime, date
import pandas as pd

# ==================== CONFIGURAZIONE ====================
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', 'YOUR_SHEET_ID_HERE')
TRMNL_WEBHOOK_URL = os.environ.get('TRMNL_WEBHOOK_URL', 'YOUR_WEBHOOK_URL_HERE')

# Soglia urgenza (giorni)
URGENCY_THRESHOLD = 7

# ==================== FUNZIONI ====================

def read_google_sheet():
    """Legge i dati dal Google Sheet pubblico"""
    url = f'https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0'
    
    try:
        df = pd.read_csv(url)
        # Rimuove spazi dai nomi delle colonne
        df.columns = df.columns.str.strip()
        print(f"✓ Letti {len(df)} record dal Google Sheet")
        print(f"  Colonne trovate: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"✗ Errore lettura Google Sheet: {e}")
        return None

def calculate_days_difference(target_date_str):
    """Calcola la differenza in giorni da oggi"""
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        today = date.today()
        diff = (target_date - today).days
        return diff
    except:
        return None

def format_date(date_str):
    """Formatta la data in formato gg/mm/aaaa"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except:
        return ""

def process_perizie(df):
    """Processa i dati delle perizie e calcola i giorni"""
    perizie = []
    
    for _, row in df.iterrows():
        if row['Stato'] != 'Attiva':
            continue
            
        perizia = {
            'numero': row['Numero_Perizia'],
            'tribunale': row['Tribunale'],
            'giudice': row.get('Giudice', ''),
            'luogo_iop': row.get('Luogo_IOP', ''),
            'giuramento': calculate_days_difference(row['Data_Giuramento']),
            'inizio': calculate_days_difference(row['Data_Inizio']),
            'bozza': calculate_days_difference(row['Data_Bozza']),
            'deposito': calculate_days_difference(row['Data_Deposito']),
            'data_giuramento': format_date(row['Data_Giuramento']),
            'data_inizio': format_date(row['Data_Inizio']),
            'data_bozza': format_date(row['Data_Bozza']),
            'data_deposito': format_date(row['Data_Deposito'])
        }
        
        # Calcola urgenza minima
        giorni = [perizia['giuramento'], perizia['inizio'], 
                  perizia['bozza'], perizia['deposito']]
        giorni_positivi = [g for g in giorni if g is not None and g > 0]
        perizia['urgenza_min'] = min(giorni_positivi) if giorni_positivi else 999
        
        perizie.append(perizia)
    
    # Ordina per urgenza
    perizie.sort(key=lambda x: x['urgenza_min'])
    
    print(f"✓ Processate {len(perizie)} perizie attive")
    return perizie

def format_days(days):
    """Formatta i giorni con segno"""
    if days is None:
        return "N/A"
    return f"{days:+d}" if days != 0 else "0"

def is_urgent(days):
    """Verifica se una data è urgente"""
    return days is not None and 0 < days <= URGENCY_THRESHOLD

def send_to_trmnl(perizie):
    """Invia i dati a TRMNL via Webhook"""
    
    # Prepara i dati per TRMNL
    oggi = datetime.now().strftime('%A %d %B %Y')
    giorni_it = {'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
                 'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'}
    for eng, ita in giorni_it.items():
        oggi = oggi.replace(eng, ita)
    
    # Crea l'array di perizie con info formattate
    perizie_data = []
    for p in perizie[:6]:  # Max 6 perizie
        perizie_data.append({
            'numero': p['numero'],
            'tribunale': p['tribunale'],
            'giudice': p['giudice'],
            'luogo_iop': p['luogo_iop'],
            'giur': format_days(p['giuramento']),
            'giur_urg': is_urgent(p['giuramento']),
            'giur_data': p['data_giuramento'],
            'inizio': format_days(p['inizio']),
            'inizio_urg': is_urgent(p['inizio']),
            'inizio_data': p['data_inizio'],
            'bozza': format_days(p['bozza']),
            'bozza_urg': is_urgent(p['bozza']),
            'bozza_data': p['data_bozza'],
            'dep': format_days(p['deposito']),
            'dep_urg': is_urgent(p['deposito']),
            'dep_data': p['data_deposito'],
            'any_urgent': (is_urgent(p['giuramento']) or is_urgent(p['inizio']) or 
                          is_urgent(p['bozza']) or is_urgent(p['deposito']))
        })
    
    # Payload per TRMNL - STRUTTURA CORRETTA
    payload = {
        "merge_variables": {
            "data_aggiornamento": oggi,
            "num_perizie": len(perizie),
            "perizie": perizie_data
        }
    }
    
    # Invia a TRMNL
    try:
        response = requests.post(
            TRMNL_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        print(f"✓ Dati inviati a TRMNL: {response.status_code}")
        return True
    except Exception as e:
        print(f"✗ Errore invio a TRMNL: {e}")
        return False

# ==================== MAIN ====================

def main():
    print("=== TRMNL Perizie - Aggiornamento Display ===\n")
    
    # 1. Leggi Google Sheet
    df = read_google_sheet()
    if df is None:
        return
    
    # 2. Processa perizie
    perizie = process_perizie(df)
    if not perizie:
        print("✗ Nessuna perizia attiva trovata")
        return
    
    # 3. Invia a TRMNL
    if TRMNL_WEBHOOK_URL != 'YOUR_WEBHOOK_URL_HERE':
        send_to_trmnl(perizie)
    else:
        print("⚠ TRMNL_WEBHOOK_URL non configurato")
    
    print("\n=== Completato ===")

if __name__ == "__main__":
    main()
