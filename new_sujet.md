MSPR TPRE622 – ObRail Europe
Développement d’un modèle d’apprentissage répondant au besoin d’une solution IA

====================================================
CONTEXTE
====================================================

ObRail Europe est un observatoire spécialisé dans le ferroviaire et la mobilité durable.

Mission :
- Collecter et analyser les données ferroviaires européennes.
- Évaluer l’impact environnemental des transports.
- Produire des études comparatives.
- Promouvoir le train comme alternative à l’avion.

Partenaires :
- Commission Européenne
- Parlement Européen
- SNCF
- DB
- ÖBB Nightjet
- Trenitalia
- ONG environnementales

Objectif du projet :
Créer un référentiel de données harmonisé permettant :
- L’analyse de la couverture ferroviaire.
- L’entraînement de modèles d’IA.
- Le développement d’un service applicatif.

Contraintes :

1. Dispersion des données
- CSV
- GTFS
- API
- Excel
- HTML Scraping

2. Qualité des données
- Doublons
- Valeurs manquantes
- Incohérences

3. Standardisation
- Formats différents selon les pays

4. RGPD
- Transparence
- Documentation
- Sécurité

5. Délais
- Première version avant la fin de l’année.

====================================================
ENJEUX MÉTIERS
====================================================

Choisir au moins un axe :

1. Prévoir la fréquentation des lignes ferroviaires.
2. Estimer les émissions futures de CO2.
3. Détecter les zones sous-desservies.
4. Prévoir la congestion des lignes.
5. Identifier les lignes pouvant remplacer l’avion.
6. Identifier les lignes à fort potentiel.

====================================================
CONTRAINTES TECHNIQUES
====================================================

Le projet doit :

- Comparer plusieurs solutions IA.
- Être reproductible.
- Être documenté.
- Respecter les bonnes pratiques Data Science.
- Utiliser un workflow complet :
  * Exploration
  * Préparation
  * Entraînement
  * Évaluation
  * Sélection
  * Sauvegarde

Le modèle doit être exportable :
- Pickle
- Joblib

Une API de prédiction doit être proposée.

====================================================
BESOINS À RÉALISER
====================================================

1. Analyse exploratoire

- Étudier les données.
- Détecter les anomalies.
- Nettoyer les données.
- Réaliser le Feature Engineering.
- Construire les jeux :
  * Train
  * Validation
  * Test

Livrable :
- Notebook d’analyse.
- Tableau des variables.

----------------------------------------------------

2. Environnement de développement

Exemples :
- Python
- Scikit-Learn
- TensorFlow
- PyTorch

Livrable :
- Structure du projet.
- requirements.txt

----------------------------------------------------

3. Développement de modèles

Tester plusieurs modèles :

- Régression Linéaire
- Random Forest
- XGBoost
- LightGBM
- Réseau de neurones (MLP)

Livrable :
- Scripts d’entraînement.
- Tableau comparatif.

----------------------------------------------------

4. Entraînement et optimisation

- GridSearch
- RandomSearch
- Cross Validation

Livrable :
- Rapport d’évaluation.
- Visualisations.

----------------------------------------------------

5. API REST

Créer une API avec :

- FastAPI
ou
- Flask

Route obligatoire :

POST /predict

Livrable :
- API fonctionnelle.

----------------------------------------------------

6. Benchmark IA

Comparer au moins 3 services :

- AWS SageMaker
- Azure Machine Learning
- Google Vertex AI
- HuggingFace AutoTrain
- IBM Watson AutoAI

Comparer :
- Prix
- Performances
- Facilité d’intégration
- Explicabilité

Livrable :
- Tableau comparatif.
- Recommandations.

----------------------------------------------------

7. Reproductibilité

- Sauvegarde du modèle.
- Script predict.py.
- Documentation de ré-entraînement.

Livrable :
- Modèle final.
- Documentation.

----------------------------------------------------

8. Veille

- Veille technologique IA.
- Veille réglementaire.
- Veille éthique.

Livrable :
- Recommandations.
- Synthèse.

----------------------------------------------------

9. Rapport et soutenance

Rapport complet contenant :

- Données
- Architecture
- Méthodologie
- Résultats
- Limites
- Perspectives

Livrable :
- Rapport final.
- Support PowerPoint.

====================================================
LIVRABLES FINAUX
====================================================

1. Notebook d’analyse.
2. Tableau des variables.
3. requirements.txt.
4. Scripts d’entraînement.
5. Tableau comparatif des modèles.
6. Rapport d’évaluation.
7. API REST.
8. Benchmark IA.
9. Modèle sauvegardé.
10. Script predict.py.
11. Documentation.
12. Veille technologique.
13. Rapport technique complet.
14. Support de soutenance.

====================================================
TECHNOLOGIES RECOMMANDÉES
====================================================

Langage :
- Python

Bibliothèques :
- NumPy
- Pandas
- Scikit-Learn
- XGBoost
- LightGBM
- TensorFlow
- PyTorch

Visualisation :
- Matplotlib
- Seaborn
- Plotly

Dashboard (optionnel) :
- Streamlit
- Dash

Sauvegarde :
- Pickle
- Joblib

====================================================
ORGANISATION
====================================================

Équipe :
- 4 étudiants (5 maximum)

Préparation :
- 29 heures

Soutenance :
- 20 min présentation
- 30 min questions jury

Durée totale :
- 50 minutes