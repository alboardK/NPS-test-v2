import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
import os
import gspread
import logging
from datetime import datetime, timedelta

# Configuration initiale de la page
st.set_page_config(
    page_title="Dashboard NPS Annette K. 🏊‍♀️",
    page_icon="🏊‍♀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Gestion du thème
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# CSS pour les deux thèmes
LIGHT_THEME = """
    <style>
        /* Style du header - Light */
        .main-header {
            padding: 1rem;
            background-color: #f0f2f6;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            color: #262730;
        }
        /* Style des onglets - Light */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: #ffffff;
            padding: 0.5rem;
            border-radius: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 2rem;
            font-weight: 500;
            color: #262730;
        }
        /* Style des métriques - Light */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 600;
            color: #262730;
        }
        /* Couleurs de fond - Light */
        .stApp {
            background-color: #ffffff;
            color: #262730;
        }
        .element-container, .stMarkdown {
            color: #262730;
        }
        div[data-testid="stExpander"] {
            background-color: #f0f2f6;
            border: 1px solid #e0e0e0;
        }
        /* Style du bouton toggle - Light */
        [data-testid="baseButton-secondary"] {
            background-color: #f0f2f6 !important;
            border: 2px solid #262730 !important;
            color: #262730 !important;
        }
    </style>
"""

DARK_THEME = """
    <style>
        /* Style du header - Dark */
        .main-header {
            padding: 1rem;
            background-color: #262730;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
        }
        /* Style des onglets - Dark */
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
        /* Style des métriques - Dark */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 600;
        }
        /* Couleurs de fond - Dark */
        .stApp {
            background-color: #0E1117;
        }
        div[data-testid="stExpander"] {
            background-color: #262730;
            border: 1px solid #4A4A4A;
        }
        /* Style du bouton toggle - Dark */
        [data-testid="baseButton-secondary"] {
            background-color: transparent !important;
            border: 2px solid #4A4A4A !important;
            border-radius: 50% !important;
            padding: 15px !important;
            font-size: 1.5rem !important;
            transition: all 0.3s ease !important;
        }
        [data-testid="baseButton-secondary"]:hover {
            border-color: #808080 !important;
            transform: scale(1.1) !important;
        }
    </style>
"""

# Fonction pour gérer le changement de thème
def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
    
# Application du thème
st.markdown(DARK_THEME if st.session_state.theme == 'dark' else LIGHT_THEME, unsafe_allow_html=True)

# Classes de gestion des données et visualisation
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
            st.error(f"Erreur credentials: {str(e)}")
            return None

    @staticmethod
    def load_data():
        """Charge les données avec gestion des erreurs silencieuse"""
        try:
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
            sheet = gc.open_by_key("1i8TU3c72YH-5sfAKcxmeuthgSeHcW3-ycg7cwzOtkrE")
            worksheet = sheet.worksheet("Réponses")
            
            data = worksheet.get_all_values()
            if not data:
                st.error("Aucune donnée trouvée")
                return None
            
            df = pd.DataFrame(data[1:], columns=data[0])
            df = df.dropna(axis=1, how='all')
            
            if 'Horodateur' in df.columns:
                df['Horodateur'] = pd.to_datetime(df['Horodateur'], format='%d/%m/%Y %H:%M:%S')
            
            return df
            
        except Exception as e:
            st.error(f"Erreur chargement données: {str(e)}")
            return None

class NPSVisualizer:
    def __init__(self, df):
        self.df = df
        self.nps_col = [col for col in df.columns if "recommand" in col.lower()][0]
        self.reabo_col = [col for col in df.columns if "probabilité" in col.lower()][0]
        self.process_nps_data()

    def process_nps_data(self):
        try:
            self.df['NPS_Score'] = self.df[self.nps_col].str.extract('(\d+)').astype(float)
            
            def categorize_nps(score):
                if pd.isna(score): return None
                if score >= 9: return 'Promoteur'
                if score >= 6: return 'Passif'  # Règle française
                return 'Détracteur'
            
            self.df['NPS_Category'] = self.df['NPS_Score'].apply(categorize_nps)
            self.df['Month'] = pd.to_datetime(self.df['Horodateur']).dt.to_period('M')
            
        except Exception as e:
            st.error(f"Erreur traitement données: {str(e)}")

    def show_kpi_metrics(self):
        try:
            valid_responses = self.df[self.df['NPS_Category'].notna()]
            total_responses = len(valid_responses)
            
            if total_responses == 0:
                st.warning("Aucune réponse valide trouvée")
                return
            
            promoters = len(valid_responses[valid_responses['NPS_Category'] == 'Promoteur'])
            passifs = len(valid_responses[valid_responses['NPS_Category'] == 'Passif'])
            detractors = len(valid_responses[valid_responses['NPS_Category'] == 'Détracteur'])
            
            promoters_pct = (promoters / total_responses) * 100
            passifs_pct = (passifs / total_responses) * 100
            detractors_pct = (detractors / total_responses) * 100
            nps_score = promoters_pct - detractors_pct
            
            cols = st.columns(4)
            metrics = [
                ("Score NPS", f"{nps_score:.1f}%", "Net Promoter Score"),
                ("Promoteurs", f"{promoters_pct:.1f}%", f"{promoters} répondants"),
                ("Passifs", f"{passifs_pct:.1f}%", f"{passifs} répondants"),
                ("Détracteurs", f"{detractors_pct:.1f}%", f"{detractors} répondants")
            ]
            
            for col, (label, value, help_text) in zip(cols, metrics):
                col.metric(label=label, value=value, help=help_text)
                
        except Exception as e:
            st.error(f"Erreur calcul métriques: {str(e)}")

    def show_trend_charts(self):
        try:
            if self.df.empty:
                st.warning("Aucune donnée disponible pour les graphiques")
                return

            # Préparation des données mensuelles
            monthly_stats = []
            for month in sorted(self.df['Month'].unique()):
                month_data = self.df[self.df['Month'] == month]
                total = len(month_data)
                
                if total > 0:
                    stats = {
                        'Month': month.strftime('%Y-%m'),
                        'Total': total,
                        'Promoteurs': len(month_data[month_data['NPS_Category'] == 'Promoteur']),
                        'Passifs': len(month_data[month_data['NPS_Category'] == 'Passif']),
                        'Détracteurs': len(month_data[month_data['NPS_Category'] == 'Détracteur'])
                    }
                    
                    for key in ['Promoteurs', 'Passifs', 'Détracteurs']:
                        stats[f'{key}_pct'] = (stats[key] / total) * 100
                    stats['NPS'] = stats['Promoteurs_pct'] - stats['Détracteurs_pct']
                    
                    monthly_stats.append(stats)

            if not monthly_stats:
                st.warning("Pas assez de données pour générer les graphiques")
                return

            df_stats = pd.DataFrame(monthly_stats)
            
            # Graphique d'évolution NPS
            fig_nps = px.line(
                df_stats,
                x='Month',
                y='NPS',
                title="Évolution mensuelle du Score NPS",
                labels={'NPS': 'Score NPS (%)', 'Month': 'Mois'},
                markers=True,
                custom_data=['Total']
            )
            fig_nps.update_traces(
                hovertemplate="<br>".join([
                    "Mois: %{x}",
                    "NPS: %{y:.1f}%",
                    "Nombre de réponses: %{customdata[0]}"
                ])
            )
            fig_nps.update_layout(
                xaxis_title="Mois",
                yaxis_title="Score NPS (%)",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis={'showgrid': False},
                yaxis={'showgrid': True, 'gridcolor': 'rgba(128,128,128,0.2)'}
            )
            st.plotly_chart(fig_nps, use_container_width=True)
            
            # Graphique de répartition
            stack_cols = ['Détracteurs_pct', 'Passifs_pct', 'Promoteurs_pct']
            fig_categories = px.bar(
                df_stats,
                x='Month',
                y=stack_cols,
                title="Répartition mensuelle des catégories",
                labels={'value': 'Répartition (%)', 'Month': 'Mois'},
                color_discrete_map={
                    'Détracteurs_pct': '#EF553B',
                    'Passifs_pct': '#FFA15A',
                    'Promoteurs_pct': '#00CC96'
                }
            )
            fig_categories.update_layout(
                barmode='stack',
                showlegend=True,
                xaxis_title="Mois",
                yaxis_title="Répartition (%)",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            new_names = {
                'Promoteurs_pct': 'Promoteurs',
                'Passifs_pct': 'Passifs',
                'Détracteurs_pct': 'Détracteurs'
            }
            fig_categories.for_each_trace(lambda t: t.update(name=new_names[t.name]))
            
            st.plotly_chart(fig_categories, use_container_width=True)

        except Exception as e:
            st.error(f"Erreur graphiques: {str(e)}")

def main():
    # Header avec toggle de thème
    header_container = st.container()
    with header_container:
        col1, col2, col3 = st.columns([0.45, 0.1, 0.45])
        
        with col2:
            theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
            if st.button(
                theme_icon,
                help="Changer le thème clair/sombre",
                key="theme_toggle",
                use_container_width=True
            ):
                toggle_theme()
                st.rerun()
        
        st.markdown(
            '<div class="main-header"><h1 style="text-align: center">Dashboard NPS Annette K. 🏊‍♀️</h1></div>',
            unsafe_allow_html=True
        )

    # Chargement et affichage des données
    data_manager = DataManager()
    df = data_manager.load_data()
    
    if df is not None:
        visualizer = NPSVisualizer(df)
        
        tab1, tab2, tab3 = st.tabs([
            "📈 Tableau de Bord",
            "📊 Analyses Détaillées",
            "⚙️ Configuration"
        ])
        
        with tab1:
            visualizer.show_kpi_metrics()
            visualizer.show_trend_charts()
            
        with tab2:
            visualizer.show_detailed_analysis()
            
        with tab3:
            st.header("Configuration")
            if st.checkbox("Afficher les informations de débogage"):
                st.write("Dimensions:", df.shape)
                st.write("Colonnes:", df.columns.tolist())
                with st.expander("Aperçu des données"):
                    st.dataframe(df.head())

if __name__ == "__main__":
    main()
