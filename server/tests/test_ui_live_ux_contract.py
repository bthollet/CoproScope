from __future__ import annotations

import os
import re
import unittest
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen


LIVE_BASE_URL = os.environ.get("COPROSCOPE_LIVE_URL", "http://127.0.0.1:8766").rstrip("/")
LIVE_TOKEN = os.environ.get("COPROSCOPE_LIVE_TOKEN", "local-secret")
LIVE_REQUIRED = os.environ.get("COPROSCOPE_LIVE_REQUIRED", "").lower() in {"1", "true", "yes"}
LIVE_TIMEOUT_SECONDS = float(os.environ.get("COPROSCOPE_LIVE_TIMEOUT", "8"))
RELANCE_FLOW_PIECE_ID_ENV = os.environ.get("COPROSCOPE_LIVE_PIECE_ID", "UX-PIECE-COMP-C2B3F479")
RELANCE_FLOW_AUTO_VALUES = {"auto", "discover", "live"}

SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[\s\S]*?</\1>", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
MAIN_RE = re.compile(r"<main\b[^>]*id=[\"']contenu[\"'][^>]*>(?P<body>[\s\S]*?)</main>", re.IGNORECASE)

PRIMARY_ROUTE_CONTRACTS = [
    (
        "/",
        (
            "Cockpit conseil syndical",
            "Ce qui demande attention maintenant",
            "Statut sync a verifier",
        ),
    ),
    (
        "/actions",
        (
            "Registre des decisions",
            "Boite de travail du conseil syndical",
            "Preuve / source",
            "Prochaine action",
        ),
    ),
    (
        "/comptes",
        (
            "Controle des comptes",
            "Prochain geste humain",
            "questions au syndic",
        ),
    ),
    (
        "/documents",
        (
            "Documents, preuves et demandes",
            "DocOps actionnable",
            "Ce qu'on a, ce qui manque, ce qu'il faut demander",
        ),
    ),
    (
        "/documents/ajouter",
        (
            "Ajout de document",
            "Parcours novice piece -> point -> action -> preuve",
            "Prochaine action",
        ),
    ),
    (
        "/pieces",
        (
            "Atelier pieces",
            "Pieces a demander",
            "Prochaine etape",
        ),
    ),
    (
        "/demandes",
        (
            "Boite de demandes a suivre",
            "lecture novice",
            "prochaine action",
        ),
    ),
    (
        "/ag-contentieux",
        (
            "AG, contentieux, passation",
            "Preuve / source",
            "Restriction / diffusion",
        ),
    ),
    (
        "/gouvernance",
        (
            "Tableau de controle local",
            "Droits croises",
            "Commissions et acces",
        ),
    ),
    (
        "/pilotage",
        (
            "Pilotage des indicateurs",
            "Preuve ou source",
            "Prochaine action",
        ),
    ),
    (
        "/confidentialite",
        (
            "Confidentialite et diffusion",
            "Decision de diffusion",
            "Regle de publication prudence",
        ),
    ),
    (
        "/chantiers",
        (
            "Memoire de copropriete",
            "Ajouter un evenement",
            "preuves a transmettre",
        ),
    ),
    (
        "/depot",
        (
            "Depot guide & exports locaux",
            "Ce depot reste local",
            "Cette page ne synchronise rien vers un service cloud",
        ),
    ),
]

ACTIONABLE_ROUTE_CONTRACTS = [
    (
        "/actions?priority=P1",
        "Toutes les actions en retard",
        (
            "Preparer une relance",
            "Rattacher une piece",
        ),
    ),
    (
        "/demandes/relance",
        "Relance syndic",
        (
            "Noter l'envoi fait hors CoproScope",
            "Rattacher la reponse du syndic",
        ),
    ),
    (
        "/pieces?proof=missing",
        "Pieces manquantes",
        (
            "Creer demandes syndic",
            "Ajouter reponse recue",
        ),
    ),
]

NOVICE_LABEL_ROUTES = [
    (
        "/",
        (
            "Cette page reste locale",
            "aucune synchronisation externe n'est lancee",
            "Ce qui demande attention maintenant",
        ),
    ),
    (
        "/documents/ajouter",
        (
            "reference opaque",
            "chemin prive",
            "Relier la preuve",
        ),
    ),
    (
        "/demandes",
        (
            "lecture novice",
            "preuve/source",
            "prochaine action",
            "diffusion",
        ),
    ),
    (
        "/ag-contentieux",
        (
            "Preuve / source",
            "Restriction / diffusion",
            "Prochaine action",
        ),
    ),
    (
        "/depot",
        (
            "Ce depot reste local",
            "A verifier avant toute sync externe",
            "sans publier les bruts",
        ),
    ),
]

