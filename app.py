import os
import json
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_file, session

app = Flask(__name__)
app.secret_key = 'kunci-rahasia-anda'
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        target_column = request.form.get('target_column', '').strip()
        display_columns_raw = request.form.get('display_columns', '').strip()
        
        if not file or file.filename == '':
            return render_template('upload.html', error="Silakan pilih file Excel terlebih dahulu!")
            
        if not target_column:
            return render_template('upload.html', error="Silakan isi nama kolom target!")

        if file and file.filename.endswith(('.xlsx', '.xls')):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
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
            json_filename = f"{file.filename}.json"
            json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
            
            # Ubah data Na/NaN menjadi string kosong agar aman di JSON
            df = df.fillna('')
            data = df.to_dict(orient='records')
            save_json(json_path, data)

            # Simpan metadata ke session
            session['json_path'] = json_path
            session['target_column'] = target_column
            session['display_columns'] = display_columns
            session['current_index'] = 0
            session['columns'] = available_cols
            
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

    if request.method == 'POST':
        new_val = request.form.get('target_value')
        
        # Update nilai kolom target
        data[current_index][target_column] = new_val
        save_json(json_path, data)
        
        # Lanjut ke baris berikutnya
        session['current_index'] += 1
        
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
    data = load_json(json_path)
    
    # Buat kembali DataFrame dengan urutan kolom persis seperti file asli
    df = pd.DataFrame(data)
    df = df[session['columns']]

    export_path = os.path.join(app.config['UPLOAD_FOLDER'], 'hasil_updated.xlsx')
    df.to_excel(export_path, index=False)

    if os.path.exists(json_path):
        os.remove(json_path)

    session.clear()

    return send_file(export_path, as_attachment=True, download_name='hasil_updated.xlsx')


if __name__ == '__main__':
    # host='0.0.0.0' membuat server Flask dapat diakses oleh semua perangkat di jaringan yang sama
    app.run(host='0.0.0.0', port=5000, debug=True)