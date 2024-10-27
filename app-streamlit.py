import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
import os
import gspread
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def get_available_data_sources():
    st.write("📂 Recherche des sources de données disponibles...")
    
    sources = ["Google Sheets (Live)"]
    st.write(f"Sources initiales: {sources}")
    
    data_dir = 'data'
    try:
        if not os.path.exists(data_dir):
            st.warning(f"⚠️ Le dossier {data_dir} n'existe pas. Création du dossier...")
            os.makedirs(data_dir)
            st.success(f"✅ Dossier {data_dir} créé avec succès")
        
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

def load_sheets_data():
    st.write("🔄 Début du chargement des données Google Sheets")
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sheet = gc.open_by_key("1i8TU3c72YH-5sfAKcxmeuthgSeHcW3-ycg7cwzOtkrE")
        
        st.write("📑 Recherche de l'onglet 'Réponses'...")
        try:
            worksheet = sheet.worksheet("Réponses")
            st.write("✅ Onglet 'Réponses' trouvé")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'accès à l'onglet 'Réponses': {str(e)}")
            all_worksheets = sheet.worksheets()
            st.write("📑 Onglets disponibles:")
            for ws in all_worksheets:
                st.write(f"- {ws.title}")
            return None
        
        rows = worksheet.row_count
        cols = worksheet.col_count
        st.write(f"📊 Dimensions de la feuille : {rows} lignes x {cols} colonnes")
        
        values = worksheet.get_all_values()
        if not values:
            st.error("❌ Aucune donnée récupérée")
            return None
            
        st.write(f"📊 Nombre total de lignes récupérées : {len(values)}")
        
        headers = values[0]
        df = pd.DataFrame(values[1:], columns=headers)
        df = df.dropna(axis=1, how='all')
        
        if 'Horodateur' in df.columns:
            df['Horodateur'] = pd.to_datetime(df['Horodateur'], format='%d/%m/%Y %H:%M:%S')
            st.write("✅ Conversion des dates réussie")
        
        st.write(f"📊 Dimensions finales : {df.shape[0]} lignes x {df.shape[1]} colonnes")
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement : {type(e).__name__} - {str(e)}")
        return None

def load_local_data(filename):
    st.write(f"📂 Chargement du fichier local: {filename}")
    try:
        file_path = os.path.join('data', filename)
        st.write(f"🔍 Chemin complet: {file_path}")
        
        if not os.path.exists(file_path):
            st.error(f"❌ Fichier non trouvé: {file_path}")
            return None
            
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
        
        if 'Horodateur' in df.columns:
            try:
                df['Horodateur'] = pd.to_datetime(df['Horodateur'], format='%d/%m/%Y %H:%M:%S')
                st.write("✅ Conversion des dates réussie")
            except Exception as e:
                st.warning(f"⚠️ Erreur de conversion des dates: {str(e)}")
                
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

def calculate_nps_metrics(df):
    """Calcule les métriques NPS avec gestion d'erreur améliorée"""
    # Définition de la colonne NPS
    nps_col = [col for col in df.columns if "recommand" in col.lower() and "échelle" in col.lower()]
    if not nps_col:
        st.error("❌ Colonne NPS non trouvée")
        return None
    nps_col = nps_col[0]
    
    try:
        # Conversion en numérique avec nettoyage
        df['NPS_Score'] = pd.to_numeric(df[nps_col].str.extract('(\d+)')[0], errors='coerce')
        
        # Calcul des catégories NPS
        df['NPS_Category'] = df['NPS_Score'].apply(lambda x: 
            'Promoteur' if x >= 9 
            else 'Passif' if x >= 7 
            else 'Détracteur' if x >= 0 
            else None
        )
        
        # Calculs des pourcentages
        total_responses = len(df[df['NPS_Score'].notna()])
        if total_responses == 0:
            st.error("❌ Aucune réponse valide trouvée")
            return None
            
        promoters_pct = len(df[df['NPS_Category'] == 'Promoteur']) / total_responses * 100
        detractors_pct = len(df[df['NPS_Category'] == 'Détracteur']) / total_responses * 100
        passifs_pct = len(df[df['NPS_Category'] == 'Passif']) / total_responses * 100
        
        # Calcul du NPS
        nps_score = promoters_pct - detractors_pct
        
        return {
            'nps_score': round(nps_score, 1),
            'promoters_pct': round(promoters_pct, 1),
            'passifs_pct': round(passifs_pct, 1),
            'detractors_pct': round(detractors_pct, 1),
            'total_responses': total_responses
        }
    except Exception as e:
        st.error(f"❌ Erreur dans le calcul du NPS: {str(e)}")
        return None

        return None
