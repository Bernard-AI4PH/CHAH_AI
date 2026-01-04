import os
import tempfile
from flask import Flask, send_file, jsonify
from flask_cors import CORS

from engine import generate_transition_report_pdf

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "favicon.png")

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/api/report/<patient_id>")
def api_generate_report(patient_id: str):
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, dir="/tmp") as tmp:
            pdf_path = tmp.name

        generate_transition_report_pdf(
            patient_id=patient_id,
            pdf_path=pdf_path,
            logo_path=LOGO_PATH,
        )

        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"transition_report_{patient_id}.pdf",
        )

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
