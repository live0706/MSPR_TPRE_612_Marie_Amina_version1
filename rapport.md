# Rapport detaille du projet ObRail

Ce rapport explique le fonctionnement du projet, les sources de donnees choisies, et les raisons pour lesquelles certaines donnees affichent des valeurs manquantes ou faibles.

## 1) Fonctionnement general du projet

Le projet suit un pipeline ETL classique en 3 etapes :

1. Decouverte des sources
   - Le script `etl/discover.py` genere un fichier `etl/sources.json`.
   - Les sources sont composees de :
     - une source "toujours presente" (Wikipedia),
     - des sources statiques definies dans `etl/sources_static.json`,
     - des sources dynamiques (OpenDataSoft et Transitland) si l'acces reseau est autorise.

2. Extraction
   - Le script `etl/extract.py` telecharge les fichiers source (HTML, CSV, JSON, GTFS .zip) puis les parse.
   - Chaque source est stockee dans `data/raw`.

3. Transformation
   - Le script `etl/transform.py` normalise les colonnes, nettoie les donnees, convertit les heures, et calcule le CO2 si manquant.
   - Un filtre retire les lignes dont `distance_km` est manquante, afin d'eviter des enregistrements incomplets.

4. Chargement
   - Le script `etl/load.py` charge les donnees dans PostgreSQL.
   - En local, il faut fournir la variable `DATABASE_URL`.
   - En Docker, cette variable est fournie par le fichier `.env`.

5. API et dashboard
   - L'API expose les donnees depuis PostgreSQL.
   - Le dashboard interroge l'API pour afficher les indicateurs.

## 2) Sources choisies et rationale

Les sources sont parametrees dans `etl/sources_static.json`. Actuellement :

- Back-on-Track (Open Night Train DB)
  - Format : CSV
  - Avantage : fournit horaires de depart/arrivee, pays, et distance.
  - Limite : certaines lignes contiennent des valeurs manquantes ou des cellules "N/A".

- Wikipedia (Named passenger trains of Europe)
  - Format : HTML
  - Avantage : permet d'avoir des exemples stables et faciles a parser.
  - Limite : ne fournit pas d'horaires ni de distances fiables. Les lignes sont souvent filtrees si `distance_km` est absente.

- GTFS (transport public)
  - Des feeds GTFS peuvent etre ajoutes pour augmenter le volume.
  - Les routes non ferroviaires (bus, tram, metro) sont filtrees.

## 3) Pourquoi certaines donnees sont faibles ou manquantes

Les donnees peuvent paraitre "faibles" ou "incompletes" pour plusieurs raisons :

1. Acces reseau bloque
   - Si le poste bloque HTTPS, les sources distantes ne sont pas telechargees.
   - Le pipeline retombe alors sur Wikipedia uniquement, donc volume tres faible.

2. Filtrage sur `distance_km`
   - Les lignes sans distance sont retirees pour garantir une qualite minimale.
   - Wikipedia est quasi entierement filtree pour cette raison.

3. Variations de structure entre sources
   - Les colonnes n'ont pas toujours les memes noms.
   - Le mapping corrige ces differences, mais certaines sources restent partielles.

4. Donnees manquantes a l'origine
   - Certains CSV contiennent des cellules vides ou des marqueurs `#N/A`.
   - Ces valeurs sont nettoyees et peuvent entrainer le rejet des lignes.

## 4) Impact sur le dashboard

Le dashboard n'affiche des donnees que si :
1. Le pipeline ETL a reussi.
2. Les donnees ont ete chargees dans PostgreSQL.
3. L'API est disponible et connectee a la base.

Si `DATABASE_URL` est absent en local, le chargement echoue et le dashboard reste vide.

## 5) Commandes utiles

Relancer le pipeline complet en Docker :
```
docker compose up -d db
docker compose run --rm etl
docker compose up -d api dashboard
```

Relancer en local :
```
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/obrail"
python .\\etl\\main_etl.py
```

## 6) Recommandations

- Ajouter des feeds GTFS ferroviaires fiables pour augmenter le volume.
- Verifier que l'acces HTTPS n'est pas bloque.
- Garder le filtre `distance_km` pour eviter les enregistrements incomplets.
- Surveiller `data/processed/quality_report.json` pour mesurer la qualite.
