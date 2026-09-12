# Projet ML Trading — corrections de cohérence

## 🔴 Bug bloquant corrigé : le backend ne démarrait pas
`data/collector.py` contenait :
```python
def validate_data (self, df : pd.Dataframe) :
```
`pd.Dataframe` n'existe pas dans pandas (bon nom : `pd.DataFrame`). Comme les
annotations de type sont évaluées **au moment où Python lit la fonction**
(pas seulement à l'appel), le simple fait d'importer `collector.py` levait :
```
AttributeError: module 'pandas' has no attribute 'Dataframe'
```
Et comme `main.py` fait `from data.collector import DataCollection` dès le
démarrage, **toute l'API plantait avant même de recevoir une requête**.
→ Corrigé.

## 🔴 Bug silencieux corrigé : mauvaises dates sur le graphique "Price Evolution"
Dans `/api/data-analysis` (main.py), l'ordre des opérations était :
1. `features.add_features()` → ajoute une colonne `Date`
2. `features.clean()` → fait `select_dtypes(include=[np.number])`, ce qui
   **supprime la colonne `Date`** (elle n'est pas numérique)
3. Le code cherchait ensuite `'Date'` dans les colonnes pour construire le
   graphique... et ne la trouvait plus. Le code de secours finissait par
   interpréter la première colonne numérique restante (ex: `Weekdays`,
   valeurs 0 à 6) comme une date avec `pd.to_datetime()`, produisant des
   dates aberrantes (autour de 1970).

Tu avais déjà correctement géré ce problème dans `/api/run-backtest`
(sauvegarder les dates avant `clean()`, puis les réaligner sur l'index
restant) — la même logique manquait juste dans `/api/data-analysis`.
→ Corrigé et testé (voir plus bas).

## 🟠 Structure de fichiers corrigée
`main.py` importe `from data.collector import ...`, `from features.features
import ...`, `from models.optimizer import ...`, etc. — ça suppose une
organisation en **packages Python**. Les fichiers uploadés étaient tous à
plat. J'ai recréé l'arborescence attendue avec des `__init__.py` :

```
backend/
├── main.py
├── requirements.txt
├── data/
│   ├── __init__.py
│   ├── collector.py      (corrigé : pd.DataFrame)
│   └── storage.py
├── features/
│   ├── __init__.py
│   ├── features.py
│   ├── alpha_generator.py
│   ├── alpha_primitive.py
│   └── selection.py
└── models/
    ├── __init__.py
    ├── optimizer.py
    ├── classifiers.py    (nettoyé, voir ci-dessous)
    ├── backtest.py        ⚠ non utilisé par l'API, voir note
    └── time_series.py     ⚠ non utilisé par l'API, voir note

frontend/
├── package.json
└── src/
    ├── App.jsx
    ├── config.js          (nouveau : URL de l'API centralisée)
    └── components/
        ├── utils.jsx
        ├── Menu.jsx
        ├── Data.jsx
        ├── Alpha.jsx
        ├── Optimization.jsx
        └── Backtest.jsx
```

J'ai vérifié que `main.py` s'importe désormais sans erreur et que toutes les
routes sont bien enregistrées (`/api/data-analysis`, `/api/enrich-dataset`,
`/api/optimize-model`, `/api/run-backtest`, etc.).

## 🟡 Autres incohérences corrigées

- **`classifiers.py`** importait `statsmodels`, `pmdarima`, `matplotlib`
  sans jamais les utiliser — ça obligeait à installer ces librairies rien
  que pour charger le module (importé par `main.py`). Imports supprimés.
- **`main.py`** importait `Classifiers` sans jamais l'utiliser (import mort)
  — supprimé.
- **URLs d'API incohérentes côté frontend** : `Alpha.jsx` appelait
  `http://127.0.0.1:8000`, les autres composants `http://localhost:8000`.
  Ça marchait quand même grâce à `allow_origins=["*"]`, mais j'ai centralisé
  tout ça dans `src/config.js` (`API_BASE_URL`).
- **`collector.py`** importait `ABC`/`abstractmethod` sans les utiliser
  (la classe n'était pas abstraite) — retiré pour éviter toute confusion.

## ⚠️ Points restants à ta décision (pas corrigés, car ambigus)

- **`backtest.py` (classe `Backtester`) n'est jamais appelée** par `main.py` :
  la route `/api/run-backtest` réimplémente sa propre logique de backtest à
  la main. Le fichier est donc du code mort actuellement. Je l'ai gardé dans
  `models/backtest.py` au cas où tu voudrais un jour refactoriser
  `main.py` pour l'utiliser, mais dans l'état ce n'est pas branché.
- **`time_series.py`** (classe `ARIMA`) n'est importé nulle part non plus —
  gardé tel quel, considère-le comme un script expérimental à part.
- **`dashboard.jsx` et `effects.jsx`** (dans tes fichiers uploadés) sont
  vides (0 octet) et ne sont importés par aucun autre composant — je ne les
  ai pas repris dans l'arborescence corrigée. Si tu comptais y mettre du
  code, il faudra le réécrire.
- **`App.jsx`** utilise une classe CSS `blob-gpu` qui n'est définie dans
  aucun des fichiers fournis (probablement dans un `index.css` global non
  uploadé). Il te faudra la fournir avec les directives Tailwind
  (`@tailwind base/components/utilities`) pour que le build fonctionne.
- Le frontend n'avait pas de `package.json`/config de build (Vite, Tailwind
  config, `index.html`) dans les fichiers fournis — j'ai ajouté un
  `package.json` minimal, mais il te manque encore `vite.config.js`,
  `tailwind.config.js` et `index.html` pour que `npm run dev` fonctionne
  telle quelle.

## Lancer le projet

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend** (une fois les fichiers de config Vite/Tailwind ajoutés)
```bash
cd frontend
npm install
npm run dev
```
