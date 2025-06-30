from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort
import os, json, csv, io, uuid, re
from werkzeug.utils import secure_filename
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer, Image as PlatypusImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATA_FILE = 'registrations.json'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
ADMIN_PASSWORD = 'admin123'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_registrations():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_registration(data):
    registrations = load_registrations()
    registrations.append(data)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(registrations, f, ensure_ascii=False, indent=2)

def slugify(value):
    value = str(value).strip().lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form.get('category')
        team_name = request.form.get('team_name')
        team_email = request.form.get('team_email')
        instagram = request.form.get('instagram')
        members = []
        error = False
        team_slug = slugify(team_name)
        for i in range(1, 7):
            member = {
                'name': request.form.get(f'member_name_{i}'),
                'gender': request.form.get(f'member_gender_{i}'),
                'ktm': None,
                'kta': None,
                'instagram': request.form.get(f'member_instagram_{i}'),
                'whatsapp': request.form.get(f'member_whatsapp_{i}')
            }
            ktm_file = request.files.get(f'member_ktm_{i}')
            kta_file = request.files.get(f'member_kta_{i}')
            # KTM
            if ktm_file and allowed_file(ktm_file.filename) and ktm_file.filename:
                ext = ktm_file.filename.rsplit('.', 1)[1].lower()
                filename = f"{team_slug}_anggota{i}_ktm.{ext}"
                ktm_file.save(os.path.join(UPLOAD_FOLDER, filename))
                member['ktm'] = filename
            # KTA
            if kta_file and allowed_file(kta_file.filename) and kta_file.filename:
                ext = kta_file.filename.rsplit('.', 1)[1].lower()
                filename = f"{team_slug}_anggota{i}_kta.{ext}"
                kta_file.save(os.path.join(UPLOAD_FOLDER, filename))
                member['kta'] = filename
            # Validasi: minimal salah satu KTM/KTA harus ada
            if not member['ktm'] and not member['kta']:
                error = True
            if not all([member['name'], member['gender'], member['instagram'], member['whatsapp']]):
                error = True
            members.append(member)
        if not category or not team_name or not team_email or not instagram or error:
            flash('Semua data wajib diisi. Untuk KTM/KTA, minimal salah satu harus diupload (jpg/png/pdf) per anggota!')
            # Kirim data yang sudah diisi agar tidak hilang
            return render_template('index.html',
                category=category,
                team_name=team_name,
                team_email=team_email,
                instagram=instagram,
                members=members
            )
        # Simpan ke file
        save_registration({
            'category': category,
            'team_name': team_name,
            'team_email': team_email,
            'instagram': instagram,
            'members': members
        })
        flash('Pendaftaran berhasil!')
        return render_template('success.html', team_name=team_name, members=members, category=category)
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            flash('Password salah!')
    if not session.get('admin'):
        return render_template('admin_login.html')
    # Filter
    registrations = load_registrations()
    filter_category = request.args.get('filter_category', '')
    search_team = request.args.get('search_team', '').strip().lower()
    if filter_category:
        registrations = [r for r in registrations if r['category'] == filter_category]
    if search_team:
        registrations = [r for r in registrations if search_team in r['team_name'].lower()]
    return render_template('admin.html', registrations=registrations, filter_category=filter_category, search_team=search_team)

@app.route('/export_csv')
def export_csv():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    registrations = load_registrations()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Kategori', 'Nama Tim', 'Email', 'Instagram', 'Nama Anggota', 'Gender', 'KTM', 'KTA', 'Instagram Anggota', 'WhatsApp'])
    for reg in registrations:
        for m in reg['members']:
            writer.writerow([
                reg['category'], reg['team_name'], reg['team_email'], reg['instagram'],
                m['name'], m['gender'], m['ktm'], m['kta'], m['instagram'], m['whatsapp']
            ])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='pendaftaran.csv')

