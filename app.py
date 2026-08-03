import io
import os
import json
from datetime import datetime
from uuid import uuid4
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'kunci-rahasia-anda'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['UPLOAD_RETENTION_SECONDS'] = 24 * 60 * 60

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def cleanup_files(*paths):
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)


def cleanup_stale_uploads():
    cutoff = datetime.now().timestamp() - app.config['UPLOAD_RETENTION_SECONDS']
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.isfile(path):
            continue
        if os.path.getmtime(path) < cutoff:
            os.remove(path)


def clear_session_file_refs():
    cleanup_files(
        session.get('upload_path'),
        session.get('json_path'),
        session.get('export_path'),
    )

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_empty_row(row):
    return all(str(value).strip() == '' for value in row.values())


def next_non_empty_index(data, start_index):
    index = start_index
    while index < len(data) and is_empty_row(data[index]):
        index += 1
    return index


@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        cleanup_stale_uploads()
        clear_session_file_refs()

        file = request.files.get('file')
        target_column = request.form.get('target_column', '').strip()
        display_columns_raw = request.form.get('display_columns', '').strip()
        
        if not file or file.filename == '':
            return render_template('upload.html', error="Silakan pilih file Excel terlebih dahulu!")
            
        if not target_column:
            return render_template('upload.html', error="Silakan isi nama kolom target!")

        if file and file.filename.endswith(('.xlsx', '.xls', '.XLSX', '.XLS')):
            upload_id = uuid4().hex
            original_filename = secure_filename(file.filename)
            file_root, file_ext = os.path.splitext(original_filename)
            stored_filename = f"{file_root}_{upload_id}{file_ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
            file.save(filepath)
            
            df = pd.read_excel(filepath)
            available_cols = list(df.columns)
            
            # Validasi 1: Kolom target harus ada
            if target_column not in available_cols:
                return render_template('upload.html', 
                                       error=f"Kolom '{target_column}' tidak ditemukan! Kolom tersedia: [{', '.join(available_cols)}]")

            # Olah kolom tampilan (display columns)
            display_columns = []
            if display_columns_raw:
                # Split berdasarkan koma dan hilangkan spasi tambahan
                display_columns = [col.strip() for col in display_columns_raw.split(',') if col.strip()]
                
                # Validasi 2: Cek jika ada nama kolom tampilan yang salah
                invalid_cols = [col for col in display_columns if col not in available_cols]
                if invalid_cols:
                    return render_template('upload.html', 
                                           error=f"Kolom tampilan tidak valid: [{', '.join(invalid_cols)}]. Kolom tersedia: [{', '.join(available_cols)}]")
            else:
                # Jika kosong, tampilkan semua kolom selain kolom target
                display_columns = [col for col in available_cols if col != target_column]

            # Simpan data ke JSON sementara
            json_filename = f"{file_root}_{upload_id}.json"
            json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
            
            # Ubah data Na/NaN menjadi string kosong agar aman di JSON
            df = df.fillna('')
            data = df.to_dict(orient='records')
            save_json(json_path, data)

            # Simpan metadata ke session
            session['upload_path'] = filepath
            session['json_path'] = json_path
            session['target_column'] = target_column
            session['display_columns'] = display_columns
            session['current_index'] = next_non_empty_index(data, 0)
            session['columns'] = available_cols
            session['export_stem'] = file_root or 'hasil_updated'
            session.pop('export_path', None)
            
            return redirect(url_for('edit'))
            
    return render_template('upload.html')


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if 'json_path' not in session or not os.path.exists(session['json_path']):
        return redirect(url_for('upload'))
        
    json_path = session['json_path']
    data = load_json(json_path)
    
    current_index = session['current_index']
    target_column = session['target_column']
    display_columns = session['display_columns']
    total_rows = len(data)

    current_index = next_non_empty_index(data, current_index)
    session['current_index'] = current_index

    if current_index >= total_rows:
        return redirect(url_for('export'))

    if request.method == 'POST':
        new_val = request.form.get('target_value')
        
        # Update nilai kolom target
        data[current_index][target_column] = new_val
        save_json(json_path, data)

        # Lanjut ke baris berikutnya
        session['current_index'] = next_non_empty_index(data, current_index + 1)
        
        if session['current_index'] >= total_rows:
            return redirect(url_for('export'))
            
        return redirect(url_for('edit'))

    current_row = data[current_index]
    
    return render_template('edit.html', 
                           row=current_row, 
                           index=current_index + 1, 
                           total=total_rows, 
                           target_column=target_column,
                           display_columns=display_columns)


@app.route('/export')
def export():
    if 'json_path' not in session or not os.path.exists(session['json_path']):
        return redirect(url_for('upload'))

    json_path = session['json_path']
    upload_path = session.get('upload_path')
    data = load_json(json_path)
    
    # Buat kembali DataFrame dengan urutan kolom persis seperti file asli
    df = pd.DataFrame(data)
    df = df[session['columns']]

    export_stem = secure_filename(session.get('export_stem', 'hasil_updated')) or 'hasil_updated'
    export_filename = f"{export_stem}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:8]}.xlsx"
    export_path = os.path.join(app.config['UPLOAD_FOLDER'], export_filename)
    df.to_excel(export_path, index=False)
    session['export_path'] = export_path

    session.clear()

    # Baca ke memory agar file bisa dihapus sebelum dikirim (hindari WinError 32)
    with open(export_path, 'rb') as f:
        file_bytes = io.BytesIO(f.read())
    cleanup_files(upload_path, json_path, export_path)

    return send_file(file_bytes, as_attachment=True, download_name=export_filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5000'))
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'}

    if debug_mode:
        app.run(host=host, port=port, debug=True)
    else:
        from waitress import serve

        serve(app, host=host, port=port, threads=8)