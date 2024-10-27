import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from datetime import datetime, timedelta
import plotly.express as px
import os

# Configuration de l'authentification Google Sheets
@st.cache_resource
def get_google_credentials():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return credentials

# Fonction pour lister les fichiers CSV disponibles
def get_available_data_sources():
    # Ajout de l'option Google Sheets
    sources = ["Google Sheets (Live)"]
    
    # Lecture du dossier data
    data_dir = 'data'
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        sources.extend([f"Fichier Local: {f}" for f in csv_files])
    
    return sources

# Fonction pour charger les données depuis Google Sheets
def load_sheets_data():
    try:
        credentials = get_google_credentials()
        sheet_id = "1i8TU3c72YH-5sfAKcxmeuthgSeHcW3-ycg7cwzOtkrE"
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données depuis Google Sheets: {str(e)}")
        return None

# Fonction pour charger les données depuis un fichier local spécifique
def load_local_data(filename):
    try:
        file_path = os.path.join('data', filename)
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier {filename}: {str(e)}")
        return None

# Fonction de chargement des données selon la source sélectionnée
def load_data(source):
    if source == "Google Sheets (Live)":
        df = load_sheets_data()
        if df is not None:
            st.success("Connexion réussie à Google Sheets!")
    else:
        # Extraction du nom du fichier de la source sélectionnée
        filename = source.replace("Fichier Local: ", "")
        df = load_local_data(filename)
        if df is not None:
            st.success(f"Fichier '{filename}' chargé avec succès!")
    
    return process_data(df) if df is not None else None

# Fonction générique de traitement des données
def process_data(df):
    if df is not None:
        # Mapping des colonnes
        columns_mapping = {
            'Horodateur': 'date',
            'Sur une échelle de 1 à 10 , où 1 représente "je ne recommanderais pas du tout" et 10 "Avec enthousiasme", à quel point êtes-vous susceptible de conseiller Annette K à un proche ?': 'nps_score',
            'Sur une échelle de 1 à 10, Quelle est la probabilité que vous soyez toujours abonné chez Annette K. dans 6 mois ?': 'retention_score',
            "l'expérience à la salle de sport": 'score_salle',
            "l'expérience piscine": 'score_piscine',
            "La qualité des coaching en groupe": 'score_coaching_groupe',
            "la disponibilité des cours sur le planning": 'score_planning',
            "la disponibilité des équipements sportifs": 'score_equipements',
            "les coachs": 'score_coachs',
            "les maitres nageurs": 'score_maitres_nageurs',
            "le personnel d'accueil": 'score_accueil',
            "Le commercial": 'score_commercial',
            "l'ambiance générale": 'score_ambiance',
            "la propreté générale": 'score_proprete',
            "les vestiaires (douches / sauna/ serviettes..)": 'score_vestiaires',
            'Pourquoi cette note ?': 'commentaire_nps',
            'Pourquoi cette réponse ?': 'commentaire_retention'
        }
        
        # Renommer les colonnes
        for old_name, new_name in columns_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        try:
            # Conversion de la date
            df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y %H:%M:%S')
        except Exception as e:
            st.warning(f"Attention: Format de date non standard. Erreur: {str(e)}")
            # Tentative de conversion alternative
            try:
                df['date'] = pd.to_datetime(df['date'])
            except:
                st.error("Impossible de convertir la colonne date")
                return None
        
        return df
    return None

def calculate_nps(df):
    total_responses = len(df)
    if total_responses == 0:
        return 0
    
    promoters = len(df[df['nps_score'] >= 9])
    detractors = len(df[df['nps_score'] <= 6])
    
    nps = (promoters - detractors) / total_responses * 100
    return round(nps, 1)

def main():
    st.title("Dashboard NPS Annette K.")
    
    # Récupération des sources de données disponibles
    available_sources = get_available_data_sources()
    
    # Sélection de la source de données
    data_source = st.selectbox(
        "Source des données",
        available_sources,
        help="Sélectionnez la source des données à analyser"
    )
    
    # Information sur la source sélectionnée
    if data_source.startswith("Fichier Local:"):
        st.info(f"Source: {data_source}")
    
    # Chargement des données
    df = load_data(data_source)
    
    if df is not None:
        # [Le reste du code reste identique]
        # Filtrage sur les 12 derniers mois
        last_date = df['date'].max()
        start_date = last_date - timedelta(days=365)
        df_filtered = df[df['date'] >= start_date]
        
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        with col1:
            nps_score = calculate_nps(df_filtered)
            st.metric("Score NPS", f"{nps_score}")
        with col2:
            avg_retention = df_filtered['retention_score'].mean()
            st.metric("Score de rétention moyen", f"{avg_retention:.1f}/10")
        with col3:
            st.metric("Nombre de réponses", len(df_filtered))
        
        # [Suite du code identique...]
        # Graphiques et filtres comme précédemment...
        
        # Affichage des retours filtrés
        display_columns = ['date', 'nps_score', 'retention_score', 'commentaire_nps', 'commentaire_retention']
        st.dataframe(df_filtered[display_columns])

if __name__ == "__main__":
    main()
