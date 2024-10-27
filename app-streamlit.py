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
        """Affiche les analyses détaillées"""
        
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
        
        # Sélection de catégorie pour les commentaires
        comment_category = st.selectbox(
            "Filtrer par catégorie",
            ["Tous", "Promoteurs", "Passifs", "Détracteurs"]
        )
        
        if comment_category != "Tous":
            comments_df = filtered_df[filtered_df['NPS_Category'] == comment_category]
        else:
            comments_df = filtered_df
            
        # Affichage des derniers commentaires
        with st.expander("Derniers commentaires"):
            for _, row in comments_df.sort_values('Horodateur', ascending=False).head(5).iterrows():
                st.markdown(f"""
                **Date:** {row['Horodateur'].strftime('%d/%m/%Y')}  
                **Catégorie:** {row['NPS_Category']}  
                **Note NPS:** {row['NPS_Score']}  
                **Commentaire:** {row['Pourquoi cette note ?']}
                ---
                """)
        
        # 2. Analyse des Services
        st.subheader("🎯 Analyse des Services")
        
        # Identification des colonnes de service
        service_cols = [
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
        
        # Calcul des moyennes par service
        service_scores = filtered_df[service_cols].mean().round(2)
        
        # Graphique radar des services
        fig_radar = px.line_polar(
            r=service_scores.values,
            theta=service_scores.index,
            line_close=True
        )
        fig_radar.update_traces(fill='toself')
        st.plotly_chart(fig_radar)
        
        # 3. Analyse Réabonnement
        st.subheader("🔄 Analyse du Réabonnement")
        
        # Calcul de la corrélation entre NPS et réabonnement
        reabo_col = [col for col in filtered_df.columns if "probabilité" in col.lower()][0]
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
        
        # 4. Statistiques d'export (optionnel)
        st.subheader("📊 Statistiques et Export")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Taux de réponse moyen",
                f"{len(filtered_df) / (date_max - date_min).days:.1f}",
                help="Nombre moyen de réponses par jour"
            )
            
        with col2:
            st.metric(
                "Taux de commentaires",
                f"{filtered_df['Pourquoi cette note ?'].notna().mean()*100:.1f}%",
                help="Pourcentage de réponses avec commentaires"
            )
            
        if st.button("Exporter les données filtrées"):
            # Création du fichier Excel en mémoire
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False)
            
            # Téléchargement du fichier
            st.download_button(
                label="📥 Télécharger les données",
                data=output.getvalue(),
                file_name=f"nps_data_{period}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

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