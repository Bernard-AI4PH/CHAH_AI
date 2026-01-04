import os
import tempfile
from flask import Flask, send_file, jsonify
from flask_cors import CORS

from engine import generate_transition_report_pdf

app = Flask(__name__)

# For initial testing: allow all origins. Tighten later if needed.
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "favicon.png")


@app.route("/", methods=["GET", "HEAD"])
def index():
    # Render/load balancers commonly send HEAD / probes.
    return (
        jsonify(
            {
                "service": "CHAH Flask API",
                "status": "running",
                "endpoints": ["/health", "/api/report/<patient_id>"],
            }
        ),
        200,
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/api/report/<patient_id>")
def api_generate_report(patient_id: str):
    try:
        # Render instances safely allow writing to /tmp.
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, dir="/tmp") as tmp:
            pdf_path = tmp.name

        generate_transition_report_pdf(
            patient_id=patient_id,
            pdf_path=pdf_path,
            logo_path=LOGO_PATH,  # uses your CHAH logo
        )

        # If you prefer a forced download, set as_attachment=True
        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"transition_report_{patient_id}.pdf",
        )

    except ValueError as ve:
        # engine.py raises ValueError for "patient not found" cases
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
