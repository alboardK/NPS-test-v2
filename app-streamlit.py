import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from datetime import datetime, timedelta
import plotly.express as px
import os
import gspread 

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
        
        # Utilisation de gspread avec gestion des en-têtes dupliqués
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sheet = gc.open_by_key("1i8TU3c72YH-5sfAKcxmeuthgSeHcW3-ycg7cwzOtkrE")
        worksheet = sheet.get_worksheet(0)
        
        # Récupération des données avec gestion des en-têtes
        try:
            data = worksheet.get_all_records(expected_headers=[
                'Horodateur',
                'Sur une échelle de 1 à 10 , où 1 représente "je ne recommanderais pas du tout" et 10 "Avec enthousiasme", à quel point êtes-vous susceptible de conseiller Annette K à un proche ?',
                'Pourquoi cette note ?',
                'Sur une échelle de 1 à 10, Quelle est la probabilité que vous soyez toujours abonné chez Annette K. dans 6 mois ?',
                'Pourquoi cette réponse ?',
                "l'expérience à la salle de sport",
                "l'expérience piscine",
                "La qualité des coaching en groupe",
                "la disponibilité des cours sur le planning",
                "la disponibilité des équipements sportifs",
                "les coachs",
                "les maitres nageurs",
                "le personnel d'accueil",
                "Le commercial",
                "l'ambiance générale",
                "la propreté générale",
                "les vestiaires (douches / sauna/ serviettes..)"
            ])
        except Exception as e:
            st.write("⚠️ Tentative de récupération alternative des données...")
            # Si ça échoue, on essaie de récupérer toutes les valeurs et de créer le DataFrame manuellement
            values = worksheet.get_all_values()
            headers = values[0]
            data = values[1:]
            df = pd.DataFrame(data, columns=headers)
            return df
            
        df = pd.DataFrame(data)
        st.write("✅ Données chargées avec succès")
        st.write(f"Nombre de colonnes chargées: {len(df.columns)}")
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