PRIVATE_ROUTE_PROBES = [
    "/raw/ui-live-probe.txt",
    "/restricted/ui-live-probe.txt",
    "/logs/ui-live-probe.log",
    "/private/ui-live-probe.txt",
    "/exports/raw/ui-live-probe.txt",
    "/exports/restricted/ui-live-probe.txt",
    "/exports/logs/ui-live-probe.log",
    "/exports/private/ui-live-probe.txt",
]

PRIVATE_LEAK_MARKERS = (
    "UI_ROUTE_RAW_LEAK",
    "UI_ROUTE_RESTRICTED_LEAK",
    "UI_ROUTE_LOG_LEAK",
    "UI_ROUTE_PRIVATE_LEAK",
)

PRIVATE_PATH_PATTERNS = (
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)[\\/]", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'=])(?:raw|restricted|logs|private)[\\/]", re.IGNORECASE),
)

LIVE_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
PIECE_DETAIL_HREF_RE = re.compile(r"href=[\"'](?P<href>/pieces/(?P<piece_id>[A-Za-z0-9][A-Za-z0-9_.:-]{0,127})(?:\?[^\"'#]*)?)[\"']")


def _visible_text(html: str) -> str:
    without_code = SCRIPT_STYLE_RE.sub(" ", html)
    without_tags = TAG_RE.sub(" ", without_code)
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def _main_text(html: str) -> str:
    match = MAIN_RE.search(html)
    if not match:
        raise AssertionError("Missing main#contenu")
    return _visible_text(match.group("body"))


def _with_token(path: str) -> str:
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}token={quote(LIVE_TOKEN, safe='')}"


def _url(path: str, *, token: bool = True) -> str:
    return f"{LIVE_BASE_URL}{_with_token(path) if token else path}"


def _fetch(path: str, *, token: bool = True) -> tuple[int, str]:
    request = Request(_url(path, token=token), headers={"User-Agent": "coproscope-qa-live-ux-contract"})
    try:
        with urlopen(request, timeout=LIVE_TIMEOUT_SECONDS) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        try:
            return exc.code, exc.read().decode("utf-8", errors="replace")
        finally:
            exc.close()


def _relance_flow_piece_id() -> str:
    requested = RELANCE_FLOW_PIECE_ID_ENV.strip()
    if requested.lower() not in RELANCE_FLOW_AUTO_VALUES:
        return requested or "UX-PIECE-COMP-C2B3F479"

    status, html = _fetch("/pieces?proof=missing")
    if status != 200:
        raise AssertionError(f"live missing-pieces route returned {status}; cannot discover a piece detail link")

    for match in PIECE_DETAIL_HREF_RE.finditer(html):
        href = unescape(match.group("href"))
        path = urlsplit(href).path
        piece_id = unquote(path.removeprefix("/pieces/")).strip()
        if piece_id != "reference-locale-masquee" and LIVE_SAFE_ID_RE.fullmatch(piece_id):
            return piece_id
    raise AssertionError("No live piece detail link found on /pieces?proof=missing")


