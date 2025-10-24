#!/usr/bin/env python3
"""
Script per visualizzare perizie su TRMNL e-ink display
Ottimizzato per TRMNL Framework v2
Legge da Google Sheet e invia dati via Webhook a TRMNL
"""

import os
import requests
from datetime import datetime
import pandas as pd

# ==================== CONFIGURAZIONE ====================
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', 'YOUR_SHEET_ID_HERE')
TRMNL_WEBHOOK_URL = os.environ.get('TRMNL_WEBHOOK_URL', 'YOUR_WEBHOOK_URL_HERE')

# Soglia urgenza (giorni)
URGENCY_THRESHOLD = 7

# ==================== FUNZIONI ====================

def read_google_sheet(sheet_id):
    """Legge i dati dal Google Sheet pubblico"""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        df = pd.read_csv(url)
        print(f"✓ Letti {len(df)} record dal Google Sheet")
        print(f"  Colonne trovate: {df.columns.tolist()}")
        return df
    except Exception as e:
        print(f"✗ Errore lettura Google Sheet: {e}")
        return None

def calculate_days_difference(date_str):
    """Calcola la differenza in giorni da oggi"""
    try:
        # Prova prima il formato italiano gg/mm/aaaa
        try:
            target_date = datetime.strptime(date_str, '%d/%m/%Y')
        except:
            # Se fallisce, prova il formato ISO aaaa-mm-gg
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        diff = (target_date - today).days
        return diff
    except:
        return None

def format_days(days):
    """Formatta il numero di giorni con +/-"""
    if days is None:
        return "N/A"
    if days > 0:
        return f"+{days}"
    elif days < 0:
        return f"{days}"
    else:
        return "OGGI"

def format_date(date_str):
    """Formatta la data in formato gg/mm/aaaa"""
    try:
        # Prova prima il formato italiano gg/mm/aaaa
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        except:
            # Se fallisce, prova il formato ISO aaaa-mm-gg
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        return date_obj.strftime('%d/%m/%Y')
    except:
        return ""

def is_urgent(days):
    """Determina se una scadenza è urgente"""
    if days is None:
        return False
    return abs(days) <= URGENCY_THRESHOLD

def process_perizie(df):
    """Processa i dati delle perizie e calcola i giorni"""
    perizie = []
    
    for _, row in df.iterrows():
        if row['Stato'] != 'Attiva':
            continue
            
        giuramento_days = calculate_days_difference(row['Data_Giuramento'])
        inizio_days = calculate_days_difference(row['Data_Inizio'])
        bozza_days = calculate_days_difference(row['Data_Bozza'])
        deposito_days = calculate_days_difference(row['Data_Deposito'])
        
        # Determina se c'è almeno una scadenza urgente
        any_urgent = (is_urgent(giuramento_days) or is_urgent(inizio_days) or 
                     is_urgent(bozza_days) or is_urgent(deposito_days))
        
        perizia = {
            'numero': row['Numero_Perizia'],
            'tribunale': row['Tribunale'],
            'giudice': row.get('Giudice', ''),
            'luogo_iop': row.get('Luogo_IOP', ''),
            'parti': row.get('Parti', ''),
            'any_urgent': any_urgent,
            'giur': format_days(giuramento_days),
            'giur_urg': is_urgent(giuramento_days),
            'giur_data': format_date(row['Data_Giuramento']),
            'inizio': format_days(inizio_days),
            'inizio_urg': is_urgent(inizio_days),
            'inizio_data': format_date(row['Data_Inizio']),
            'bozza': format_days(bozza_days),
            'bozza_urg': is_urgent(bozza_days),
            'bozza_data': format_date(row['Data_Bozza']),
            'dep': format_days(deposito_days),
            'dep_urg': is_urgent(deposito_days),
            'dep_data': format_date(row['Data_Deposito'])
        }
        
        perizie.append(perizia)
    
    print(f"✓ Processate {len(perizie)} perizie attive")
    return perizie

def send_to_trmnl(perizie):
    """Invia i dati a TRMNL via Webhook"""
    
    # Prepara i dati per TRMNL
    oggi = datetime.now()
    giorni_it = {
        'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
        'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'
    }
    mesi_it = {
        'January': 'Gennaio', 'February': 'Febbraio', 'March': 'Marzo',
        'April': 'Aprile', 'May': 'Maggio', 'June': 'Giugno',
        'July': 'Luglio', 'August': 'Agosto', 'September': 'Settembre',
        'October': 'Ottobre', 'November': 'Novembre', 'December': 'Dicembre'
    }
    
    data_formattata = oggi.strftime('%A %d %B %Y')
    for eng, ita in giorni_it.items():
        data_formattata = data_formattata.replace(eng, ita)
    for eng, ita in mesi_it.items():
        data_formattata = data_formattata.replace(eng, ita)
    
    # Costruisci il payload nel formato corretto per TRMNL
    payload = {
        "merge_variables": {
            "data_aggiornamento": data_formattata,
            "num_perizie": len(perizie),
            "perizie": perizie[:5]  # Max 5 perizie per non sovraccaricare
        }
    }
    
    print(f"✓ Preparate {len(perizie[:5])} perizie per invio")
    
    # Debug: mostra il payload
    import json
    print("✓ Payload preparato:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    # Invia a TRMNL
    try:
        response = requests.post(
            TRMNL_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"✓ Dati inviati a TRMNL: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  Risposta: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"✗ Errore invio a TRMNL: {e}")
        return False

# ==================== MAIN ====================

def main():
    print("=== TRMNL Perizie - Aggiornamento Display (Framework v2) ===\n")
    
    # 1. Leggi dati da Google Sheet
    df = read_google_sheet(GOOGLE_SHEET_ID)
    if df is None:
        return
    
    # 2. Processa le perizie
    perizie = process_perizie(df)
    
    if not perizie:
        print("✗ Nessuna perizia attiva trovata")
        return
    
    # 3. Invia a TRMNL
    success = send_to_trmnl(perizie)
    
    if success:
        print("\n=== Completato con successo ===")
    else:
        print("\n=== Completato con errori ===")

if __name__ == "__main__":
    main()
