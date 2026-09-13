# Tests utilisateur - actions comptes

Date: 2026-06-02
Lot: CONV-2026-2076
Worktree: coproscope-actions-compta-tests-utilisateur-20260602

## Scenario metier

Un membre du conseil syndical voit une anomalie comptable et veut la transformer
en action humaine: question a poser, preuve a relire, trace a garder. Il ne doit
pas comprendre que CoproScope valide les comptes.

## Retour utilisateur simule

Profil: expert-auditeur metier, novice CoproScope.

- Le filtre comptes existe, mais les mots "Controle comptes" et "preuve validee"
  peuvent faire croire a une validation officielle.
- L'interface existante est suffisante; il ne faut pas inventer une nouvelle
  direction visuelle pour cette page.
- Les reperes attendus sont: question, preuve a relire, decision humaine.

## Correction courte

- La page `/actions?scope=comptes` affiche une notice compacte dans le style
  existant.
- Le titre et les cartes parlent d'actions comptes, de question a poser et de
  preuve a relire.
- Les textes du parcours comptes disent explicitement que CoproScope ne valide
  pas les comptes.

## Backlog

Aucun nouveau besoin fonctionnel cree dans ce lot. Une future iteration pourra
mieux selectionner automatiquement une fiche comptes dans le registre permanent,
mais ce n'est pas necessaire pour cette correction de sens.

## Verifications

- `PYTHONPATH=server/src python -m unittest server.tests.test_ui_registre_actions -q`
  : 10 tests OK, 1 skip preexistant.
- `python tools/check_code_line_limit.py` : OK.
- `git diff --check` : OK.

