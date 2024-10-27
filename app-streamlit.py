import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
import os
import gspread
import logging
from datetime import datetime, timedelta

# Configuration initiale de Streamlit
# ... [imports et configuration de page restent identiques]

st.set_page_config(
    page_title="Dashboard NPS Annette K. 🏊‍♀️",
    page_icon="🏊‍♀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)
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
    </style>
""", unsafe_allow_html=True)

# Cette classe DataManager a deux responsabilités principales :
    # Gérer les credentials Google (get_google_credentials)
    # Charger les données (load_data)
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
            
            # Récupération des données
            data = worksheet.get_all_values()
            if not data:
                st.error("Aucune donnée trouvée")
                return None
                
            # Création du DataFrame
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Nettoyage basique
            df = df.dropna(axis=1, how='all')
            
            # Conversion des dates
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
            # Nettoyage et conversion des scores
            self.df['NPS_Score'] = self.df[self.nps_col].str.extract('(\d+)').astype(float)
            
            # Catégorisation avec règle française (6 = Passif)
            def categorize_nps(score):
                if pd.isna(score): return None
                if score >= 9: return 'Promoteur'
                if score >= 6: return 'Passif'
                return 'Détracteur'
            
            self.df['NPS_Category'] = self.df['NPS_Score'].apply(categorize_nps)
            self.df['Month'] = pd.to_datetime(self.df['Horodateur']).dt.to_period('M')
            
        except Exception as e:
            st.error(f"Erreur traitement données: {str(e)}")

    def show_kpi_metrics(self):
        """Affichage des métriques clés avec gestion d'erreur"""
        try:
            # Calcul des métriques sur les données valides
            valid_responses = self.df[self.df['NPS_Category'].notna()]
            total_responses = len(valid_responses)
            
            if total_responses == 0:
                st.warning("Aucune réponse valide trouvée")
                return
            
            # Calcul des pourcentages
            promoters = len(valid_responses[valid_responses['NPS_Category'] == 'Promoteur'])
            passifs = len(valid_responses[valid_responses['NPS_Category'] == 'Passif'])
            detractors = len(valid_responses[valid_responses['NPS_Category'] == 'Détracteur'])
            
            promoters_pct = (promoters / total_responses) * 100
            passifs_pct = (passifs / total_responses) * 100
            detractors_pct = (detractors / total_responses) * 100
            nps_score = promoters_pct - detractors_pct
            
            # Affichage avec mise en forme
            cols = st.columns(4)
            metrics = [
                ("Score NPS", f"{nps_score:.1f}%", "Net Promoter Score"),
                ("Promoteurs", f"{promoters_pct:.1f}%", f"{promoters} répondants"),
                ("Passifs", f"{passifs_pct:.1f}%", f"{passifs} répondants"),
                ("Détracteurs", f"{detractors_pct:.1f}%", f"{detractors} répondants")
            ]
            
            for col, (label, value, help_text) in zip(cols, metrics):
                col.metric(
                    label=label,
                    value=value,
                    help=help_text
                )
        except Exception as e:
            st.error(f"Erreur calcul métriques: {str(e)}")
            st.error("Détails des données problématiques:", self.df['NPS_Score'].value_counts())
                
    def show_trend_charts(self):
        """Affichage des graphiques avec gestion d'erreur améliorée"""
        try:
            # Assurons-nous d'avoir des données valides
            if self.df.empty:
                st.warning("Aucune donnée disponible pour les graphiques")
                return

            # Préparation des données mensuelles
            monthly_stats = []
            
            # Conversion explicite en datetime pour le tri
            self.df['Month'] = pd.to_datetime(self.df['Horodateur']).dt.to_period('M')
            
            # Groupement par mois avec gestion d'erreur
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
                    
                    # Calcul des pourcentages
                    stats['Promoteurs_pct'] = (stats['Promoteurs'] / total) * 100
                    stats['Passifs_pct'] = (stats['Passifs'] / total) * 100
                    stats['Détracteurs_pct'] = (stats['Détracteurs'] / total) * 100
                    stats['NPS'] = stats['Promoteurs_pct'] - stats['Détracteurs_pct']
                    
                    monthly_stats.append(stats)

            if not monthly_stats:
                st.warning("Pas assez de données pour générer les graphiques")
                return

            # Création du DataFrame pour les graphiques
            df_stats = pd.DataFrame(monthly_stats)
            
            # 1. Graphique d'évolution du NPS
            fig_nps = px.line(
                df_stats,
                x='Month',
                y='NPS',
                title="Évolution mensuelle du Score NPS",
                labels={'NPS': 'Score NPS (%)', 'Month': 'Mois'},
                markers=True
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
            
            # 2. Graphique de répartition
            fig_categories = px.bar(
                df_stats,
                x='Month',
                y=['Promoteurs_pct', 'Passifs_pct', 'Détracteurs_pct'],
                title="Répartition mensuelle des catégories",
                labels={
                    'value': 'Pourcentage',
                    'Month': 'Mois',
                    'variable': 'Catégorie'
                },
                color_discrete_map={
                    'Promoteurs_pct': '#00CC96',
                    'Passifs_pct': '#FFA15A',
                    'Détracteurs_pct': '#EF553B'
                }
            )
            fig_categories.update_layout(
                barmode='stack',
                showlegend=True,
                xaxis_title="Mois",
                yaxis_title="Répartition (%)",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis={'showgrid': False},
                yaxis={'showgrid': True, 'gridcolor': 'rgba(128,128,128,0.2)'}
            )
            
            # Mise à jour des noms dans la légende
            new_names = {
                'Promoteurs_pct': 'Promoteurs',
                'Passifs_pct': 'Passifs',
                'Détracteurs_pct': 'Détracteurs'
            }
            fig_categories.for_each_trace(lambda t: t.update(name=new_names[t.name]))
            
            st.plotly_chart(fig_categories, use_container_width=True)

        except Exception as e:
            st.error(f"Erreur lors de la création des graphiques: {str(e)}")
            if st.checkbox("Afficher les détails de l'erreur"):
                st.write("Données mensuelles:", monthly_stats if 'monthly_stats' in locals() else "Non disponible")


def main():
    # En-tête avec émoji
    st.markdown('<div class="main-header"><h1 style="text-align: center">Dashboard NPS Annette K. 🏊‍♀️</h1></div>', 
                unsafe_allow_html=True)
    
    # Chargement silencieux des données
    data_manager = DataManager()
    df = data_manager.load_data()
    
    if df is not None:
        visualizer = NPSVisualizer(df)
        
        # Navigation
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
            # ... [code pour l'analyse détaillée]
            
        with tab3:
            st.header("Configuration")
            if st.checkbox("Afficher les informations de débogage"):
                st.write("Dimensions:", df.shape)
                st.write("Colonnes:", df.columns.tolist())
                with st.expander("Aperçu des données"):
                    st.dataframe(df.head())

if __name__ == "__main__":
    main()