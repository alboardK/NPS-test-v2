# NPS Test V2 - Annette K.

Dashboard de visualisation NPS pour Annette K. Version 2.0 avec interface améliorée.

## Fonctionnalités

- Dashboard général avec KPIs et visualisations
- Système de suivi des retours clients
- Filtrage des données par date et catégorie
- Design inspiré de la charte graphique Annette K.
- Interface responsive et moderne

## Installation

1. Cloner le repository :
```bash
git clone https://github.com/[votre-username]/nps-test-v2.git
cd nps-test-v2
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Placer vos fichiers de données CSV dans le dossier `data/`

4. Lancer l'application :
```bash
streamlit run app.py
```

## Structure des données

Le dashboard attend des fichiers CSV avec les colonnes suivantes :
- Horodateur
- Recommandation (NPS)
- Probabilité de réabonnement
- Notes de satisfaction par catégorie
- Commentaires
- Informations clients

## Déploiement

L'application est configurée pour être déployée sur Streamlit Cloud.

## Configuration

Les paramètres de l'application peuvent être modifiés dans le fichier `.streamlit/config.toml`

## Contributing

Les pull requests sont bienvenues. Pour des changements majeurs, merci d'ouvrir une issue d'abord.
