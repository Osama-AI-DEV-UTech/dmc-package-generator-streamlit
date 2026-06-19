"""FastAPI backend — Enterprise DMC Package Generator (v4).

POST /api/generate                    -> N distinct packages (+DMC info, refs),
                                         each with TWO PDFs: full + dmc.
GET  /api/download/{rid}/{idx}/{kind} -> kind in {full, dmc}
GET  /api/request/{rid}               -> stored result as JSON
GET  /health
"""
from __future__ import annotations

import os
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from .config import settings
from .generator import GenerationResult, generate
from .inputs import UserInput
from .openai_client import OpenAIError
from .pdf import build_package_pdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN_DIR = os.path.join(BASE_DIR, "generated")
os.makedirs(GEN_DIR, exist_ok=True)

app = FastAPI(title="Enterprise DMC Package Generator", version="4.0.0")
STORE: Dict[str, GenerationResult] = {}


def _build_pdf(v, result, kind: str) -> str:
    return build_package_pdf(v.package, v.dmc, v.references, result.sources, v.currency,
                             GEN_DIR, result.request_id, v.index, engine=result.engine, mode=kind)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "openai_configured": settings.has_openai,
            "model": settings.openai_model, "web_search": settings.enable_web_search}


@app.post("/api/generate")
def api_generate(payload: UserInput) -> JSONResponse:
    if not settings.has_openai:
        raise HTTPException(503, "OPENAI_API_KEY not configured in .env.")
    try:
        result = generate(payload)
    except OpenAIError as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Generation error: {exc}") from exc

    STORE[result.request_id] = result
    packages = []
    for v in result.variants:
        for kind in ("full", "dmc"):
            try:
                _build_pdf(v, result, kind)
            except Exception as exc:  # noqa: BLE001
                result.warnings.append(f"PDF ({kind}) for package {v.index} failed: {exc}")
        packages.append({
            "index": v.index,
            "package": v.package.as_json(),
            "dmc_info": v.dmc.model_dump() if v.dmc else None,
            "price_references": [r.model_dump() for r in v.references],
            "currency": v.currency,
            "pdf_url_full": f"/api/download/{result.request_id}/{v.index}/full",
            "pdf_url_dmc": f"/api/download/{result.request_id}/{v.index}/dmc",
        })

    return JSONResponse({
        "request_id": result.request_id, "engine": result.engine,
        "count": len(packages), "packages": packages,
        "sources": result.sources, "warnings": result.warnings,
    })


@app.get("/api/request/{rid}")
def api_request(rid: str) -> JSONResponse:
    r = STORE.get(rid)
    if not r:
        raise HTTPException(404, "Request not found.")
    return JSONResponse({
        "request_id": r.request_id, "count": len(r.variants),
        "packages": [{
            "index": v.index, "package": v.package.as_json(),
            "dmc_info": v.dmc.model_dump() if v.dmc else None,
            "price_references": [x.model_dump() for x in v.references],
            "currency": v.currency,
            "pdf_url_full": f"/api/download/{r.request_id}/{v.index}/full",
            "pdf_url_dmc": f"/api/download/{r.request_id}/{v.index}/dmc",
        } for v in r.variants],
        "sources": r.sources,
    })


@app.get("/api/download/{rid}/{idx}/{kind}")
def api_download(rid: str, idx: int, kind: str) -> FileResponse:
    if kind not in ("full", "dmc"):
        raise HTTPException(400, "kind must be 'full' or 'dmc'.")
    r = STORE.get(rid)
    if not r:
        raise HTTPException(404, "Request not found.")
    v = next((x for x in r.variants if x.index == idx), None)
    if not v:
        raise HTTPException(404, "Package index not found.")
    path = os.path.join(GEN_DIR, f"{rid}_pkg{idx}_{kind}.pdf")
    if not os.path.isfile(path):
        _build_pdf(v, r, kind)
    safe = "".join(ch for ch in v.package.name if ch.isalnum() or ch in " -_")[:50].strip()
    suffix = "full" if kind == "full" else "for-DMC"
    return FileResponse(path, media_type="application/pdf",
                        filename=f"{safe or 'package'}-{idx}-{suffix}.pdf")
