# app.py

import os
import json
import tempfile
from flask import Flask, render_template, request, jsonify
from resume_parser import parse_resume

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    result_json = None
    error = None

    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            error = "Please upload a resume file."
        else:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in [".pdf", ".docx", ".txt", ".text", ".jpg", ".jpeg", ".png"]:
                error = "Unsupported file type. Use PDF, DOCX, TXT, JPG, PNG."
            else:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                try:
                    file.save(tmp.name)
                    data = parse_resume(tmp.name)
                    result = data
                    result_json = json.dumps(data, indent=2, ensure_ascii=False)
                except Exception as e:
                    error = f"Error while parsing: {e}"
                finally:
                    tmp.close()
                    try:
                        os.remove(tmp.name)
                    except OSError:
                        pass

    return render_template("index.html", result=result, result_json=result_json, error=error)


# Optional JSON API endpoint
@app.route("/api/parse", methods=["POST"])
def api_parse():
    """
    POST /api/parse
    form-data: file=<resume file>
    returns JSON schema
    """
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "file is required"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".txt", ".text", ".jpg", ".jpeg", ".png"]:
        return jsonify({"error": "Unsupported file type"}), 400

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        file.save(tmp.name)
        data = parse_resume(tmp.name)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        tmp.close()
        try:
            os.remove(tmp.name)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(debug=True)
