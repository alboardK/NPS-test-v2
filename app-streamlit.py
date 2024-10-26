import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

# Configuration de la page Streamlit
st.set_page_config(page_title="Annette K. - Dashboard NPS", layout="wide")

# Styles CSS personnalisés
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #E6EEF0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #1A374D;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Fonction pour lister les fichiers CSV disponibles
def get_available_files():
    files = [f for f in os.listdir("data") if f.endswith('.csv') and os.path.isfile(os.path.join("data", f))]
    return files

# Fonction pour charger les données
@st.cache_data
def load_data(filename):
    df = pd.read_csv(f"data/{filename}")
    df['Horodateur'] = pd.to_datetime(df['Horodateur'], format='%d/%m/%Y %H:%M:%S')
    df['Month'] = df['Horodateur'].dt.strftime('%Y-%m')
    
    # Gestion des noms complets
    df['Nom_Complet'] = df['Votre Nom'].fillna('') + ' ' + df['Votre prénom'].fillna('')
    df['Nom_Complet'] = df['Nom_Complet'].str.strip()
    return df

# Layout du sélecteur de fichier
col1, col2, col3 = st.columns([2,2,1])
with col3:
    available_files = get_available_files()
    selected_file = st.selectbox(
        "Sélectionner la source de données",
        available_files,
        index=0 if available_files else None
    )

# Chargement des données
if selected_file:
    try:
        df = load_data(selected_file)
        
        # Création des onglets principaux
        tab1, tab2 = st.tabs(["Dashboard Général", "Retours Clients"])
        
        with tab1:
            # Section Dashboard Général
            st.subheader("🏊‍♂️ Annette K. - Indicateurs clés")
            
            # Fonction pour calculer le NPS
            def calculate_nps(scores):
                promoters = sum(scores >= 9)
                detractors = sum(scores <= 6)
                total = len(scores)
                return ((promoters - detractors) / total) * 100 if total > 0 else 0

            # Trouver la colonne NPS
            nps_column = [col for col in df.columns if 'Recommandation' in col][0]
            retention_column = [col for col in df.columns if 'probabilité' in col][0]

            # Métriques principales avec nouveau design
            metrics_cols = st.columns(3)
            with metrics_cols[0]:
                nps_score = calculate_nps(df[nps_column].dropna())
                st.markdown(f"""
                <div class="metric-card">
                    <h3>NPS Score</h3>
                    <h2>{nps_score:.1f}%</h2>
                </div>
                """, unsafe_allow_html=True)

            with metrics_cols[1]:
                retention_score = df[retention_column].mean()
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Score de Rétention Moyen</h3>
                    <h2>{retention_score:.1f}/10</h2>
                </div>
                """, unsafe_allow_html=True)

            with metrics_cols[2]:
                responses_count = len(df)
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Nombre de Réponses</h3>
                    <h2>{responses_count}</h2>
                </div>
                """, unsafe_allow_html=True)

            # Graphique de répartition amélioré
            st.subheader("Répartition mensuelle des répondants")
            def get_nps_category(score):
                if pd.isna(score):
                    return 'Non renseigné'
                if score >= 9:
                    return 'Promoteurs'
                elif score <= 6:
                    return 'Détracteurs'
                else:
                    return 'Neutres'

            df['NPS_Category'] = df[nps_column].apply(get_nps_category)
            monthly_volumes = pd.DataFrame(df.groupby(['Month', 'NPS_Category']).size()).reset_index()
            monthly_volumes.columns = ['Month', 'NPS_Category', 'count']

            # Limite à 12 mois et tri inverse
            unique_months = sorted(monthly_volumes['Month'].unique(), reverse=True)[:12]
            monthly_volumes = monthly_volumes[monthly_volumes['Month'].isin(unique_months)]

            fig_volumes = px.bar(monthly_volumes,
                               x='Month',
                               y='count',
                               color='NPS_Category',
                               title="Répartition mensuelle des répondants",
                               labels={'count': 'Nombre de répondants',
                                     'Month': 'Mois',
                                     'NPS_Category': 'Catégorie'},
                               category_orders={'NPS_Category': ['Détracteurs', 'Neutres', 'Promoteurs']},
                               color_discrete_map={'Promoteurs': '#6B9080',
                                                 'Neutres': '#A4C3B2',
                                                 'Détracteurs': '#CCE3DE'})

            fig_volumes.update_layout(
                barmode='stack',
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=500
            )

            st.plotly_chart(fig_volumes, use_container_width=True)

        with tab2:
            # Section Retours Clients
            col_filters1, col_filters2 = st.columns([1,1])
            
            with col_filters1:
                date_filter = st.date_input(
                    "Filtrer par date",
                    value=(df['Horodateur'].min(), df['Horodateur'].max())
                )
            
            with col_filters2:
                category_filter = st.multiselect(
                    "Filtrer par catégorie",
                    ['Promoteurs', 'Neutres', 'Détracteurs'],
                    default=['Promoteurs', 'Neutres', 'Détracteurs']
                )

            # Liste des retours filtrée
            filtered_df = df[
                (df['Horodateur'].dt.date >= date_filter[0]) &
                (df['Horodateur'].dt.date <= date_filter[1]) &
                (df['NPS_Category'].isin(category_filter))
            ]

            # Affichage des retours
            st.markdown("### Derniers retours")
            for _, row in filtered_df.iterrows():
                with st.expander(f"{row['Nom_Complet']} - {row['Horodateur'].strftime('%d/%m/%Y')} - NPS: {row[nps_column]}"):
                    col1, col2 = st.columns([1,1])
                    with col1:
                        st.markdown("**Informations personnelles**")
                        st.write(f"Nom: {row['Votre Nom']}")
                        st.write(f"Prénom: {row['Votre prénom']}")
                        st.write(f"Date: {row['Horodateur'].strftime('%d/%m/%Y %H:%M')}")
                    
                    with col2:
                        st.markdown("**Scores**")
                        st.write(f"NPS: {row[nps_column]}")
                        st.write(f"Probabilité de réabonnement: {row[retention_column]}")
                    
                    # Notes détaillées
                    st.markdown("**Notes détaillées**")
                    satisfaction_cols = [col for col in df.columns if "sur une echelle de 1 à 5" in col.lower()]
                    for col in satisfaction_cols:
                        clean_name = col.lower().replace("sur une echelle de 1 à 5, 1 etant la pire note et 5 la meilleure, notez votre satisfaction concernant ", "")
                        st.write(f"{clean_name}: {row[col]}/5")

    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
else:
    st.error("Aucun fichier CSV trouvé dans le dossier data/")
