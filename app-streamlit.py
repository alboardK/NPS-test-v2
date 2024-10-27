import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
import os
import gspread
import logging
from datetime import datetime, timedelta

# Configuration initiale de Streamlit
st.set_page_config(
    page_title="Dashboard NPS Annette K.",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration du style CSS personnalisé
st.markdown("""
    <style>
        /* Style du header */
        .main-header {
            padding: 1rem;
            background-color: #262730;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
        }
        /* Style des onglets */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: #1E1E1E;
            padding: 0.5rem;
            border-radius: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 2rem;
            font-weight: 500;
        }
        /* Style des métriques */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 600;
        }
        /* Masquer les messages de débogage par défaut */
        .debug-info {
            display: none;
        }
        /* Style des graphiques */
        .plotly-chart {
            background-color: #262730;
            padding: 1rem;
            border-radius: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Classe pour gérer les données
class DataManager:
    @staticmethod
    @st.cache_resource
    def get_google_credentials():
        try:
            return service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        except Exception as e:
            return None

    @staticmethod
    def load_data():
        """Charge les données avec gestion des erreurs silencieuse"""
        try:
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
            sheet = gc.open_by_key("1i8TU3c72YH-5sfAKcxmeuthgSeHcW3-ycg7cwzOtkrE")
            worksheet = sheet.worksheet("Réponses")
            
            data = worksheet.get_all_values()
            df = pd.DataFrame(data[1:], columns=data[0])
            df = df.dropna(axis=1, how='all')
            
            # Conversion des dates
            if 'Horodateur' in df.columns:
                df['Horodateur'] = pd.to_datetime(df['Horodateur'], format='%d/%m/%Y %H:%M:%S')
            
            return df
        except Exception as e:
            st.error("Erreur de chargement des données")
            return None

# Classe pour les visualisations
class NPSVisualizer:
    def __init__(self, df):
        self.df = df
        self.nps_col = [col for col in df.columns if "recommand" in col.lower() and "échelle" in col.lower()][0]
        self.process_nps_data()

    def process_nps_data(self):
        """Traitement initial des données NPS"""
        try:
            self.df['NPS_Score'] = pd.to_numeric(
                self.df[self.nps_col].str.extract('(\d+)')[0], 
                errors='coerce'
            )
            self.df['NPS_Category'] = self.df['NPS_Score'].apply(
                lambda x: 'Promoteur' if x >= 9 else 'Passif' if x >= 7 else 'Détracteur' if x >= 0 else None
            )
        except Exception as e:
            st.error("Erreur dans le traitement des données NPS")

    def show_kpi_metrics(self):
        """Affiche les métriques clés"""
        try:
            total_responses = len(self.df[self.df['NPS_Score'].notna()])
            promoters_pct = len(self.df[self.df['NPS_Category'] == 'Promoteur']) / total_responses * 100
            passifs_pct = len(self.df[self.df['NPS_Category'] == 'Passif']) / total_responses * 100
            detractors_pct = len(self.df[self.df['NPS_Category'] == 'Détracteur']) / total_responses * 100
            nps_score = promoters_pct - detractors_pct

            cols = st.columns(4)
            metrics = [
                ("Score NPS", f"{nps_score:.1f}%", "Net Promoter Score"),
                ("Promoteurs", f"{promoters_pct:.1f}%", "Notes de 9-10"),
                ("Passifs", f"{passifs_pct:.1f}%", "Notes de 7-8"),
                ("Détracteurs", f"{detractors_pct:.1f}%", "Notes de 0-6")
            ]

            for col, (label, value, help_text) in zip(cols, metrics):
                col.metric(label, value, help=help_text)

        except Exception as e:
            st.error("Erreur dans l'affichage des métriques")

    def show_trend_charts(self):
        """Affiche les graphiques de tendance"""
        try:
            # Préparation des données temporelles
            self.df['Month'] = self.df['Horodateur'].dt.to_period('M')
            
            # Évolution du NPS
            monthly_data = self.df.groupby('Month').apply(
                lambda x: (
                    len(x[x['NPS_Category'] == 'Promoteur']) - 
                    len(x[x['NPS_Category'] == 'Détracteur'])
                ) / len(x) * 100
            ).reset_index()
            monthly_data.columns = ['Month', 'NPS']

            # Graphique d'évolution
            fig_nps = px.line(
                monthly_data,
                x='Month',
                y='NPS',
                title="Évolution mensuelle du Score NPS",
                labels={'NPS': 'Score NPS (%)', 'Month': 'Mois'},
                markers=True
            )
            st.plotly_chart(fig_nps, use_container_width=True)

        except Exception as e:
            st.error("Erreur dans l'affichage des graphiques")

def main():
    """Fonction principale de l'application"""
    # Chargement des données (silencieux)
    data_manager = DataManager()
    df = data_manager.load_data()

    # Interface utilisateur
    st.markdown('<div class="main-header"><h1 style="text-align: center">Dashboard NPS Annette K.</h1></div>', 
                unsafe_allow_html=True)

    if df is not None:
        # Création du visualiseur
        visualizer = NPSVisualizer(df)
        
        # Navigation principale
        tab1, tab2, tab3 = st.tabs([
            "📈 Tableau de Bord",
            "📊 Analyses Détaillées",
            "⚙️ Configuration"
        ])

        with tab1:
            visualizer.show_kpi_metrics()
            visualizer.show_trend_charts()

        with tab2:
            st.header("Analyses Détaillées")
            # [Ajoutez ici le code pour les analyses détaillées]

        with tab3:
            st.header("Configuration et Diagnostic")
            if st.checkbox("Afficher les informations de débogage"):
                st.write("Dimensions du DataFrame:", df.shape)
                st.write("Colonnes disponibles:", df.columns.tolist())
                st.write("Aperçu des données:", df.head())
                
                st.subheader("Qualité des données")
                null_counts = df.isnull().sum()
                if null_counts.any():
                    st.warning("Valeurs manquantes détectées:")
                    for col, count in null_counts[null_counts > 0].items():
                        st.write(f"- {col}: {count} valeurs manquantes")

if __name__ == "__main__":
    main()