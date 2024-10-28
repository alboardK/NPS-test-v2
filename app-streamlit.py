import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
import os
import gspread
import logging
from datetime import datetime, timedelta


# Configuration initiale
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
    </style>
"""

# Fonction pour gérer le changement de thème
def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
    
# Application du thème
st.markdown(DARK_THEME if st.session_state.theme == 'dark' else LIGHT_THEME, unsafe_allow_html=True)

# Dans la fonction main(), ajouter le bouton de toggle juste après le titre :
def main():
    # Container pour le header avec le toggle
    with st.container():
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(
                '<div class="main-header"><h1 style="text-align: center">Dashboard NPS Annette K. 🏊‍♀️</h1></div>',
                unsafe_allow_html=True
            )
        with col2:
            theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
            if st.button(theme_icon):
                toggle_theme()
                st.rerun()

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
        """Affichage des graphiques avec améliorations"""
        try:
            if self.df.empty:
                st.warning("Aucune donnée disponible pour les graphiques")
                return

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
                    
                    # Calcul des pourcentages
                    stats['Promoteurs_pct'] = (stats['Promoteurs'] / total) * 100
                    stats['Passifs_pct'] = (stats['Passifs'] / total) * 100
                    stats['Détracteurs_pct'] = (stats['Détracteurs'] / total) * 100
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
                custom_data=['Total']  # Ajout du nombre total de réponses
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
            
            # Graphique de répartition amélioré
            df_stack = df_stats.copy()
            # Réorganisation pour empiler dans l'ordre souhaité
            stack_cols = ['Détracteurs_pct', 'Passifs_pct', 'Promoteurs_pct']
            
            fig_categories = px.bar(
                df_stack,
                x='Month',
                y=stack_cols,
                title="Répartition mensuelle des catégories",
                labels={
                    'value': 'Répartition (%)',
                    'Month': 'Mois',
                    'variable': 'Catégorie'
                },
                color_discrete_map={
                    'Détracteurs_pct': '#EF553B',
                    'Passifs_pct': '#FFA15A',
                    'Promoteurs_pct': '#00CC96'
                },
                custom_data=[  # Données pour le hover
                    'Détracteurs', 'Passifs', 'Promoteurs', 'Total'
                ]
            )
            
            # Personnalisation du hover
            fig_categories.update_traces(
                hovertemplate="<br>".join([
                    "Mois: %{x}",
                    "Pourcentage: %{y:.1f}%",
                    "Nombre: %{customdata[0]}",
                    "Total réponses: %{customdata[3]}"
                ])
            )
            
            fig_categories.update_layout(
                barmode='relative',  # Pour empiler
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
   
    def show_detailed_analysis(self):
        """Affiche les analyses détaillées avec gestion d'erreur améliorée"""
        try:
            # Filtres communs
            st.sidebar.header("Filtres")
            
            # Sélection de la période
            date_min = self.df['Horodateur'].min()
            date_max = self.df['Horodateur'].max()
            period = st.sidebar.selectbox(
                "Période d'analyse",
                ["Tout", "Dernier mois", "Dernier trimestre", "Dernière année"]
            )
            
            # Filtre des données selon la période
            if period == "Dernier mois":
                mask = self.df['Horodateur'] >= (date_max - pd.Timedelta(days=30))
            elif period == "Dernier trimestre":
                mask = self.df['Horodateur'] >= (date_max - pd.Timedelta(days=90))
            elif period == "Dernière année":
                mask = self.df['Horodateur'] >= (date_max - pd.Timedelta(days=365))
            else:
                mask = pd.Series(True, index=self.df.index)
                
            filtered_df = self.df[mask].copy()
            
            # 1. Analyse des Commentaires
            st.subheader("📝 Analyse des Commentaires")
            
            comment_category = st.selectbox(
                "Filtrer par catégorie",
                ["Tous", "Promoteurs", "Passifs", "Détracteurs"]
            )
            
            if comment_category != "Tous":
                comments_df = filtered_df[filtered_df['NPS_Category'] == comment_category]
            else:
                comments_df = filtered_df
            
            # Identification de la colonne de commentaires
            comment_col = [col for col in comments_df.columns if "pourquoi cette note" in col.lower()][0]
            
            # Affichage des derniers commentaires
            with st.expander("Derniers commentaires"):
                for _, row in comments_df.sort_values('Horodateur', ascending=False).head(5).iterrows():
                    try:
                        comment = row[comment_col] if pd.notna(row[comment_col]) else "Pas de commentaire"
                        st.markdown(f"""
                        **Date:** {row['Horodateur'].strftime('%d/%m/%Y')}  
                        **Catégorie:** {row['NPS_Category']}  
                        **Note NPS:** {row['NPS_Score']}  
                        **Commentaire:** {comment}
                        ---
                        """)
                    except Exception as e:
                        st.warning(f"Erreur d'affichage pour une entrée: {str(e)}")
            
            # 2. Analyse des Services
            st.subheader("🎯 Analyse des Services")
            
            # Identification des colonnes de service
            service_cols = [
                col for col in filtered_df.columns 
                if any(service in col.lower() for service in [
                    'expérience', 'qualité', 'disponibilité', 'coach',
                    'nageur', 'accueil', 'commercial', 'ambiance', 'propreté',
                    'vestiaire'
                ])
            ]
            
            if service_cols:
                # Conversion en numérique avec nettoyage
                service_data = filtered_df[service_cols].apply(
                    lambda x: pd.to_numeric(x.str.extract('(\d+)')[0], errors='coerce')
                )
                
                # Calcul des moyennes
                service_scores = service_data.mean().round(2)
                
                # Graphique radar
                fig_radar = px.line_polar(
                    r=service_scores.values,
                    theta=service_scores.index,
                    line_close=True
                )
                fig_radar.update_traces(fill='toself')
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 5]
                        )
                    )
                )
                st.plotly_chart(fig_radar)
                
                # Tableau des scores moyens
                st.dataframe(
                    service_scores.reset_index()
                    .rename(columns={'index': 'Service', 0: 'Score moyen'})
                    .sort_values('Score moyen', ascending=False)
                )
            
            # 3. Analyse du Réabonnement
            st.subheader("🔄 Analyse du Réabonnement")
            
            # Identification de la colonne de réabonnement
            reabo_col = [col for col in filtered_df.columns if "probabilité" in col.lower()][0]
            
            if reabo_col in filtered_df.columns:
                filtered_df['Reabo_Score'] = pd.to_numeric(
                    filtered_df[reabo_col].str.extract('(\d+)')[0], 
                    errors='coerce'
                )
                
                fig_correlation = px.scatter(
                    filtered_df,
                    x='NPS_Score',
                    y='Reabo_Score',
                    color='NPS_Category',
                    title="Corrélation entre NPS et Probabilité de Réabonnement",
                    labels={
                        'NPS_Score': 'Score NPS',
                        'Reabo_Score': 'Probabilité de Réabonnement'
                    },
                    color_discrete_map={
                        'Promoteur': '#00CC96',
                        'Passif': '#FFA15A',
                        'Détracteur': '#EF553B'
                    }
                )
                st.plotly_chart(fig_correlation)
            
            # 4. Statistiques
            st.subheader("📊 Statistiques")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Réponses par jour",
                    f"{len(filtered_df) / max(1, (date_max - date_min).days):.1f}",
                    help="Nombre moyen de réponses par jour"
                )
                
            with col2:
                st.metric(
                    "Taux de commentaires",
                    f"{filtered_df[comment_col].notna().mean()*100:.1f}%",
                    help="Pourcentage de réponses avec commentaires"
                )

        except Exception as e:
            st.error(f"Erreur dans l'analyse détaillée: {str(e)}")
            if st.checkbox("Afficher les détails de l'erreur"):
                st.write("Colonnes disponibles:", self.df.columns.tolist())

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
            visualizer.show_detailed_analysis()
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
