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
        worksheet = sheet.get_worksheet(0)
        
        # Récupération des dimensions de la feuille
        rows = worksheet.row_count
        cols = worksheet.col_count
        st.write(f"📊 Dimensions de la feuille : {rows} lignes x {cols} colonnes")
        
        # Récupération de toutes les données
        all_values = worksheet.get_all_values()
        st.write(f"📊 Nombre total de lignes récupérées : {len(all_values)}")
        
        if len(all_values) <= 1:
            st.error("❌ Pas assez de données récupérées")
            return None
        
        # Affichage des en-têtes trouvés pour debug
        headers = all_values[0]
        st.write("📋 En-têtes trouvés dans le fichier :")
        for header in headers:
            if header:  # Affiche uniquement les en-têtes non vides
                st.write(f"- {header}")
        
        # Création du DataFrame avec toutes les données
        df = pd.DataFrame(all_values[1:], columns=headers)
        st.write(f"📊 DataFrame initial : {df.shape[0]} lignes x {df.shape[1]} colonnes")
        
        # Liste exacte des en-têtes existants pour vérification
        existing_columns = [col for col in df.columns if col.strip()]  # Enlève les colonnes vides
        
        # Si nous avons des données mais pas les bonnes colonnes, affichons les premières lignes
        if df.shape[0] > 0:
            st.write("🔍 Aperçu des premières lignes :")
            st.write(df.head(2).to_dict('records'))
        
        # Conservation de toutes les colonnes non vides pour l'instant
        df = df[existing_columns]
        
        # Conversion de la colonne date si elle existe
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'horodateur' in col.lower()]
        if date_columns:
            date_col = date_columns[0]
            try:
                df[date_col] = pd.to_datetime(df[date_col], format='%d/%m/%Y %H:%M:%S')
                st.write(f"✅ Conversion des dates réussie pour la colonne {date_col}")
            except Exception as e:
                st.warning(f"⚠️ Erreur lors de la conversion des dates : {str(e)}")
        
        st.write("✅ Chargement terminé avec succès")
        st.write(f"📊 Dimensions finales : {df.shape[0]} lignes x {df.shape[1]} colonnes")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {type(e).__name__} - {str(e)}")
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