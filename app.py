# app.py
import os
from flask import Flask, request, render_template, send_from_directory, send_file, jsonify

from engine import generate_transition_report_pdf

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(REPORT_DIR, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Simple HTML UI:
    - GET: show form asking for Patient_ID
    - POST: generate PDF and show it embedded
    """
    pdf_filename = None
    patient_id = None
    error = None

    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()
        if not patient_id:
            error = "Patient_ID is required."
        else:
            try:
                pdf_filename = f"transition_report_{patient_id}.pdf"
                pdf_path = os.path.join(REPORT_DIR, pdf_filename)
                generate_transition_report_pdf(patient_id, pdf_path)
            except ValueError as ve:
                error = str(ve)
                pdf_filename = None
            except Exception as e:
                error = f"Unexpected error: {e}"
                pdf_filename = None

    return render_template(
        "index.html",
        patient_id=patient_id,
        pdf_filename=pdf_filename,
        error=error,
    )


@app.route("/reports/<path:filename>")
def serve_report(filename):
    """
    Serve a generated PDF from the /reports folder so HTML can embed it.
    """
    return send_from_directory(REPORT_DIR, filename)


@app.route("/api/report/<patient_id>", methods=["GET"])
def api_generate_report(patient_id):
    """
    API endpoint:
    - URL: /api/report/<patient_id>
    - Returns PDF file directly (for other systems / Postman / etc.)
    """
    pdf_filename = f"transition_report_{patient_id}.pdf"
    pdf_path = os.path.join(REPORT_DIR, pdf_filename)

    try:
        generate_transition_report_pdf(patient_id, pdf_path)
    except ValueError as ve:
        # Patient not found / bad data
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=False,   # change to True if you want download instead of inline
        download_name=pdf_filename,
    )


if __name__ == "__main__":
    # For local testing
    app.run(debug=True)
