import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from datetime import datetime, timedelta
import plotly.express as px
import os
import gspread 
import logging

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
        # Initialisation de gspread
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sheet = gc.open_by_key("1i8TU3c72YH-5sfAKcxmeuthgSeHcW3-ycg7cwzOtkrE")
        
        # Récupération de l'onglet "Réponses"
        st.write("📑 Recherche de l'onglet 'Réponses'...")
        try:
            worksheet = sheet.worksheet("Réponses")
            st.write("✅ Onglet 'Réponses' trouvé")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'accès à l'onglet 'Réponses': {str(e)}")
            # Liste des onglets disponibles pour debug
            all_worksheets = sheet.worksheets()
            st.write("📑 Onglets disponibles:")
            for ws in all_worksheets:
                st.write(f"- {ws.title}")
            return None
        
        # Récupération des dimensions
        rows = worksheet.row_count
        cols = worksheet.col_count
        st.write(f"📊 Dimensions de la feuille : {rows} lignes x {cols} colonnes")
        
        # Récupération des données
        st.write("⚠️ Récupération des données...")
        values = worksheet.get_all_values()
        
        if not values:
            st.error("❌ Aucune donnée récupérée")
            return None
            
        st.write(f"📊 Nombre total de lignes récupérées : {len(values)}")
        
        # Extraction des en-têtes
        headers = values[0]
        st.write("📋 En-têtes trouvés :")
        for h in headers:
            if h:  # Affiche uniquement les en-têtes non vides
                st.write(f"- {h}")
        
        # Création du DataFrame
        df = pd.DataFrame(values[1:], columns=headers)
        
        # Nettoyage des colonnes vides
        df = df.dropna(axis=1, how='all')
        st.write(f"📊 Dimensions après nettoyage : {df.shape}")
        
        # Aperçu des données
        st.write("🔍 Aperçu des premières lignes :")
        st.write(df.head(2))
        
        # Conversion de la colonne Horodateur
        if 'Horodateur' in df.columns:
            try:
                df['Horodateur'] = pd.to_datetime(df['Horodateur'], format='%d/%m/%Y %H:%M:%S')
                st.write("✅ Conversion des dates réussie")
            except Exception as e:
                st.warning(f"⚠️ Erreur lors de la conversion des dates : {str(e)}")
                st.write("Premier Horodateur :", df['Horodateur'].iloc[0])
        
        st.write("✅ Chargement terminé avec succès")
        st.write(f"📊 Dimensions finales : {df.shape[0]} lignes x {df.shape[1]} colonnes")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {type(e).__name__} - {str(e)}")
        st.error(f"Détails : {str(e)}")
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