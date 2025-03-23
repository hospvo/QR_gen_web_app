from flask import Flask, render_template, request, send_file, jsonify
import qrcode
from PIL import Image
import os
from io import BytesIO

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
GENERATED_FOLDER = "generated"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

def generate_qr(url, logo_path=None):
    """ Generate a high-resolution QR code with optional logo """
    qr = qrcode.QRCode(box_size=10, border=4)  # Always generate at high resolution
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white").convert("RGB")

    if logo_path:
        logo = Image.open(logo_path)
        qr_width, qr_height = img.size
        logo_size = min(qr_width, qr_height) // 5
        logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
        pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
        img.paste(logo, pos)

    return img

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/generate_qr", methods=["POST"])
def generate_qr_code():
    """ Handle AJAX request to generate a QR preview """
    url = request.form.get("url")
    logo = request.files.get("logo")
    size = request.form.get("size", type=int)  # Získáme požadovanou velikost

    if not size:
        size = 300  # Výchozí velikost QR kódu

    logo_path = None
    if logo and logo.filename:
        logo_path = os.path.join(UPLOAD_FOLDER, logo.filename)
        logo.save(logo_path)

    qr_image = generate_qr(url, logo_path)

    # Upravíme velikost výsledného obrázku
    qr_image = qr_image.resize((size, size), Image.Resampling.LANCZOS)

    # Uložíme high-res QR kód pro stažení
    save_path = os.path.join(GENERATED_FOLDER, "qr_code.png")
    qr_image.save(save_path)

    # Vytvoříme náhled (vždy 300px)
    preview_img = qr_image.resize((300, 300), Image.Resampling.LANCZOS)
    img_io = BytesIO()
    preview_img.save(img_io, "PNG")
    img_io.seek(0)

    return send_file(img_io, mimetype="image/png")

@app.route("/download")
def download_qr():
    """ Serve the high-resolution QR code for download """
    path = os.path.join(GENERATED_FOLDER, "qr_code.png")
    return send_file(path, as_attachment=True, download_name="qr_code.png")

if __name__ == "__main__":
    app.run(debug=True)
