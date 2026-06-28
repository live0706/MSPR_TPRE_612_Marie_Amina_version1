# TPRE622 - Modele IA CO2

Sous-projet Machine Learning pour predire les emissions de CO2 d'un trajet ferroviaire ObRail.

## Entrainement

```powershell
python -m pip install -r requirements.txt
python ml/train.py --dataset data/processed/trips_cleaned_final.csv
```

Artefacts produits :

- `ml/models/co2_emissions_model.joblib`
- `data/processed/co2_emissions_model.joblib` pour l'API
- `ml/reports/model_comparison.csv`
- `ml/reports/evaluation_report.json`
- `ml/reports/model_rmse_comparison.png`

## Prediction CLI

```powershell
python ml/predict.py --input-json ml/sample_prediction.json
```

## API

L'API FastAPI expose `POST /predict` lorsque le modele exporte est disponible.
