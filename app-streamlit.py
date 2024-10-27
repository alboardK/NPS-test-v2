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
        # Identification de la colonne NPS de manière plus robuste
        self.nps_col = [col for col in df.columns if "recommand" in col.lower()][0]
        self.reabo_col = [col for col in df.columns if "probabilité" in col.lower()][0]
        self.process_nps_data()

    def process_nps_data(self):
        """Traitement des données NPS avec gestion d'erreur améliorée"""
        try:
            # Nettoyage et conversion des scores
            self.df['NPS_Score'] = self.df[self.nps_col].str.extract('(\d+)').astype(float)
            
            # Catégorisation
            def categorize_nps(score):
             if pd.isna(score): return None
             if score >= 9: return 'Promoteur'
             if score >= 6: return 'Passif'  # Modification ici pour inclure 6 comme passif
             return 'Détracteur'
            
            self.df['NPS_Category'] = self.df['NPS_Score'].apply(categorize_nps)
            
            # Ajout du mois pour les tendances
            self.df['Month'] = pd.to_datetime(self.df['Horodateur']).dt.to_period('M')
            
        except Exception as e:
            st.error(f"Erreur traitement données: {str(e)}")

    def show_trend_charts(self):
        """Affichage des graphiques avec gestion d'erreur améliorée"""
        try:
            # Calcul des métriques mensuelles
            monthly_metrics = []
            
            for month in self.df['Month'].unique():
                month_data = self.df[self.df['Month'] == month]
                total = len(month_data)
                if total > 0:
                    promoters = len(month_data[month_data['NPS_Category'] == 'Promoteur'])
                    detractors = len(month_data[month_data['NPS_Category'] == 'Détracteur'])
                    nps = (promoters - detractors) / total * 100
                    monthly_metrics.append({
                        'Month': month,
                        'NPS': nps,
                        'Promoteurs': promoters/total*100,
                        'Passifs': len(month_data[month_data['NPS_Category'] == 'Passif'])/total*100,
                        'Détracteurs': detractors/total*100
                    })
            
            df_metrics = pd.DataFrame(monthly_metrics)
            
            # Graphique d'évolution NPS
            fig_nps = px.line(
                df_metrics,
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
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_nps, use_container_width=True)
            
            # Graphique de répartition
            fig_categories = px.bar(
                df_metrics,
                x='Month',
                y=['Promoteurs', 'Passifs', 'Détracteurs'],
                title="Répartition mensuelle des catégories",
                labels={'value': 'Pourcentage', 'Month': 'Mois', 'variable': 'Catégorie'},
                color_discrete_map={
                    'Promoteurs': '#00CC96',
                    'Passifs': '#FFA15A',
                    'Détracteurs': '#EF553B'
                }
            )
            fig_categories.update_layout(
                barmode='relative',
                xaxis_title="Mois",
                yaxis_title="Répartition (%)",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_categories, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erreur graphiques: {str(e)}")

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