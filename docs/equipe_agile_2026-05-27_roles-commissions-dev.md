# Equipe agile - roles et commissions

Date: 2026-05-27.

## BOT-START

Roadmap: `RM-2026-0026` / `RM-2026-0033`.
Chantier: `CH-20260527-171100-RM-2026-0026-acces-roles-commissions`.
Conversation: `CONV-2026-1791`.
Role: owner code unique front/back/viewmodel `ORD-P2-040`.

Mission: livrer une surface locale pour relire roles, commissions, referents,
productions et droits par ressource.

Ownership modifiable: `roles_commissions_view.py`, `roles_commissions.html`,
navigation `base.html`, `feature_routes.py`, `styles.css`, `styles_part_26.css`,
tests UI/smoke/securite/anti-fuite et registres gouvernail.

Fichiers evites: instances privees, documents bruts, OCR/logs, exports bruts,
secrets, profils reels, annuaire coproprietaires, invitation ou revocation
reelle, droits appliques, serveurs non reserves, scans/kills, push GitHub,
`RM-2026-0017`, `ORD-P0-990`.

## Livraison

Route livree: `/gouvernance/roles-commissions`.

La page affiche uniquement des donnees FICTIVES:

- profils synthetiques;
- commissions travaux, finances et communication;
- referents et productions attendues;
- matrice de droits par ressource;
- gates de validation humaine;
- actions sensibles bloquees.

Aucun droit n'est applique. Aucune invitation, revocation, publication, export
d'annuaire ou diffusion large n'est declenche.

## Preuves

Commandes executees depuis le repo principal:

```powershell
cd server
.\.venv\Scripts\python.exe -B -m unittest tests.test_ui_roles_commissions tests.test_ui_smoke_routes_expanded tests.test_ui_security_routes tests.test_security_no_private_sync_leaks -v
```

Resultat: 21 tests OK.

```powershell
.\server\.venv\Scripts\python.exe .\tools\check_code_line_limit.py
```

Resultat: OK, aucun fichier code suivi ne depasse 600 lignes.

Limite: pas de recette navigateur live ni capture, car aucun serveur reserve ne
devait etre lance.
