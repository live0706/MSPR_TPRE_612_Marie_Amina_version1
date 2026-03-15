# Plan de presentation (soutenance) - detail par slide

## Slide 1 - Titre et contexte
Objectif : introduire ObRail Europe et la mission.
Messages clefs : besoin d un ETL ferroviaire europeen, exploitation data/IA.
Preuve/demo : rappel du cahier des charges (road_map.txt).

## Slide 2 - Objectifs et livrables
Objectif : cadrer les 7 livrables attendus.
Messages clefs : ETL, MCD/MPD, base alimentee, API, doc, dashboard, soutenance.
Preuve/demo : tableau de conformite.

## Slide 3 - Sources de donnees
Objectif : justifier les sources retenues.
Messages clefs : Back-on-Track + Wikipedia, GTFS rail possible, Transitland optionnel.
Preuve/demo : `etl/sources_static.json`.

## Slide 4 - Architecture technique
Objectif : montrer la stack.
Messages clefs : Python, PostgreSQL, FastAPI, Streamlit, Docker Compose.
Preuve/demo : `docker-compose.yml`.

## Slide 5 - Pipeline ETL
Objectif : expliquer les etapes.
Messages clefs : decouverte, extraction, transformation, chargement.
Preuve/demo : diagramme simple + scripts `etl/`.

## Slide 6 - Nettoyage et regles metier
Objectif : expliquer les regles.
Messages clefs : normalisation colonnes, filtrage rail, filtrage distance_km, calcul CO2.
Preuve/demo : extrait `etl/transform.py`.

## Slide 7 - Modele de donnees
Objectif : presenter MCD/MPD.
Messages clefs : entite Trip, attributs principaux, table `trips`.
Preuve/demo : `docs/mcd.md` + `database/init.sql`.

## Slide 8 - Base de donnees alimentee
Objectif : montrer l alimentation.
Messages clefs : ETL charge PostgreSQL via `DATABASE_URL`.
Preuve/demo : commandes Docker.

## Slide 9 - API REST
Objectif : montrer l acces aux donnees.
Messages clefs : endpoints `/trains`, `/stats`, pagination.
Preuve/demo : exemple de requete.

## Slide 10 - Dashboard
Objectif : visualiser la qualite et les indicateurs.
Messages clefs : KPIs, Jour/Nuit, top operateurs, qualite CO2.
Preuve/demo : capture ou demo Streamlit.

## Slide 11 - Resultats et qualite
Objectif : donner les chiffres.
Messages clefs : 352 lignes, Jour 290, Nuit 62, zero manquants.
Preuve/demo : `quality_report.json`.

## Slide 12 - Difficultes et solutions
Objectif : transparence.
Messages clefs : acces reseau, sources heterogenes, filtrage rail.
Preuve/demo : logs et choix techniques.

## Slide 13 - Limites et perspectives
Objectif : ouvrir sur la suite.
Messages clefs : feeds GTFS rail, tests automatises, diagrammes MCD/MPD graphiques.
Preuve/demo : backlog d amelioration.

## Slide 14 - Conclusion
Objectif : synthese.
Messages clefs : livrables OK/Partiel, prochaines actions.
Preuve/demo : tableau final de conformite.
