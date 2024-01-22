import pyodbc
from flask import Flask, render_template, request, redirect, flash, jsonify
from keras.models import load_model
import os
import numpy as np
from PIL import Image
from datetime import datetime
import tensorflow as tf

# Thiết lập thông tin kết nối SQL Server
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-4O30K6O;"
    "DATABASE=UngThuDa;"
    "UID=sa;"
    "PWD=123;"
)
cursor = conn.cursor()

app = Flask(__name__)
# Load mô hình được huấn luyện trước
model = tf.keras.models.load_model('..\\DoAn\\templates\\skinDiseaseDetectionUsningCNN_vgg16_70_30.onnx')

UPLOAD_FOLDER = '..\\DoAn\\templates\\Test'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Các định dạng ảnh cho phép

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Hàm kiểm tra định dạng tệp ảnh cho phép
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/', methods=['GET', 'POST'])
def danh_sach_tai_khoan():
    cursor.execute('SELECT * FROM TaiKhoan')
    rows = cursor.fetchall()
    return render_template('DangNhap.html', data=rows)

@app.route('/login', methods=['GET', 'POST'])
def dang_nhap():
    if request.method == 'POST':
        TenNguoiDung = request.form['TenNguoiDung']
        MatKhau = request.form['MatKhau']

        query = "SELECT * FROM TaiKhoan WHERE taikhoan = ? AND matkhau = ?"
        cursor.execute(query, (TenNguoiDung, MatKhau))
        user = cursor.fetchone()

        if user is None:
            return render_template('DangNhap.html')
        else:
            return render_template('ThongTinBenhNhan.html')

    return render_template('DangNhap.html')

@app.route('/thongtinbenhnhan', methods=['POST'])
def thong_tin_benh_nhan():
    try:
        if request.method == 'POST':
            maBN = request.form['MaBN']
            tenBN = request.form['TenBN']
            ngaySinh = request.form['NgaySinh']
            ngayS = datetime.strptime(ngaySinh, "%d/%m/%Y").date()
            gioiTinh = request.form['GioiTinh']
            sdt = request.form['sdt']
            diaChi = request.form['DiaChi']

            cursor.execute("INSERT INTO ThongTinBenhNhan (MaBN, TenBN, NgaySinh, GioiTinh, sdt, DiaChi) VALUES (?, ?, ?, ?, ?, ?)",
                           (maBN, tenBN, ngayS, gioiTinh, sdt, diaChi))
            conn.commit()

    except Exception as e:
        flash(f'Lỗi: {str(e)}', 'error')
        return redirect(request.url)

    return render_template('ThongTinBenhNhan.html')

@app.route('/chandoan', methods=['GET', 'POST'])
def chandoan():
    if request.method == 'GET':
        cursor.execute('SELECT MaBN, TenBN, GioiTinh, NgaySinh FROM ThongTinBenhNhan')
        rows = cursor.fetchall()
        return render_template('ChanDoan.html', rows=rows)
    
    if request.method == 'POST':
        try:
            thongtin = []
            maBN = request.form['MaBN']
            thongtin.append(maBN)
            ngayKham = request.form['NgayKham']
            thongtin.append(ngayKham)

            if 'fileInput' not in request.files:
                flash('Không có hình ảnh được tải lên', 'error')
                return redirect(request.url)

            uploaded_image = request.files['fileInput']

            if uploaded_image.filename == '':
                flash('Không có tệp nào được chọn', 'error')
                return redirect(request.url)

            if not allowed_file(uploaded_image.filename, ALLOWED_EXTENSIONS):
                flash('Định dạng tệp không hợp lệ', 'error')
                return redirect(request.url)

            image_filename = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_image.filename)
            uploaded_image.save(image_filename)

            image = Image.open(image_filename)
            image = image.resize((100, 75))
            image_array = np.array(image)
            image_array = np.expand_dims(image_array, axis=0)
            image_array = image_array.astype('float32') / 255.0
             
            prediction = model.predict(image_array)[0]

            class_names = {
                0: 'actinic keratosis',
                1: 'dermatofibroma',
                2: 'seborrheic keratosis',
                3: 'basal cell carcinoma',
                4: 'pigmented benign keratosis',
                5: 'melanoma',
                6: 'squamous cell carcinoma',
                7: 'nevus',
                8: 'vascular lesion'
            }
            
            chanDoan = class_names[np.argmax(prediction)]
            phanTram = round(np.max(prediction) * 100, 2)

            return render_template(
                'KetQua.html',
                chanDoan=chanDoan,
                phanTram=phanTram,
                ngayKham=ngayKham,
                maBN=maBN,
            )

        except Exception as e:
            flash(f'Lỗi xử lý hình ảnh: {str(e)}', 'error')
            return redirect(request.url)


# Hiển thị lịch sử khám bệnh từ cơ sở dữ liệu SQL Server.
@app.route('/LSK')
def lich_su_kham():
    # Execute an SQL query to retrieve data from the LichSuKham table
    cursor.execute('SELECT * FROM LichSuKham')
    users = cursor.fetchall()
    return render_template('LichSuKham.html', users=users)

# Xử lý yêu cầu lưu kết quả dự đoán vào cơ sở dữ liệu SQL Server.
@app.route('/save_result', methods=['POST'])
def save_result():
    try:
        # Extract data from the form
        maBN = request.form['MaBN']
        ngayKham = request.form['NgayKham']
        ngayK = datetime.strptime(ngayKham, "%d/%m/%Y").date()
        chanDoan = request.form['ChanDoan']
        phanTram = request.form['PhanTram']
        # Loại bỏ ký tự '%' và chuyển đổi thành số thập phân
        phanTram = float(phanTram.rstrip('%'))

        ghiChu = request.form['GhiChu']

        # Check if the checkbox is checked
        if 'bacsi' in request.form:
            chanDoanBS = chanDoan  # Lưu chẩn đoán của bệnh nhân vào ChanDoan bên SQL
        else:
            chanDoanBS = request.form['ChanDoanBS']  # Lưu chẩn đoán của bác sĩ vào ChanDoan bên SQL

        # Insert data into the database
        cursor.execute("INSERT INTO LichSuKham (MaBN, NgayKham, ChanDoan, PhanTram, GhiChu) VALUES (?, ?, ?, ?, ?)",
                       (maBN, ngayK , chanDoanBS, phanTram,  ghiChu))
        conn.commit()

        response = {"message": "Kết quả đã được lưu thành công!"}
        return jsonify(response)

    except Exception as e:
        response = {"error": str(e)}
        return jsonify(response), 500


if __name__ == '__main__':
    app.run()
