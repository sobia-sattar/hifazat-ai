import csv
import io
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.security import LocalBoundaryMiddleware, MAX_BODY
from app.services.reports import comments_csv, comments_pdf


def client():
    app = FastAPI()
    app.add_middleware(LocalBoundaryMiddleware)
    @app.post('/echo')
    async def echo(request: Request):
        return await request.json()
    return TestClient(app)


def test_local_json_body_survives_security_middleware():
    response = client().post('/echo', json={'text': 'hello'}, headers={'origin': 'http://localhost:5173'})
    assert response.status_code == 200 and response.json()['text'] == 'hello'
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'


def test_cross_site_and_rebinding_blocked():
    c = client()
    assert c.post('/echo', json={}, headers={'origin': 'https://evil.example'}).status_code == 403
    assert c.post('/echo', json={}, headers={'sec-fetch-site': 'cross-site'}).status_code == 403
    assert c.post('/echo', json={}, headers={'host': 'evil.example:8011'}).status_code == 400


def test_large_and_invalid_body_lengths_rejected():
    c = client()
    assert c.post('/echo', content=b'x'*(MAX_BODY+1)).status_code == 413
    assert c.post('/echo', content=b'{}', headers={'content-length': 'oops'}).status_code == 400
    assert c.post('/echo', content=b'x'*(MAX_BODY+1), headers={'content-length': '2'}).status_code == 413


def test_video_export_does_not_execute_spreadsheet_formulas():
    output = comments_csv({'comments': [{'original_text': ' \t=HYPERLINK("bad")'}, {'original_text': 'ordinary text'}]})
    rows = list(csv.DictReader(io.StringIO(output.decode())))
    assert rows[0]['comment'].startswith("'")
    assert rows[1]['comment'] == 'ordinary text'


def test_pdf_treats_untrusted_markup_as_literal_text():
    output = comments_pdf({'video': {'title': '<img src="file:///does-not-exist"/>'},
                           'comments': [{'risk': 'HIGH', 'original_text': '<broken> & text'}]})
    assert output.startswith(b'%PDF-')


def test_external_explanations_require_explicit_privacy_opt_in():
    from app.core.config import Settings
    settings = Settings(_env_file=None, genai_api_key='test', allow_external_explanations=False)
    assert not settings.genai_enabled
    settings.allow_external_explanations = True
    assert settings.genai_enabled
