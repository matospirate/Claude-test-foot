# FootballStats — analytics football sur données réelles

Application web (backend FastAPI + frontend Next.js) construite sur des
**données réelles et ouvertes**, sans donnée inventée. Aucune clé API n'est
requise.

## Sources de données

| Source | Contenu | Licence | Portée dans l'app |
|---|---|---|---|
| [openfootball/football.json](https://github.com/openfootball/football.json) | Résultats/calendriers réels | Domaine public / open data communautaire | Classements & résultats des 5 grands championnats (Premier League, Liga, Serie A, Bundesliga, Ligue 1), saisons 2024-25 et 2025-26 |
| [StatsBomb open-data](https://github.com/statsbomb/open-data) | Données événement par événement (tirs avec xG StatsBomb, passes, dribbles, tacles, pressings, compositions avec minutes exactes) | CC BY-NC-SA 4.0 — usage non commercial, attribution requise | Coupe du Monde 2022 (64 matchs) et Euro 2024 (51 matchs), avec joueurs, équipes, tirs, stats par match/joueur/équipe |

Le pipeline d'ingestion (`backend/app/ingestion/`) est générique : n'importe
quelle autre compétition/saison présente dans `competitions.json` de
StatsBomb (Bundesliga 2023/24, La Liga 2020/21 - dernière saison de Messi au
Barça, Ligue 1 2022/23, etc.) peut être ajoutée en une ligne dans
`backend/scripts/run_ingestion.py`.

## Ce qui est réellement implémenté (par rapport au cahier des charges initial)

- **Module 1 (Joueur)** : stats standard, xG/xA, tirs qualifiés (pied/tête,
  technique, contexte), passes (progressives, clés, centres, passes
  cassant les lignes), dribbles, courses progressives, actions défensives
  (tacles, interceptions, dégagements, pressings), cartes, minutes exactes
  par match (calculées depuis les données de composition StatsBomb, pas
  estimées).
- **Module 2 (Équipe)** : classements réels, PPDA (intensité du pressing,
  calculé directement depuis les événements, pas une valeur factice),
  possession, historique de matchs.
- **Module 3 (Match)** : score, tirs des deux équipes, compositions avec
  minutes exactes, buts avec minute/xG. **Hors scope** : météo, affluence,
  état de la pelouse, statistiques d'arbitrage, VAR, temps de jeu effectif —
  aucune source gratuite fiable disponible pour ces données.
- **Module 4 (Dataviz)** : cartes de tirs (position réelle x/y, taille = xG,
  couleur = issue du tir), radar de comparaison de joueurs (métriques
  ramenées par 90 minutes), réseaux de passes agrégés par match (données
  calculées et exposées via l'API `/api/matches/{id}/pass-network`, à
  brancher sur un composant de visualisation si besoin).
- **Modules 5, 6, 7** (scouting B2B, paris/fantasy, comparateur
  inter-générations) : **non implémentés**. Ils reposent sur des données
  propriétaires (valeur marchande, contrats, historique médical, cotes de
  paris, tracking GPS) qui n'ont pas de source gratuite et légale
  accessible sans clé API commerciale, et le sandbox de développement
  utilisé pour cette session bloque par ailleurs l'accès réseau sortant
  vers des sites comme Transfermarkt, Sofascore ou Understat.

## Pourquoi pas de scraping de Transfermarkt/Sofascore/Understat ?

Deux raisons : (1) le réseau de l'environnement de développement utilisé
pour construire cette version bloque les requêtes sortantes vers ces domaines
(seul GitHub était accessible) ; (2) ces sites ont des conditions
d'utilisation qui interdisent explicitement le scraping automatisé. StatsBomb
open-data et openfootball sont au contraire publiés explicitement pour un
usage public/recherche.

## Architecture

```
backend/            FastAPI + SQLAlchemy + SQLite
  app/
    core/            config
    db/               session, init
    models/           schéma SQLAlchemy (Team, Player, Match, Shot,
                       PlayerMatchStat, TeamMatchStat, Standing, ...)
    ingestion/        statsbomb_ingest.py, openfootball_ingest.py
    api/routers/      leagues, competitions, players, teams, matches,
                       compare, search
  scripts/run_ingestion.py   point d'entrée pour (re)peupler la base

frontend/            Next.js (App Router) + TypeScript + Tailwind + Recharts
  app/               pages : accueil, ligues, compétitions, joueurs,
                       équipes, matchs, comparateur
  components/        ShotMap (SVG), PlayerRadar (recharts), SearchBar
  lib/api.ts          client HTTP typé vers le backend
```

## Lancer le projet

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python scripts/run_ingestion.py   # peuple la base (quelques minutes)
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Puis ouvrir http://localhost:3000.

## Ajouter d'autres compétitions StatsBomb

Éditer `backend/scripts/run_ingestion.py`, ajouter un tuple
`(competition_id, season_id, "Nom")` à `STATSBOMB_TARGETS` (voir la liste
complète dans `competitions.json` du dépôt StatsBomb open-data), puis
relancer le script — les matchs déjà ingérés ne sont pas retéléchargés.
