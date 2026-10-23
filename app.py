import os
import csv
import json
import re
import socket
from flask import Flask, render_template, request, jsonify, send_file
import qrcode
from io import BytesIO

app = Flask(__name__)

# Tên miền chính thức của ứng dụng
BASE_URL = 'http://www.xuatxunguongoc.id.vn'
app.config['PREFERRED_URL_SCHEME'] = 'http'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def clean_dict(d):
    return {k.replace('\ufeff', '').strip(): (v.strip() if isinstance(v, str) else v) for k, v in d.items() if k}

def load_csv(filename):
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                return [clean_dict(row) for row in reader]
        except Exception as e:
            print(f"Lỗi đọc file {filename}: {e}")
            return []
    return []

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def get_all_data():
    return {
        "san_pham": load_csv('SAN_PHAM.csv'),
        "lo_hang": load_csv('LO_HANG.csv'),
        "chu_the": load_csv('CHU_THE.csv'),
        "hanh_trinh": load_csv('HANH_TRINH.csv'),
        "chung_nhan": load_csv('CHUNG_NHAN.csv'),
        "bang_chung": load_csv('BANG_CHUNG.csv'),
        "ledger": load_csv('LEDGER_DEMO.csv'),
        "ai_hoi_dap": load_csv('AI_HOI_DAP.csv'),
        "ai_kien_thuc": load_csv('AI_KIEN_THUC.csv'),
        "nguon_tham_khao": load_csv('NGUON_THAM_KHAO.csv')
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/init', methods=['GET'])
def api_init():
    data = get_all_data()
    products = data['san_pham']
    batches = data['lo_hang']
    local_ip = get_local_ip()
    port = request.host.split(':')[-1] if ':' in request.host else '5000'
    
    combined_products = []
    for p in products:
        pid = p.get('product_id', '')
        b = next((x for x in batches if x.get('product_id') == pid or x.get('lot_id') == p.get('primary_lot_id')), {})
        #ảnh của sản phẩm
        img = p.get('image_url') or ''
        if not img or img.startswith('Cần') or 'example' in img:
            brand_upper = p.get('brand', '').upper()
            name_upper = p.get('display_name', '').upper()
            if 'ZESPRI' in brand_upper or 'KIWI' in name_upper:
                img = 'https://images.unsplash.com/photo-1618897996318-5a901fa6ca71?w=600&q=80' # thay link ảnh chổ này
            elif 'ENVY' in brand_upper or 'TÁO' in name_upper or 'APPLE' in name_upper:
                img = 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&q=80' # thay link ảnh chổ này
            else:
                img = 'https://images.unsplash.com/photo-1588347818036-558601350947?w=600&q=80' # thay link ảnh chổ này

        combined_products.append({
            'product_id': pid,
            'slug': p.get('slug', ''),
            'display_name': p.get('display_name', ''),
            'brand': p.get('brand', ''),
            'category': p.get('category', ''),
            'country': p.get('assumed_country_of_origin', ''),
            'region': p.get('assumed_region', ''),
            'image_url': img,
            'primary_lot_id': p.get('primary_lot_id') or b.get('lot_id', ''),
            'exporter': p.get('exporter_display') or 'T&G Global Ltd',
            'importer': p.get('importer_display') or 'Công ty Cổ phần Nông sản BioViet',
            'arrived_date': b.get('arrived_vietnam_date') or '10/05/2026',
            'storage_condition': b.get('storage_condition') or 'Chuỗi lạnh 2°C'
        })
        
    return jsonify({
        "success": True,
        "products": combined_products,
        "ledger": data['ledger'],
        "qa_list": data['ai_hoi_dap'],
        "network_info": { "local_ip": local_ip, "port": port }
    })

@app.route('/api/product-detail/<product_id>', methods=['GET'])
def api_product_detail(product_id):
    data = get_all_data()
    product = next((p for p in data['san_pham'] if p.get('product_id') == product_id or p.get('slug') == product_id), None)
    
    if not product:
        return jsonify({"success": False, "message": "Không tìm thấy sản phẩm"})
        
    pid = product.get('product_id')
    lot_id = product.get('primary_lot_id')
    
    # Xử lý gán hình ảnh chính xác theo sản phẩm/thương hiệu
    img = product.get('image_url') or ''
    if not img or img.startswith('Cần') or 'example' in img:
        brand_upper = product.get('brand', '').upper()
        name_upper = product.get('display_name', '').upper()
        if 'ZESPRI' in brand_upper or 'KIWI' in name_upper:
            img = 'https://images.unsplash.com/photo-1618897996318-5a901fa6ca71?w=600&q=80' # thay link ảnh chổ này
        elif 'ENVY' in brand_upper or 'TÁO' in name_upper or 'APPLE' in name_upper:
            img = 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&q=80' # thay link ảnh chổ này
        else:
            img = 'https://images.unsplash.com/photo-1588347818036-558601350947?w=600&q=80' # thay link ảnh chổ này
    
    product_copy = dict(product)
    product_copy['image_url'] = img
    
    lot = next((b for b in data['lo_hang'] if b.get('lot_id') == lot_id or b.get('product_id') == pid), {})
    journeys = [j for j in data['hanh_trinh'] if j.get('lot_id') == lot_id]
    certs = [c for c in data['chung_nhan'] if c.get('product_id') == pid]
    evidences = [e for e in data['bang_chung'] if e.get('product_id') == pid]
    actors = [a for a in data['chu_the'] if a.get('product_id') == pid]
    faqs = [q for q in data['ai_hoi_dap'] if q.get('product_id') == pid]
    ledger_records = [l for l in data['ledger'] if l.get('lot_id') == lot_id]
    
    # Sử dụng tên miền chính thức
    qr_target_url = f"{BASE_URL}/#detail/{pid}"
    
    return jsonify({
        "success": True,
        "product": product_copy,
        "lot": lot,
        "journeys": journeys,
        "certifications": certs,
        "evidences": evidences,
        "actors": actors,
        "ledger": ledger_records,
        "faqs": faqs,
        "qr_target_url": qr_target_url
    })

@app.route('/api/generate-qr', methods=['GET'])
def generate_qr():
    url = request.args.get('url', '').strip() or "http://127.0.0.1:5000"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00a859", back_color="white")
    buf = BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/api/ai-ask', methods=['POST'])
def api_ai_ask():
    req = request.json or {}
    user_q = req.get('question', '').strip().lower()
    product_id = req.get('product_id', '').strip()
    
    data = get_all_data()
    qa_list = data.get('ai_hoi_dap', [])
    kb_list = data.get('ai_kien_thuc', [])
    
    best_answer = None
    max_score = 0
    source_found = ""
    
    stop_words = {
        'là', 'gì', 'có', 'không', 'được', 'cho', 'tôi', 'hỏi', 'với', 'như', 
        'thế', 'nào', 'về', 'này', 'ơi', 'à', 'nhé', 'em', 'anh', 'chị', 'xem', 
        'biết', 'cho', 'mấy', 'các', 'những', 'của', 'ở', 'đâu'
    }
    raw_words = re.findall(r'\w+', user_q)
    keywords = [w for w in raw_words if w not in stop_words and len(w) > 1]

    if keywords:
        for qa in qa_list:
            qa_pid = qa.get('product_id', '')
            if product_id and qa_pid and qa_pid != product_id:
                continue
                
            q_text = qa.get('user_question', '').lower()
            ans_text = qa.get('recommended_answer', '').lower()
            
            score = 0
            for kw in keywords:
                if kw in q_text:
                    score += 3
                elif kw in ans_text:
                    score += 1
            
            if score > max_score:
                max_score = score
                best_answer = qa.get('recommended_answer')
                source_found = "AI_HOI_DAP"

        for kb in kb_list:
            kb_pid = kb.get('product_id', '')
            if product_id and kb_pid and kb_pid != product_id:
                continue
                
            topic = kb.get('topic', '').lower()
            fact = kb.get('fact', '').lower()
            allowed = kb.get('allowed_answer', '').lower()
            
            score = 0
            for kw in keywords:
                if kw in topic:
                    score += 3
                if kw in fact or kw in allowed:
                    score += 1
            
            if score > max_score:
                max_score = score
                best_answer = kb.get('allowed_answer') or kb.get('fact')
                source_found = "AI_KIEN_THUC"

    if not best_answer or max_score == 0:
        best_answer = "Chưa có đủ dữ liệu kiểm chứng chính thức cho câu hỏi này. Hệ thống hiển thị thông tin dựa trên hồ sơ công khai của nhà nhập khẩu."

    return jsonify({
        "answer": best_answer, 
        "score": max_score, 
        "source": source_found
    })

if __name__ == '__main__':
    # Lắng nghe kết nối từ mạng ngoài (host='0.0.0.0')
    # Chạy ở port=5000 nếu dùng ngrok (ngrok http 5000)
    # Đổi thành port=80 nếu chạy trực tiếp trên Windows (cần bật PowerShell quyền Admin)
    app.run(host='0.0.0.0', port=5000, debug=False)
