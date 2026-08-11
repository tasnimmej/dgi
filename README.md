Projet DGI - Version améliorée
================================

But: Ce dépôt est une copie améliorée du projet original `projet_dgi_ia`. Il conserve tout le travail existant et servira de base pour implémenter les cycles suivants :

Cycles (itérations)
1) Authentification et gestion des sociétés (FastAPI + JWT, tables users/companies, pages React login/signup)
2) Frontend réactif (routes, dashboard, gestion factures / déclarations)
3) Templates de factures tunisiennes + OCR (pytesseract) pour extraction automatique
4) Génération de la déclaration conforme à la Recette des Finances tunisienne et export PDF
5) Scheduler (APScheduler) + notifications (email/SMS) et vérification des échéances
6) Tests, migrations Alembic, documentation et packaging

Emplacement des fichiers copiés : le contenu original est dans ce dossier. Les dépendances (venv, node_modules) ne sont pas copiées.

Prochaine étape : implémenter la première itération (auth) — confirmez pour démarrer.
