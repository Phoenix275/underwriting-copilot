"""webdata.py — export pipeline results into the web app's data directory.

The Python pipeline stays the single source of truth for every number the
front end shows. This step copies output/portfolio.json and the evaluation
report into web/src/data/ so Vite can inline them at build time — the built
dashboard is one self-contained HTML file that needs no server and no fetch.

Run after run_pipeline.py:
    python src/run_pipeline.py && python src/webdata.py && npm --prefix web run build
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
WEB_DATA = os.path.join(ROOT, "web", "src", "data")


def _round(obj, places=4):
    """Recursively round floats — trims ~15% off the payload with no visible loss."""
    if isinstance(obj, float):
        return round(obj, places)
    if isinstance(obj, dict):
        return {k: _round(v, places) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, places) for v in obj]
    return obj


def export():
    portfolio_path = os.path.join(OUT, "portfolio.json")
    report_path = os.path.join(OUT, "evaluation_report.json")
    for p in (portfolio_path, report_path):
        if not os.path.exists(p):
            raise SystemExit(
                f"{os.path.relpath(p, ROOT)} is missing. Run `python src/run_pipeline.py` first."
            )

    os.makedirs(WEB_DATA, exist_ok=True)
    portfolio = json.load(open(portfolio_path))
    report = json.load(open(report_path))

    cases = _round(portfolio["cases"])
    # Sort by composite risk so the plane's entry animation can stagger by score
    # without the front end re-sorting 200 records on every mount.
    cases.sort(key=lambda c: c["risk_score"])

    # The report carries the exported model coefficients and scaler statistics
    # that the browser re-scores with, so it is written at full precision —
    # rounding them to 4 places drifts the in-browser score by up to 0.6 points
    # against the pipeline. Only the per-case payload, which is 40× larger and
    # display-only, gets rounded.
    written = {}
    for name, payload in (("cases.json", cases), ("report.json", report)):
        path = os.path.join(WEB_DATA, name)
        with open(path, "w") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        written[name] = os.path.getsize(path)

    for name, size in written.items():
        print(f"web/src/data/{name}  {size / 1024:.0f} KB")
    print(f"{len(cases)} cases · report generated {report['generated_at']}")


if __name__ == "__main__":
    export()
