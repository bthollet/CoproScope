from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, read_csv, relative_to, write_csv
from coproscope.modules import pdftrace_registry
from coproscope.web.app import create_app


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class DocumentViewerTraceReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(self.repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token="local-secret"))

    def _documents(self) -> tuple[list[str], list[dict[str, str]]]:
        fields, rows = read_csv(self.instance.register("documents"))
        return fields or list(DEFAULT_DOCUMENT_FIELDS), rows

    def _write_documents(self, fields: list[str], rows: list[dict[str, str]]) -> None:
        write_csv(self.instance.register("documents"), fields, rows)

    def _add_pdf_document(self, doc_id: str) -> tuple[Path, bytes]:
        fields, rows = self._documents()
        pdf_bytes = b"%PDF-1.4\n% replay trace test\n"
        pdf_path = self.instance_root / "staging" / "pdf" / f"{doc_id}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(pdf_bytes)
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": f"{doc_id}.pdf",
                "extension": "pdf",
                "sha256": _sha256(pdf_bytes),
                "size_bytes": str(pdf_path.stat().st_size),
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF",
                "page_count": "2",
                "text_char_count": "50",
            }
        )
        self._write_documents(fields, rows)
        return pdf_path, pdf_bytes

    def test_saved_trace_can_be_reopened_without_private_or_technical_leaks(self) -> None:
        doc_id = "DOC-PDF-REPLAY"
        pdf_path, pdf_bytes = self._add_pdf_document(doc_id)
        client = self._client()

        response = client.post(
            f"/documents/{doc_id}/traces?token=local-secret",
            data={
                "page": "2",
                "zone_x": "0.2",
                "zone_y": "0.25",
                "zone_width": "0.4",
                "zone_height": "0.1",
                "comment": "Point budget a reprendre",
            },
            follow_redirects=False,
        )
        trace_rows = read_csv(pdftrace_registry.trace_register_path(self.instance))[1]
        trace_id = trace_rows[0]["trace_id"]
        detail = client.get(f"/documents/{doc_id}?trace_id={trace_id}&token=local-secret")
        body = unescape(detail.text)

        self.assertEqual(response.status_code, 303)
        self.assertIn(f"trace_id={trace_id}", response.headers["location"])
        self.assertEqual(pdf_path.read_bytes(), pdf_bytes)
        self.assertEqual(detail.status_code, 200)
        self.assertIn("Reprendre cette trace", body)
        self.assertIn("Point de reprise ouvert", body)
        self.assertIn("Vous reprenez ici: Zone encadree page 2.", body)
        self.assertIn("Prochaine action:", body)
        self.assertIn("Relire manuellement la zone encadree et saisir la donnee utile.", body)
        self.assertIn("Note courte: Point budget a reprendre", body)
        self.assertNotIn("Exporter les traces a relire", body)
        self.assertNotIn("/exports/pdf-traces-reprise", body)
        self.assertIn('aria-current="true"', detail.text)
        self.assertIn('data-pdf-trace-current-page="2"', detail.text)
        self.assertIn('data-pdf-trace-resume-page="2"', detail.text)
        self.assertIn('data-pdf-trace-resume-x="0.2"', detail.text)
        self.assertIn('data-pdf-trace-resume-y="0.25"', detail.text)
        self.assertIn('data-pdf-trace-resume-width="0.4"', detail.text)
        self.assertIn('data-pdf-trace-resume-height="0.1"', detail.text)
        self.assertIn(f'data-pdf-trace-id="{trace_id}"', detail.text)
        self.assertIn('data-pdf-trace-page="2"', detail.text)
        self.assertIn('data-pdf-trace-x="0.2"', detail.text)
        self.assertIn('data-pdf-trace-y="0.25"', detail.text)
        self.assertIn('data-pdf-trace-width="0.4"', detail.text)
        self.assertIn('data-pdf-trace-height="0.1"', detail.text)
        self.assertIn("Point de reprise: Zone encadree page 2", body)
        self._assert_no_private_or_technical_leak(body)
        json_response = client.get("/exports/pdf-traces-reprise.json?token=local-secret")
        csv_response = client.get("/exports/pdf-traces-reprise.csv?token=local-secret")

        self.assertEqual(json_response.status_code, 404)
        self.assertEqual(csv_response.status_code, 404)

    def test_pdf_trace_queue_lists_local_reprises_without_export_or_leaks(self) -> None:
        doc_id = "DOC-PDF-QUEUE"
        self._add_pdf_document(doc_id)
        client = self._client()

        response = client.post(
            f"/documents/{doc_id}/traces?token=local-secret",
            data={
                "page": "2",
                "zone_x": "0.2",
                "zone_y": "0.25",
                "zone_width": "0.4",
                "zone_height": "0.1",
                "comment": "Point budget a reprendre",
            },
            follow_redirects=False,
        )
        queue = client.get("/pdf-traces?token=local-secret")
        documents = client.get("/documents?token=local-secret")
        blocked = self._client().get("/pdf-traces")
        body = unescape(queue.text)

        self.assertEqual(response.status_code, 303)
        self.assertEqual(queue.status_code, 200)
        self.assertEqual(documents.status_code, 200)
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("File locale de reprise PDF", body)
        self.assertIn("File reprises PDF", unescape(documents.text))
        self.assertIn("Ouvrir la trace", body)
        self.assertIn("Relire manuellement la zone encadree et saisir la donnee utile.", body)
        self.assertIn(f"/documents/{doc_id}?trace_id=", queue.text)
        self.assertIn("#pdf-reader", queue.text)
        self.assertNotIn("Point budget a reprendre", body)
        self.assertNotIn("Exporter les traces", body)
        self.assertNotIn("/exports/pdf-traces-reprise", body)
        self._assert_no_private_or_technical_leak(body)

    def test_public_trace_summary_keeps_replay_and_local_reprise_fields(self) -> None:
        doc_id = "DOC-PDF-REPLAY-SUMMARY"
        self._add_pdf_document(doc_id)
        row = pdftrace_registry.save_zone_trace(
            self.instance,
            read_csv(self.instance.register("documents"))[1][-1],
            {
                "page": "2",
                "zone_x": "0.2",
                "zone_y": "0.25",
                "zone_width": "0.4",
                "zone_height": "0.1",
                "comment": "Point budget a reprendre",
            },
        )

        summary = pdftrace_registry.public_trace_summaries(self.instance, doc_id)[0]

        self.assertEqual(summary["trace_id"], row["trace_id"])
        self.assertEqual(summary["page"], "2")
        self.assertEqual(summary["zone_x"], "0.2")
        self.assertEqual(summary["zone_y"], "0.25")
        self.assertEqual(summary["zone_width"], "0.4")
        self.assertEqual(summary["zone_height"], "0.1")
        self.assertEqual(summary["resume_path"], f"/documents/{doc_id}?trace_id={row['trace_id']}")
        self.assertEqual(summary["next_action"], "Relire manuellement la zone encadree et saisir la donnee utile.")
        for forbidden in ("source_engine", "zotero_position", "rects", "selected_text_hash", "original_path"):
            self.assertNotIn(forbidden, summary)

    def test_pdf_trace_selection_script_replays_saved_zone_read_only(self) -> None:
        script = _selection_script_text(self.repo_root)

        self.assertIn("data-pdf-trace-resume-page", script)
        self.assertIn("data-pdf-trace-replay", script)
        self.assertIn("applySavedTrace", script)
        self.assertIn("restoreSavedSelection", script)
        self.assertIn("resumeSelection.page !== currentPage", script)
        self.assertIn("setSubmitEnabled(submit, false)", script)
        self.assertIn("Point de reprise", script)
        self.assertNotIn("zotero_position", script)
        self.assertNotIn("source_engine", script)
        self.assertNotIn("rects", script)

    def _assert_no_private_or_technical_leak(self, body: str) -> None:
        forbidden = (
            "source_engine",
            "zotero_position",
            "rects",
            "selected_text_hash",
            "original_path",
            str(self.instance_root),
            "raw/",
            "raw\\",
        )
        for value in forbidden:
            self.assertNotIn(value, body)


def _selection_script_text(repo_root: Path) -> str:
    return (repo_root / "server" / "src" / "coproscope" / "web" / "static" / "pdf_trace_selection.js").read_text(
        encoding="utf-8"
    )


if __name__ == "__main__":
    unittest.main()