@app.route('/export_pdf/<int:team_id>')
def export_pdf(team_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    registrations = load_registrations()
    if team_id < 1 or team_id > len(registrations):
        abort(404)
    reg = registrations[team_id-1]
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    # Judul
    elements.append(Paragraph(f"<b>Detail Tim: {reg['team_name']}</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Kategori:</b> {reg['category']}<br/><b>Email:</b> {reg['team_email']}<br/><b>Instagram:</b> {reg['instagram']}", styles['Normal']))
    elements.append(Spacer(1, 18))
    # Data anggota
    for idx, m in enumerate(reg['members'], 1):
        anggota_data = [
            [Paragraph(f"<b>Anggota {idx}: {m['name']}</b>", styles['Heading4']), '', ''],
            [f"Gender: {m['gender']}", f"Instagram: {m['instagram']}", f"WhatsApp: {m['whatsapp']}"]
        ]
        anggota_table = Table(anggota_data, colWidths=[180, 180, 180])
        anggota_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#b3d8fd')),  # Light blue
            ('BACKGROUND', (0,1), (-1,1), colors.whitesmoke),           # Light grey
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#003366')),   # Dark blue for nama
            ('TEXTCOLOR', (0,1), (-1,1), colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('FONTSIZE', (0,1), (-1,1), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,1), (-1,1), 6),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#b3d8fd')),
            ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor('#b3d8fd')),
        ]))
        elements.append(anggota_table)
        elements.append(Spacer(1, 8))
        # KTM
        if m.get('ktm'):
            ktm_path = os.path.join(UPLOAD_FOLDER, m['ktm'])
            if os.path.exists(ktm_path) and m['ktm'].lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    img = Image.open(ktm_path)
                    img.thumbnail((300, 300))
                    img_io = io.BytesIO()
                    img.save(img_io, format='PNG')
                    img_io.seek(0)
                    elements.append(Paragraph("<b>KTM:</b>", styles['Normal']))
                    elements.append(Spacer(1, 2))
                    elements.append(PlatypusImage(img_io, width=120, height=90))
                    elements.append(Spacer(1, 8))
                except Exception:
                    elements.append(Paragraph(f"KTM: {m['ktm']}", styles['Normal']))
            else:
                elements.append(Paragraph(f"KTM: {m['ktm']}", styles['Normal']))
        # KTA
        if m.get('kta'):
            kta_path = os.path.join(UPLOAD_FOLDER, m['kta'])
            if os.path.exists(kta_path) and m['kta'].lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    img = Image.open(kta_path)
                    img.thumbnail((300, 300))
                    img_io = io.BytesIO()
                    img.save(img_io, format='PNG')
                    img_io.seek(0)
                    elements.append(Paragraph("<b>KTA:</b>", styles['Normal']))
                    elements.append(Spacer(1, 2))
                    elements.append(PlatypusImage(img_io, width=120, height=90))
                    elements.append(Spacer(1, 8))
                except Exception:
                    elements.append(Paragraph(f"KTA: {m['kta']}", styles['Normal']))
            else:
                elements.append(Paragraph(f"KTA: {m['kta']}", styles['Normal']))
        elements.append(Spacer(1, 16))
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"pendaftaran_{reg['team_name']}.pdf")

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

@app.route('/admin/reset', methods=['POST'])
def admin_reset():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    # Hapus semua file media di uploads
    registrations = load_registrations()
    for reg in registrations:
        for m in reg['members']:
            for key in ['ktm', 'kta']:
                file = m.get(key)
                if file:
                    file_path = os.path.join(UPLOAD_FOLDER, file)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)
    flash('Semua data pendaftar dan file media berhasil dihapus!')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:team_id>', methods=['POST'])
def admin_delete_team(team_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    registrations = load_registrations()
    if 1 <= team_id <= len(registrations):
        reg = registrations.pop(team_id-1)
        # Hapus file media tim ini
        for m in reg['members']:
            for key in ['ktm', 'kta']:
                file = m.get(key)
                if file:
                    file_path = os.path.join(UPLOAD_FOLDER, file)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(registrations, f, ensure_ascii=False, indent=2)
        flash('Data tim dan file media berhasil dihapus!')
    else:
        flash('Tim tidak ditemukan!')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)