import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from datetime import datetime, timedelta
import plotly.express as px
import os

# Configuration de l'authentification Google Sheets
@st.cache_resource
def get_google_credentials():
    st.write("🔑 Tentative de récupération des credentials Google...")
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        st.write("✅ Credentials Google récupérées avec succès")
        return credentials
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des credentials: {str(e)}")
        return None

# Fonction pour lister les fichiers CSV disponibles
def get_available_data_sources():
    st.write("📂 Recherche des sources de données disponibles...")
    
    # Ajout de l'option Google Sheets
    sources = ["Google Sheets (Live)"]
    st.write(f"Sources initiales: {sources}")
    
    # Lecture du dossier data
    data_dir = 'data'
    if os.path.exists(data_dir):
        st.write(f"✅ Dossier {data_dir} trouvé")
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        st.write(f"Fichiers CSV trouvés: {csv_files}")
        sources.extend([f"Fichier Local: {f}" for f in csv_files])
    else:
        st.write(f"❌ Dossier {data_dir} non trouvé")
    
    st.write(f"Sources finales disponibles: {sources}")
    return sources

# Fonction pour charger les données depuis Google Sheets
def load_sheets_data():
    st.write("🔄 Début du chargement des données Google Sheets")
    try:
        credentials = get_google_credentials()
        if credentials is None:
            st.error("❌ Échec de récupération des credentials")
            return None
            
        st.write("✅ Credentials récupérées avec succès")
        sheet_id = "1i8TU3c72YH-5sfAKcxmeuthgSeHcW3-ycg7cwzOtkrE"
        
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(0)
        
        # Récupération des données brutes
        all_values = worksheet.get_all_values()
        
        # Récupération des en-têtes (première ligne)
        headers = all_values[0]
        
        # Création d'en-têtes uniques si nécessaire
        unique_headers = []
        seen = {}
        for i, h in enumerate(headers):
            if h in seen:
                unique_headers.append(f"{h}_{seen[h]}")
                seen[h] += 1
            else:
                unique_headers.append(h)
                seen[h] = 1
        
        # Création du DataFrame avec les en-têtes uniques
        df = pd.DataFrame(all_values[1:], columns=unique_headers)
        
        st.write("✅ Données chargées avec succès")
        st.write(f"Colonnes chargées: {', '.join(df.columns)}")
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur détaillée: {type(e).__name__} - {str(e)}")
        return None
def main():
    st.title("Dashboard NPS Annette K.")
    
    # Sélection de la source de données
    st.write("🚀 Démarrage de l'application...")
    available_sources = get_available_data_sources()
    
    st.write("📌 Configuration du sélecteur de source...")
    data_source = st.selectbox(
        "Source des données",
        available_sources,
        help="Sélectionnez la source des données à analyser"
    )
    
    st.write(f"Source sélectionnée: {data_source}")
    
    # Chargement des données selon la source sélectionnée
    if data_source == "Google Sheets (Live)":
        st.write("🔄 Chargement des données depuis Google Sheets...")
        df = load_sheets_data()
        if df is None:
            st.error("❌ Erreur lors du chargement des données Google Sheets")
            return
    else:
        # Extraction du nom du fichier
        filename = data_source.replace("Fichier Local: ", "")
        df = load_local_data(filename)
if __name__ == "__main__":
    main()