def show_data_source_tab(available_sources):
    """Nouvel onglet pour la gestion des sources de données"""
    st.header("🔄 Sources de Données")
    
    # Sélection de la source
    data_source = st.selectbox(
        "Source des données",
        available_sources,
        help="Sélectionnez la source des données à analyser"
    )
    
    # Chargement des données
    df = handle_data_source_selection(data_source)
    
    if df is not None:
        # Affichage des informations sur les données
        st.subheader("📊 Informations sur les données")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nombre de réponses", df.shape[0])
        with col2:
            st.metric("Nombre de colonnes", df.shape[1])
        with col3:
            date_range = df['Horodateur'].agg(['min', 'max'])
            st.metric("Période couverte", f"{date_range['min'].strftime('%d/%m/%y')} - {date_range['max'].strftime('%d/%m/%y')}")
        
        # Affichage des valeurs manquantes
        st.subheader("🔍 Analyse de la qualité des données")
        null_counts = df.isnull().sum()
        if null_counts.any():
            st.warning("⚠️ Valeurs manquantes détectées:")
            for col, count in null_counts[null_counts > 0].items():
                st.write(f"- {col}: {count} valeurs manquantes")
                
        return df
    return None

def show_nps_trends_tab(df):
    """Affichage amélioré des tendances NPS"""
    st.header("📈 Tableau de Bord NPS")
    
    metrics = calculate_nps_metrics(df)
    
    if metrics:
        # Métriques principales avec style amélioré
        st.subheader("Métriques Clés")
        cols = st.columns(4)
        with cols[0]:
            st.metric("Score NPS", f"{metrics['nps_score']}%", 
                     help="Net Promoter Score = % Promoteurs - % Détracteurs")
        with cols[1]:
            st.metric("Promoteurs", f"{metrics['promoters_pct']}%",
                     help="Clients ayant donné une note de 9 ou 10")
        with cols[2]:
            st.metric("Passifs", f"{metrics['passifs_pct']}%",
                     help="Clients ayant donné une note de 7 ou 8")
        with cols[3]:
            st.metric("Détracteurs", f"{metrics['detractors_pct']}%",
                     help="Clients ayant donné une note de 0 à 6")
        
        # Évolution temporelle
        st.subheader("Évolution dans le temps")
        
        # Préparation des données mensuelles
        df['Month'] = df['Horodateur'].dt.to_period('M')
        monthly_stats = df.groupby('Month').apply(calculate_nps_metrics).apply(pd.Series)
        
        # Graphique d'évolution NPS
        fig_nps = px.line(
            monthly_stats,
            x=monthly_stats.index.astype(str),
            y='nps_score',
            title="Évolution du Score NPS",
            labels={'x': 'Mois', 'y': 'Score NPS (%)'},
            markers=True
        )
        fig_nps.update_layout(
            xaxis_title="Mois",
            yaxis_title="Score NPS (%)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_nps)
        
        # Graphique de répartition
        categories_by_month = df.groupby(['Month', 'NPS_Category']).size().unstack(fill_value=0)
        categories_by_month_pct = categories_by_month.div(categories_by_month.sum(axis=1), axis=0) * 100
        
        fig_categories = px.bar(
            categories_by_month_pct,
            barmode='relative',
            title="Répartition mensuelle Promoteurs/Passifs/Détracteurs",
            labels={'value': 'Pourcentage', 'Month': 'Mois'},
            color_discrete_map={
                'Promoteur': '#00CC96',
                'Passif': '#FFA15A',
                'Détracteur': '#EF553B'
            }
        )
        fig_categories.update_layout(
            xaxis_title="Mois",
            yaxis_title="Répartition (%)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_categories)



def show_recent_responses_tab(df):
    st.header("🔍 Dernières Réponses")
    
    col1, col2 = st.columns(2)
    with col1:
        days_filter = st.slider("Nombre de jours à afficher", 1, 90, 30)
    with col2:
        category_filter = st.multiselect(
            "Catégories à afficher",
            ['Tous', 'Promoteur', 'Passif', 'Détracteur'],
            default=['Tous']
        )
    
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days_filter)
    recent_df = df[df['Horodateur'] > cutoff_date].copy()
    
    if 'Tous' not in category_filter:
        recent_df = recent_df[recent_df['NPS_Category'].isin(category_filter)]
    
    for _, row in recent_df.sort_values('Horodateur', ascending=False).iterrows():
        with st.expander(f"{row['Horodateur'].strftime('%d/%m/%Y')} - Score: {row['Sur une échelle de 1 à 10 , où 1 représente \"je ne recommanderais pas du tout\" et 10 \"Avec enthousiasme\", à quel point êtes-vous susceptible de conseiller Annette K à un proche ?']} ({row['NPS_Category']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("💭 Commentaire NPS:")
                st.write(row["Pourquoi cette note ?"])
            with col2:
                st.write("🔄 Probabilité de réabonnement:")
                st.write(f"Score: {row['Sur une échelle de 1 à 10, Quelle est la probabilité que vous soyez toujours abonné chez Annette K. dans 6 mois ?']}")
                st.write(row["Pourquoi cette réponse ?"])

def main():
    st.title("Dashboard NPS Annette K.")
    
    available_sources = get_available_data_sources()
    
    # Création des onglets avec nouvel ordre
    tab1, tab2, tab3 = st.tabs([
        "📊 Tableau de Bord",
        "📝 Réponses Récentes",
        "🔄 Sources de Données"
    ])
    
    # Gestion des données dans l'onglet Sources
    with tab3:
        df = show_data_source_tab(available_sources)
    
    # Affichage des autres onglets uniquement si les données sont chargées
    if df is not None:
        with tab1:
            show_nps_trends_tab(df)
        with tab2:
            show_recent_responses_tab(df)

if __name__ == "__main__":
    main()