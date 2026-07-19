# Démo autonome (offline, sans backend)

Génère une unique page HTML auto-contenue (données + polices embarquées en
base64) pour partager ou consulter l'application sans faire tourner
FastAPI/Next.js. Utilisée pour publier une démo consultable depuis un
navigateur ou un mobile sans installation.

## Régénérer la démo

```bash
# 1. Exporter les données réelles depuis la base SQLite (nécessite le backend
#    déjà peuplé, voir backend/README ou le README racine)
cd ../backend && source venv/bin/activate
PYTHONPATH=. python scripts/export_static_data.py ../artifact/static_data_raw.json
cd ../artifact

# 2. Réduire la taille (limite à ~400 joueurs, retire les remplaçants à 0 minute)
python trim_data.py static_data_raw.json static_data.json

# 3. Injecter polices + données dans le template et produire le HTML final
#    Polices attendues (OFL, à récupérer sur Google Fonts) : Big Shoulders (bold),
#    Work Sans (regular+bold), Red Hat Mono (regular)
FONT_DIR=/path/to/fonts python build.py static_data.json football_demo.html
```

`football_demo.html` (~2-3 Mo) n'est pas versionné (voir `.gitignore`) : c'est
un artefact généré, pas du code source. `template.html` contient le HTML/CSS/JS
source (aucune dépendance externe, tout le rendu — carte de tirs, radar de
comparaison — est fait en SVG/canvas vanilla JS).

## Portée

Contrairement à l'app complète (backend + frontend), cette démo n'a pas de
recherche live sur toute la base ni de mise à jour des données : tout est figé
au moment de l'export. Elle couvre les mêmes deux compétitions à données
détaillées (Coupe du Monde 2022, Euro 2024) et les classements des 5 grands
championnats.
