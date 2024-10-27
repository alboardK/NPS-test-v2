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
        
        # Récupération des dimensions de la feuille pour validation
        rows = worksheet.row_count
        cols = worksheet.col_count
        st.write(f"📊 Dimensions de la feuille : {rows} lignes x {cols} colonnes")
        
        # Récupération de toutes les données en une seule fois
        st.write("⚠️ Récupération des données brutes...")
        all_values = worksheet.get_all_values()
        st.write(f"📊 Nombre total de lignes récupérées : {len(all_values)}")
        
        if len(all_values) <= 1:
            st.error("❌ Pas assez de données récupérées")
            return None
            
        # Création du DataFrame avec toutes les données d'abord
        df_complet = pd.DataFrame(all_values[1:], columns=all_values[0])
        st.write(f"📊 DataFrame initial : {df_complet.shape[0]} lignes x {df_complet.shape[1]} colonnes")
        
        # Vérification des données avant filtrage
        st.write("📋 Premières colonnes disponibles :")
        for col in list(df_complet.columns)[:5]:  # Affiche les 5 premières colonnes
            st.write(f"- {col}")
        st.write(f"... et {len(df_complet.columns) - 5} autres colonnes")
        
        # Liste des colonnes nécessaires avec vérification de leur présence
        colonnes_necessaires = [
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
        ]
        
        # Vérification de l'existence des colonnes avant filtrage
        colonnes_manquantes = [col for col in colonnes_necessaires if col not in df_complet.columns]
        if colonnes_manquantes:
            st.warning("⚠️ Colonnes manquantes dans les données source :")
            for col in colonnes_manquantes:
                st.write(f"- {col}")
        
        # Filtrage uniquement sur les colonnes existantes
        colonnes_presentes = [col for col in colonnes_necessaires if col in df_complet.columns]
        if not colonnes_presentes:
            st.error("❌ Aucune colonne requise n'a été trouvée dans les données")
            return None
            
        df = df_complet[colonnes_presentes].copy()
        st.write(f"📊 Après sélection des colonnes : {df.shape[0]} lignes x {df.shape[1]} colonnes")
        
        # Conversion des dates avec gestion d'erreurs
        if 'Horodateur' in df.columns:
            try:
                df['Horodateur'] = pd.to_datetime(df['Horodateur'], format='%d/%m/%Y %H:%M:%S')
                st.write("✅ Conversion des dates réussie")
            except Exception as e:
                st.warning(f"⚠️ Erreur lors de la conversion des dates : {str(e)}")
                st.write("🔍 Exemple de valeurs dans Horodateur :", df['Horodateur'].head().tolist())
        
        st.write("✅ Chargement terminé avec succès")
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {type(e).__name__} - {str(e)}")
        logger.error(f"Erreur détaillée : {str(e)}", exc_info=True)
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