def _relance_flow_routes(piece_id: str) -> list[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    return [
        (
            f"/pieces/{quote(piece_id, safe='')}",
            (
                "Detail piece/preuve",
                "Pourquoi cette piece compte",
                "Piece concernee",
                "Action suivante",
                "Prudence diffusion",
                "Relancer syndic",
                "Ajouter reponse recue",
            ),
            (
                "Detail piece/preuve",
                "Pourquoi cette piece compte",
                "Piece concernee",
                "Action suivante",
                "Prudence diffusion",
                "Relancer syndic",
            ),
        ),
        (
            f"/demandes/relance?piece_detail={quote(piece_id, safe='')}",
            (
                "Brouillon a copier, non envoye",
                "Piece concernee",
                "Preuve attendue",
                "A qui demander / qui doit l'avoir",
                "Pourquoi",
                "Action suivante",
                "Prudence diffusion",
                "Diffusion : verifier avant de joindre une piece",
                "Rattacher la reponse du syndic",
                "Retour detail piece/preuve",
                "Noter l'envoi hors CoproScope indisponible",
            ),
            (
                "Brouillon a copier, non envoye",
                "Piece concernee",
                "Preuve attendue",
                "A qui demander / qui doit l'avoir",
                "Pourquoi",
                "Action suivante",
                "Prudence diffusion",
            ),
        ),
        (
            f"/depot?intent=proof&status=reponse-recue&return=pieces&piece_detail={quote(piece_id, safe='')}",
            (
                "Depot guide & exports locaux",
                "Reponse recue pour cette piece",
                "Piece candidate a verifier",
                "Piece concernee",
                "Action suivante",
                "Prudence diffusion",
                "Preuve attendue",
                "Retour detail piece/preuve",
            ),
            (
                "Depot guide & exports locaux",
                "Reponse recue pour cette piece",
                "Piece candidate a verifier",
                "Piece concernee",
                "Action suivante",
                "Prudence diffusion",
            ),
        ),
    ]


def _flow_route_label(path: str, piece_id: str) -> str:
    encoded = quote(piece_id, safe="")
    return path.replace(encoded, "<piece-id>").replace(piece_id, "<piece-id>")


def _assert_no_private_leak(testcase: unittest.TestCase, text: str, route: str) -> None:
    for marker in PRIVATE_LEAK_MARKERS:
        testcase.assertNotIn(marker, text, route)
    for pattern in PRIVATE_PATH_PATTERNS:
        testcase.assertIsNone(pattern.search(text), f"{route} leaks private path pattern {pattern.pattern!r}")


class LiveUiUxContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            status, body = _fetch("/health", token=False)
        except URLError as exc:
            message = f"live server unavailable at {LIVE_BASE_URL}: {exc}"
            if LIVE_REQUIRED:
                raise AssertionError(message) from exc
            raise unittest.SkipTest(message) from exc

        if status != 200:
            raise AssertionError(f"live health returned {status}: {body[:200]}")

    def test_primary_live_routes_are_200_and_render_useful_main_content(self) -> None:
        for path, expected_labels in PRIMARY_ROUTE_CONTRACTS:
            with self.subTest(path=path):
                status, html = _fetch(path)
                main = _main_text(html)

                self.assertEqual(status, 200, path)
                self.assertNotIn("404", main[:500], path)
                for label in expected_labels:
                    self.assertIn(label, main, f"{path} missing useful label {label!r}")
                _assert_no_private_leak(self, html, path)

    def test_useful_content_stays_close_to_top_and_context_banner_is_bounded(self) -> None:
        for path, expected_labels in PRIMARY_ROUTE_CONTRACTS:
            with self.subTest(path=path):
                status, html = _fetch(path)
                main = _main_text(html)

                self.assertEqual(status, 200, path)
                first_label_index = min(main.index(label) for label in expected_labels if label in main)
                self.assertLess(first_label_index, 900, f"{path} useful content is too deep in main#contenu")

                context_index = html.find("context-banner")
                main_index = html.find('<main id="contenu"')
                if 0 <= context_index < main_index:
                    context_visible_len = len(_visible_text(html[context_index:main_index]))
                    self.assertLessEqual(
                        context_visible_len,
                        1500,
                        f"{path} context banner is too large before main content",
                    )

    def test_novice_labels_are_present_on_expected_live_surfaces(self) -> None:
        for path, expected_labels in NOVICE_LABEL_ROUTES:
            with self.subTest(path=path):
                status, html = _fetch(path)
                main = _main_text(html)

                self.assertEqual(status, 200, path)
                for label in expected_labels:
                    self.assertIn(label, main, f"{path} missing novice label {label!r}")

    def test_p1_relance_and_missing_piece_routes_expose_useful_actions(self) -> None:
        for path, page_label, action_labels in ACTIONABLE_ROUTE_CONTRACTS:
            with self.subTest(path=path):
                status, html = _fetch(path)
                main = _main_text(html)

                self.assertEqual(status, 200, path)
                self.assertIn(page_label, main)
                for label in action_labels:
                    self.assertIn(label, main, f"{path} missing action {label!r}")
                _assert_no_private_leak(self, html, path)

    def test_piece_relance_depot_flow_keeps_novice_markers_in_first_viewport_band(self) -> None:
        piece_id = _relance_flow_piece_id()
        for path, expected_labels, first_viewport_labels in _relance_flow_routes(piece_id):
            route_label = _flow_route_label(path, piece_id)
            with self.subTest(path=route_label):
                status, html = _fetch(path)
                main = _main_text(html)
                first_viewport_band = main[:1800]

                self.assertEqual(status, 200, route_label)
                for label in expected_labels:
                    self.assertIn(label, main, f"{route_label} missing flow label {label!r}")
                for label in first_viewport_labels:
                    self.assertIn(label, first_viewport_band, f"{route_label} hides {label!r} too deep for novice use")
                if path.startswith("/pieces/"):
                    self.assertNotIn("Piece introuvable", main, route_label)
                if piece_id not in html:
                    self.fail(f"{route_label} lost piece context")
                _assert_no_private_leak(self, html, route_label)

    def test_private_roots_are_not_served_or_leaked_by_live_routes(self) -> None:
        for path in PRIVATE_ROUTE_PROBES:
            with self.subTest(path=path):
                status, body = _fetch(path)

                self.assertEqual(status, 404, path)
                _assert_no_private_leak(self, body, path)


if __name__ == "__main__":
    unittest.main()
