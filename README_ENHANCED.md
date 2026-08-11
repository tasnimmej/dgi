Projet DGI - Version améliorée
================================

But: Ce dépôt est une copie améliorée du projet original `projet_dgi_ia`. Il conserve tout le travail existant et sert de base pour implémenter les fonctionnalités nécessaires pour une PME en Tunisie.

Fonctionnalités implémentées (sommaire)
- Authentification (FastAPI + JWT) : endpoints /auth/register, /auth/login, /auth/me
- Frontend (React + Vite) : pages login et register, routage basique
- Import CSV et enregistrement des factures
- OCR pour factures (endpoint /invoices/upload-invoice) utilisant pytesseract
- Génération PDF de la déclaration (adaptée aux libellés tunisiens)
- Scheduler (APScheduler) pour vérifier les échéances (timezone Africa/Tunis)
- Tests unitaires basiques pour le calcul de TVA

Arborescence importante
- app/ : code backend (models, services, routes, auth)
- frontend/ : application React (Vite)
- requirements.txt : dépendances Python
- tests/ : tests unitaires

Exécution locale (raccourci)
1) Backend
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   # Assurez-vous de configurer la base PostgreSQL et la variable d'environnement si nécessaire
   uvicorn main:app --reload

2) Frontend
   cd frontend
   npm install
   npm run dev

Notes et recommandations
- Remplacer SECRET_KEY (app/auth.py) par une valeur sécurisée en production.
- Installer Tesseract OCR sur la machine pour que pytesseract fonctionne correctement.
- Préparer les migrations Alembic (non inclus automatiquement) :
   alembic init alembic
   # configurer alembic/env.py pour target_metadata = app.database.Base.metadata
   alembic revision --autogenerate -m "Initial"
   alembic upgrade head

Prochaines améliorations (prioritaires)
1) Améliorer les templates OCR pour couvrir différents formats de factures tunisiennes
2) Adapter précisément le PDF de déclaration pour correspondre au formulaire officiel de la Recette des Finances tunisienne
3) Ajouter export/impression et signature numérique si requis
4) Intégrer service SMS (Twilio) et/ou SendGrid pour notifications de rappel
5) Ajouter pipeline CI et déploiement

Si vous voulez, je peux :
- Générer les fichiers Alembic de base pour ce dépôt (préparer env.py)
- Ajouter l'upload d'images côté frontend et une page pour valider/éditer les données OCR
- Adapter davantage le PDF pour qu'il corresponde trait pour trait au formulaire officiel (si vous fournissez une version PDF/jpg du formulaire)

