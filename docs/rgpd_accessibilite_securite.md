# RGPD, accessibilite, securite

## RGPD

- les donnees manipulees sont ferroviaires et non personnelles
- aucune donnee voyageur nominative n'est exposee
- les journaux applicatifs centralises dans Loki ne doivent pas contenir d'information sensible
- les mots de passe et secrets transitent par variables d'environnement

## Accessibilite

- interface React avec contrastes lisibles, composants natifs et navigation clavier
- navigation simple par sections et filtres explicites
- vocabulaire metier stable pour la soutenance
- pages et boutons identifies par des libelles clairs
- retours d'etat visuels explicites sur la sante API et la selection de trajet

## Securite

- validation Pydantic et `Query` sur les entrees utilisateur
- requetes SQL parametrees
- en-tetes de securite HTTP de base
- CORS configurable
- rotation des logs applicatifs avec `RotatingFileHandler`
- aucun secret stocke dans le depot

## Recommandations complementaires

- restreindre `CORS_ORIGINS` en production
- ajouter un reverse proxy HTTPS
- activer l'authentification Grafana
- separer les bases `dev`, `test`, `prod`
