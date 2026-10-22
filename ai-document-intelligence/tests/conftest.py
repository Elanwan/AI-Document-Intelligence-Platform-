from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from app.database import configure_database
from app.main import app


def make_pdf(lines: list[str]) -> bytes:
    buffer = BytesIO()
    canvas = Canvas(buffer, pagesize=A4)
    _, height = A4
    text = canvas.beginText(72, height - 72)
    for line in lines:
        text.textLine(line)
    canvas.drawText(text)
    canvas.save()
    return buffer.getvalue()


@pytest.fixture
def pdf_factory():
    return make_pdf


@pytest.fixture
def client(tmp_path):
    configure_database(f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as test_client:
        yield test_client

