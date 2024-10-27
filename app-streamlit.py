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
    
    # Liste qui contiendra toutes les sources
    sources = ["Google Sheets (Live)"]
    st.write(f"Sources initiales: {sources}")
    
    # Lecture du dossier data
    data_dir = 'data'
    try:
        if not os.path.exists(data_dir):
            st.warning(f"⚠️ Le dossier {data_dir} n'existe pas. Création du dossier...")
            os.makedirs(data_dir)
            st.success(f"✅ Dossier {data_dir} créé avec succès")
        
        # Liste tous les fichiers CSV dans le dossier
        csv_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.csv')]
        
        if csv_files:
            st.write(f"✅ {len(csv_files)} fichier(s) CSV trouvé(s)")
            for file in csv_files:
                st.write(f"📄 Fichier trouvé: {file}")
                sources.append(f"Fichier Local: {file}")
        else:
            st.write("ℹ️ Aucun fichier CSV trouvé dans le dossier data")
            
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du dossier data: {str(e)}")
    
    st.write(f"📋 Sources finales disponibles: {sources}")
    return sources

def load_local_data(filename):
    st.write(f"📂 Chargement du fichier local: {filename}")
    try:
        # Construction du chemin complet
        file_path = os.path.join('data', filename)
        st.write(f"🔍 Chemin complet: {file_path}")
        
        if not os.path.exists(file_path):
            st.error(f"❌ Fichier non trouvé: {file_path}")
            return None
            
        # Tentatives de lecture avec différents encodages
        encodings = ['utf-8', 'latin-1', 'ISO-8859-1', 'cp1252']
        df = None
        successful_encoding = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                successful_encoding = encoding
                break
            except UnicodeDecodeError:
                continue
            
        if df is None:
            st.error("❌ Impossible de lire le fichier avec les encodages standards")
            return None
            
        st.write(f"✅ Fichier chargé avec succès (encodage: {successful_encoding})")
        st.write(f"📊 Dimensions: {df.shape[0]} lignes x {df.shape[1]} colonnes")
        
        # Conversion des dates
        if 'Horodateur' in df.columns:
            try:
                df['Horodateur'] = pd.to_datetime(df['Horodateur'], format='%d/%m/%Y %H:%M:%S')
                st.write("✅ Conversion des dates réussie")
            except Exception as e:
                st.warning(f"⚠️ Erreur de conversion des dates: {str(e)}")
                st.write("🔍 Premier format de date trouvé:", df['Horodateur'].iloc[0])
        
        # Vérification de la cohérence des données
        st.write("🔍 Vérification des données...")
        null_counts = df.isnull().sum()
        if null_counts.any():
            st.warning("⚠️ Valeurs manquantes détectées:")
            for col, count in null_counts[null_counts > 0].items():
                st.write(f"- {col}: {count} valeurs manquantes")
                
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement: {type(e).__name__} - {str(e)}")
        return None

def handle_data_source_selection(data_source):
    """Gère la sélection et le chargement des données selon la source"""
    if data_source == "Google Sheets (Live)":
        st.write("🔄 Chargement des données depuis Google Sheets...")
        return load_sheets_data()
    elif data_source.startswith("Fichier Local:"):
        filename = data_source.replace("Fichier Local: ", "")
        st.write(f"📂 Chargement du fichier local: {filename}")
        return load_local_data(filename)
    else:
        st.error("❌ Source de données non reconnue")
        return None

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
    
    st.write("🚀 Démarrage de l'application...")
    
    # Récupération des sources de données disponibles
    available_sources = get_available_data_sources()
    
    # Sélecteur de source de données
    st.write("📌 Configuration du sélecteur de source...")
    data_source = st.selectbox(
        "Source des données",
        available_sources,
        help="Sélectionnez la source des données à analyser"
    )
    
    st.write(f"Source sélectionnée: {data_source}")
    
    # Chargement des données selon la source sélectionnée
    df = handle_data_source_selection(data_source)
    
    if df is not None:
        # Suite de votre code pour l'analyse et l'affichage des données
        st.write("✅ Données chargées avec succès")
        st.write(f"📊 Dimensions finales: {df.shape}")
    else:
        st.error("❌ Échec du chargement des données")

if __name__ == "__main__":
    main()