#!/usr/bin/env python3
"""
Script per visualizzare perizie su TRMNL e-ink display
Versione robusta:
- Gestisce celle vuote del Google Sheet
- Evita NaN nel payload JSON
- Gestisce date mancanti o in formato diverso
- Valida il payload prima dell'invio
"""

import os
import math
import json
import requests
import pandas as pd

from datetime import datetime

# ==================== CONFIGURAZIONE ====================

GOOGLE_SHEET_ID = os.environ.get(
    'GOOGLE_SHEET_ID',
    'YOUR_SHEET_ID_HERE'
)

TRMNL_WEBHOOK_URL = os.environ.get(
    'TRMNL_WEBHOOK_URL',
    'YOUR_WEBHOOK_URL_HERE'
)

URGENCY_THRESHOLD = 7


# ==================== FUNZIONI DI SUPPORTO ====================

def safe_str(value):
    """
    Converte qualsiasi valore in stringa sicura.
    Restituisce stringa vuota se None o NaN.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except:
        pass

    return str(value).strip()


def parse_date(date_str):
    """
    Converte una data in datetime.

    Formati accettati:

    31/12/2026
    2026-12-31
    """

    date_str = safe_str(date_str)

    if not date_str:
        return None

    formats = [
        "%d/%m/%Y",
        "%Y-%m-%d"
    ]

    for fmt in formats:

        try:
            return datetime.strptime(date_str, fmt)

        except ValueError:
            pass

    return None


def calculate_days_difference(date_str):
    """
    Calcola differenza in giorni da oggi.
    """

    target_date = parse_date(date_str)

    if target_date is None:
        return None

    today = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    return (target_date - today).days


def format_days(days):
    """
    Formatta il numero di giorni.
    """

    if days is None:
        return "N/A"

    if days > 0:
        return f"+{days}"

    if days < 0:
        return str(days)

    return "OGGI"


def format_date(date_str):
    """
    Restituisce data in formato gg/mm/aaaa.
    """

    d = parse_date(date_str)

    if d is None:
        return ""

    return d.strftime("%d/%m/%Y")


def is_urgent(days):
    """
    Determina se una scadenza è urgente.
    """

    if days is None:
        return False

    if days > 0:

        return days <= URGENCY_THRESHOLD

    return abs(days) <= 3


# ==================== VALIDAZIONE JSON ====================

def validate_json(obj, path="root"):

    if isinstance(obj, dict):

        for k, v in obj.items():

            validate_json(
                v,
                f"{path}.{k}"
            )

    elif isinstance(obj, list):

        for i, v in enumerate(obj):

            validate_json(
                v,
                f"{path}[{i}]"
            )

    elif isinstance(obj, float):

        if math.isnan(obj):

            raise ValueError(
                f"NaN trovato in {path}"
            )

        if math.isinf(obj):

            raise ValueError(
                f"Valore infinito in {path}"
            )


# ==================== LETTURA GOOGLE SHEET ====================

def read_google_sheet(sheet_id):

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{sheet_id}/export?format=csv"
    )

    try:

        df = pd.read_csv(
            url,
            dtype=str,
            keep_default_na=False,
            na_filter=False
        )

        df = df.apply(
            lambda col: col.str.strip()
        )

        print(
            f"✓ Letti {len(df)} record dal Google Sheet"
        )

        print(
            f"  Colonne trovate: {df.columns.tolist()}"
        )

        return df

    except Exception as e:

        print(
            f"✗ Errore lettura Google Sheet: {e}"
        )

        return None


# ==================== ELABORAZIONE DATI ====================

def process_perizie(df):

    perizie = []

    for _, row in df.iterrows():

        stato = safe_str(row.get("Stato"))

        if stato.lower() != "attiva":

            continue

        giuramento_days = calculate_days_difference(
            row.get("Data_Giuramento")
        )

        inizio_days = calculate_days_difference(
            row.get("Data_Inizio")
        )

        bozza_days = calculate_days_difference(
            row.get("Data_Bozza")
        )

        deposito_days = calculate_days_difference(
            row.get("Data_Deposito")
        )

        any_urgent = (

            is_urgent(giuramento_days)

            or

            is_urgent(inizio_days)

            or

            is_urgent(bozza_days)

            or

            is_urgent(deposito_days)

        )

        perizia = {

            'numero':

                safe_str(
                    row.get('Numero_Perizia')
                ),

            'tribunale':

                safe_str(
                    row.get('Tribunale')
                ),

            'giudice':

                safe_str(
                    row.get('Giudice')
                ),

            'luogo_iop':

                safe_str(
                    row.get('Luogo_IOP')
                ),

            'parti':

                safe_str(
                    row.get('Parti')
                ),

            'any_urgent':

                any_urgent,

            'giur':

                format_days(
                    giuramento_days
                ),

            'giur_urg':

                is_urgent(
                    giuramento_days
                ),

            'giur_data':

                format_date(
                    row.get(
                        'Data_Giuramento'
                    )
                ),

            'inizio':

                format_days(
                    inizio_days
                ),

            'inizio_urg':

                is_urgent(
                    inizio_days
                ),

            'inizio_data':

                format_date(
                    row.get(
                        'Data_Inizio'
                    )
                ),

            'bozza':

                format_days(
                    bozza_days
                ),

            'bozza_urg':

                is_urgent(
                    bozza_days
                ),

            'bozza_data':

                format_date(
                    row.get(
                        'Data_Bozza'
                    )
                ),

            'dep':

                format_days(
                    deposito_days
                ),

            'dep_urg':

                is_urgent(
                    deposito_days
                ),

            'dep_data':

                format_date(
                    row.get(
                        'Data_Deposito'
                    )
                )
        }

        perizie.append(perizia)

    print(
        f"✓ Processate {len(perizie)} perizie attive"
    )

    return perizie


# ==================== INVIO A TRMNL ====================

def send_to_trmnl(perizie):

    oggi = datetime.now()

    giorni_it = {

        'Monday': 'Lunedì',
        'Tuesday': 'Martedì',
        'Wednesday': 'Mercoledì',
        'Thursday': 'Giovedì',
        'Friday': 'Venerdì',
        'Saturday': 'Sabato',
        'Sunday': 'Domenica'

    }

    mesi_it = {

        'January': 'Gennaio',
        'February': 'Febbraio',
        'March': 'Marzo',
        'April': 'Aprile',
        'May': 'Maggio',
        'June': 'Giugno',
        'July': 'Luglio',
        'August': 'Agosto',
        'September': 'Settembre',
        'October': 'Ottobre',
        'November': 'Novembre',
        'December': 'Dicembre'

    }

    data_formattata = oggi.strftime(
        '%A %d %B %Y'
    )

    for eng, ita in giorni_it.items():

        data_formattata = data_formattata.replace(
            eng,
            ita
        )

    for eng, ita in mesi_it.items():

        data_formattata = data_formattata.replace(
            eng,
            ita
        )

    payload = {

        "merge_variables": {

            "data_aggiornamento":

                data_formattata,

            "num_perizie":

                len(perizie),

            "perizie":

                perizie[:5]

        }

    }

    print(
        f"✓ Preparate "
        f"{len(perizie[:5])} "
        f"perizie per invio"
    )

    validate_json(payload)

    print("✓ Payload preparato:")

    print(

        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False
        )

    )

    try:

        response = requests.post(

            TRMNL_WEBHOOK_URL,

            json=payload,

            headers={

                'Content-Type':
                'application/json'

            },

            timeout=30

        )

        print(

            f"✓ Dati inviati a "
            f"TRMNL: "
            f"{response.status_code}"

        )

        if response.status_code != 200:

            print(
                f"Risposta:"
            )

            print(
                response.text
            )

        return (

            response.status_code

            ==

            200

        )

    except Exception as e:

        print(

            f"✗ Errore invio "
            f"a TRMNL: {e}"

        )

        return False


# ==================== MAIN ====================

def main():
    print(

        "=== "
        "TRMNL Perizie "
        "- Aggiornamento "
        "Display "
        "(Robusto)"
        " ===\n"

    )

    df = read_google_sheet(
        GOOGLE_SHEET_ID
    )

    if df is None:

        return

    perizie = process_perizie(df)

    if not perizie:

        print(

            "✗ Nessuna "
            "perizia attiva "
            "trovata"

        )

        return

    success = send_to_trmnl(
        perizie
    )

    if success:

        print(
            "\n=== "
            "Completato "
            "con successo "
            "==="
        )

    else:

        print(
            "\n=== "
            "Completato "
            "con errori "
            "==="
        )


if __name__ == "__main__":

    main()
