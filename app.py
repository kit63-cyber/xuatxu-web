import os
import csv
import json
import re
import html
import hashlib
import time
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, abort
import qrcode

app = Flask(__name__)

# Cấu hình BASE URL và Scheme cho môi trường Render / Production
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'https://xuatxu-web.onrender.com').rstrip('/')
app.config['PREFERRED_URL_SCHEME'] = 'https'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
FEEDBACK_FILE = os.path.join(DATA_DIR, 'user_feedback.json')

def clean_dict(d):
    """Làm sạch key (bỏ BOM) và strip giá trị chuỗi."""
    return {k.replace('\ufeff', '').strip(): (v.strip() if isinstance(v, str) else v) for k, v in d.items() if k}

def load_csv(filename):
    """Đọc tệp CSV với utf-8-sig an toàn."""
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

def get_base_url():
    """Xác định Base URL HTTPS an toàn khi chạy trên Render hoặc local."""
    # Nếu biến môi trường được cấu hình, ưu tiên dùng
    if os.environ.get('PUBLIC_BASE_URL'):
        return os.environ.get('PUBLIC_BASE_URL').rstrip('/')
    
    # Kiểm tra header proxy
    host = request.headers.get('X-Forwarded-Host', request.host)
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme or 'https')
    if 'onrender.com' in host or 'id.vn' in host:
        scheme = 'https'
    return f"{scheme}://{host}"

def get_all_data():
    """Tải toàn bộ bộ dữ liệu chuẩn hóa v1.1."""
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
        "nguon_tham_khao": load_csv('NGUON_THAM_KHAO.csv'),
        "noi_dung_web": load_csv('NOI_DUNG_WEB.csv'),
        "display_cards": load_csv('PUBLIC_DISPLAY_CARDS.csv'),
        "claims": load_csv('CLAIM_EVIDENCE.csv'),
        "source_usage": load_csv('SOURCE_USAGE_STATUS.csv'),
        "product_source_links": load_csv('PRODUCT_SOURCE_LINKS.csv'),
        "vichi_observations": load_csv('VICHI_OBSERVATIONS.csv'),
        "tech_events": load_csv('DEMO_EVENTS.csv'),
        "tech_hash_chain": load_csv('DEMO_HASH_CHAIN.csv'),
        "kiem_thu": load_csv('KIEM_THU.csv')
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/init', methods=['GET'])
def api_init():
    """Khởi tạo ứng dụng: Trả về 02 hồ sơ sản phẩm thực tế tại VICHI và dữ liệu liên quan."""
    data = get_all_data()
    products = data['san_pham']
    
    clean_products = []
    for p in products:
        pid = p.get('product_id', '')
        # Đường dẫn ảnh thực tế tại VICHI
        img = p.get('image_url') or ''
        if not img or not img.startswith('/static/'):
            if 'ENVY' in pid:
                img = '/static/images/vichi_envy_bag.jpg'
            elif 'ZESPRI' in pid:
                img = '/static/images/vichi_zespri_gold_4.jpg'
        
        # Chỉ giữ thông tin có nguồn thực tế, KHÔNG tự bịa số lô, nhà nhập khẩu hay ngày đến
        clean_products.append({
            'product_id': pid,
            'slug': p.get('slug', ''),
            'display_name': p.get('display_name', ''),
            'brand': p.get('brand', ''),
            'category': p.get('category', ''),
            'assumed_country_of_origin': p.get('assumed_country_of_origin', ''),
            'origin_iso2': p.get('origin_iso2', ''),
            'variety': p.get('variety', ''),
            'description': p.get('description', ''),
            'characteristics': p.get('characteristics', ''),
            'packaging_demo': p.get('packaging_demo', ''),
            'manufacturer_display': p.get('manufacturer_display', ''),
            'retailer_display': p.get('retailer_display', 'Ghi nhận tại VICHI MARKET'),
            'image_url': img,
            'image_alt': p.get('image_alt', ''),
            'qr_target': p.get('qr_target', ''),
            'consumer_banner': p.get('consumer_banner', '')
        })

    return jsonify({
        "success": True,
        "positioning": "XuatXu – Biết nguồn, hiểu bằng chứng",
        "products": clean_products,
        "qa_list": data['ai_hoi_dap'],
        "sources": data['nguon_tham_khao'],
        "display_cards": data['display_cards'],
        "base_url": get_base_url()
    })

@app.route('/api/product-detail/<product_id>', methods=['GET'])
def api_product_detail(product_id):
    """Chi tiết hồ sơ sản phẩm: Hiển thị 03 thẻ thông tin có nguồn + 01 khối phạm vi xác minh."""
    data = get_all_data()
    product = next((p for p in data['san_pham'] if p.get('product_id') == product_id or p.get('slug') == product_id), None)
    
    if not product:
        return jsonify({"success": False, "message": "Không tìm thấy hồ sơ sản phẩm"}), 404
        
    pid = product.get('product_id')
    
    # Đảm bảo dùng ảnh thực tế tại VICHI
    img = product.get('image_url') or ''
    if not img or not img.startswith('/static/'):
        if 'ENVY' in pid:
            img = '/static/images/vichi_envy_bag.jpg'
        elif 'ZESPRI' in pid:
            img = '/static/images/vichi_zespri_gold_4.jpg'
    
    product_copy = dict(product)
    product_copy['image_url'] = img
    
    # Lấy thông tin lô (trường lot_code rỗng, TUYỆT ĐỐI không render META lot_id làm mã lô)
    lot = next((b for b in data['lo_hang'] if b.get('product_id') == pid), {})
    
    # 08 thẻ hiển thị tuyển chọn theo PUBLIC_DISPLAY_CARDS.csv (04 thẻ/sản phẩm: 3 thẻ thông tin + 1 giới hạn)
    cards = [c for c in data['display_cards'] if c.get('product_id') == pid]
    cards = sorted(cards, key=lambda c: int(c.get('sort_order') or 999))
    
    # 14 bản ghi bằng chứng chi tiết trong BANG_CHUNG.csv
    evidences = [e for e in data['bang_chung'] if e.get('product_id') == pid]
    
    # 06 tình huống tuyên bố - bằng chứng CLAIM_EVIDENCE.csv
    claims = [cl for cl in data['claims'] if cl.get('product_id') == pid]
    
    # Chứng nhận
    certs = [c for c in data['chung_nhan'] if c.get('product_id') == pid]
    
    # Nguồn tham khảo liên quan
    used_source_ids = set()
    for c in cards:
        if c.get('source_ids'):
            for s in c['source_ids'].split(','):
                used_source_ids.add(s.strip())
    for e in evidences:
        if e.get('source_id'):
            used_source_ids.add(e['source_id'].strip())
            
    sources = [s for s in data['nguon_tham_khao'] if s.get('source_id') in used_source_ids]
    
    # 19 câu hỏi đáp chuẩn hóa lọc theo sản phẩm
    faqs = [q for q in data['ai_hoi_dap'] if q.get('product_id') == pid]
    
    # Tạo URL HTTPS chuẩn cho mã QR
    base_url = get_base_url()
    qr_target_url = f"{base_url}/#detail/{pid}"
    
    return jsonify({
        "success": True,
        "product": product_copy,
        "lot": lot,
        "display_cards": cards,
        "evidences": evidences,
        "claims": claims,
        "sources": sources,
        "certifications": certs,
        "faqs": faqs,
        "journeys": [],  # Rỗng theo đúng bộ dữ liệu thực tế v1.1
        "ledger": [],    # Rỗng theo đúng bộ dữ liệu thực tế v1.1
        "qr_target_url": qr_target_url
    })

@app.route('/api/generate-qr', methods=['GET'])
def generate_qr():
    """Tạo ảnh QR Code HTTPS màu đen chuẩn trỏ chính xác đến hồ sơ sản phẩm."""
    product_id = request.args.get('product_id', '').strip()
    target_url = request.args.get('url', '').strip()
    
    base_url = get_base_url()
    
    if product_id:
        final_url = f"{base_url}/#detail/{product_id}"
    elif target_url:
        # Giới hạn hostname hợp lệ tránh open-redirect/phishing
        if target_url.startswith('/') or target_url.startswith('#') or 'xuatxu' in target_url or '127.0.0.1' in target_url or 'localhost' in target_url:
            final_url = target_url
        else:
            final_url = f"{base_url}/#detail/P-ENVY-VICHI-01"
    else:
        final_url = f"{base_url}/#detail/P-ENVY-VICHI-01"
        
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2
    )
    qr.add_data(final_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/api/ai-ask', methods=['POST'])
@app.route('/api/ai/ask', methods=['POST'])
def api_ai_ask():
    """Trợ lý giải thích thông tin XuatXu: Trả lời dựa trên 19 nội dung hỏi đáp có nguồn tham chiếu và 10 hồ sơ nông sản thực tế."""
    req = request.json or {}
    user_q = (req.get('question') or req.get('user_q') or '').strip()
    qa_id = req.get('qa_id', '').strip()
    product_id = req.get('product_id', '').strip()
    
    data = get_all_data()
    qa_list = data.get('ai_hoi_dap', [])
    products = data.get('san_pham', [])
    sources_dict = {s.get('source_id'): s for s in data.get('nguon_tham_khao', [])}
    
    matched_qa = None
    
    # 1. Ưu tiên khớp chính xác qa_id
    if qa_id:
        matched_qa = next((q for q in qa_list if q.get('qa_id') == qa_id), None)
        
    # 2. Khớp theo câu hỏi người dùng
    if not matched_qa and user_q:
        q_norm = user_q.lower().strip()
        candidates = [q for q in qa_list if (not product_id or q.get('product_id') == product_id)]
        
        # Khớp chính xác câu hỏi
        for c in candidates:
            if c.get('user_question', '').lower().strip() == q_norm:
                matched_qa = c
                break
                
        # Khớp từ khóa chủ đề (topic-matching) có kiểm soát
        if not matched_qa:
            best_score = 0
            words = [w for w in re.findall(r'[\w]+', q_norm) if len(w) > 1]
            
            for c in candidates:
                q_text = c.get('user_question', '').lower()
                ans_text = (c.get('recommended_answer') or c.get('official_answer') or '').lower()
                score = 0
                
                # So khớp từ khóa trực tiếp
                for w in words:
                    if w in q_text:
                        score += 3
                    elif w in ans_text:
                        score += 1
                        
                # Nếu câu hỏi trùng cụm từ
                if q_text in q_norm or q_norm in q_text:
                    score += 8
                    
                if score > best_score:
                    best_score = score
                    matched_qa = c
                    
            if best_score < 3:
                matched_qa = None

    if matched_qa:
        answer_text = matched_qa.get('recommended_answer') or matched_qa.get('official_answer') or ''
        source_ids = re.findall(r'SRC-[A-Z0-9-]+', answer_text)
        sources_info = [sources_dict[sid] for sid in source_ids if sid in sources_dict]
        
        return jsonify({
            "success": True,
            "answer": answer_text,
            "qa_id": matched_qa.get('qa_id'),
            "product_id": matched_qa.get('product_id'),
            "question": matched_qa.get('user_question'),
            "source_ids": ", ".join(source_ids) if source_ids else (matched_qa.get('source_policy') or 'Kho tri thức XuatXu'),
            "sources": sources_info,
            "source_nature": "Kho tri thức chuẩn hóa XuatXu",
            "matched": True
        })

    # 3. Tra cứu sản phẩm trong hệ thống nếu câu hỏi nhắc đến tên quả / thương hiệu
    if user_q:
        q_lower = user_q.lower()
        matched_prod = None
        for p in products:
            p_name = (p.get('display_name') or '').lower()
            pid = (p.get('product_id') or '').lower()
            
            key_terms = []
            if 'nho' in p_name: key_terms.extend(['nho', 'shine muscat', 'sữa'])
            elif 'dưa lưới' in p_name: key_terms.extend(['dưa lưới', 'danny green', 'hoàng kim'])
            elif 'bưởi' in p_name: key_terms.extend(['bưởi', 'huka', 'da xanh'])
            elif 'xoài' in p_name: key_terms.extend(['xoài', 'cát chu', 'mr 9', 'mr. 9', 'chú mười'])
            elif 'lê' in p_name: key_terms.extend(['lê', 'eloasis', 'k-pear', 'lê nâu', 'hàn quốc'])
            elif 'quýt' in p_name: key_terms.extend(['quýt', 'tony fruit', 'quýt úc'])
            elif 'kim quất' in p_name: key_terms.extend(['kim quất', 'quất', 'đài loan'])
            elif 'măng cụt' in p_name: key_terms.extend(['măng cụt', 'nam bộ'])
            elif 'envy' in p_name: key_terms.extend(['envy', 'táo'])
            elif 'zespri' in p_name: key_terms.extend(['zespri', 'kiwi'])
            
            if any(term in q_lower for term in key_terms) or (pid and pid in q_lower):
                matched_prod = p
                break
                
        if matched_prod:
            p_name = matched_prod.get('display_name')
            p_origin = matched_prod.get('assumed_country_of_origin') or 'Ghi nhận trên nhãn'
            p_brand = matched_prod.get('brand') or 'Thương hiệu đối tác'
            p_desc = matched_prod.get('description') or ''
            p_retailer = matched_prod.get('retailer_display', 'VICHI MARKET')
            p_pack = matched_prod.get('packaging_demo', 'Quy cách chuẩn')
            
            if any(w in q_lower for w in ['giá', 'bao nhiêu', 'tiền', 'cost', 'bán']):
                answer = f"Sản phẩm {p_name} có quy cách '{p_pack}' được ghi nhận trực tiếp tại điểm bán {p_retailer}. Mức giá bán lẻ được cập nhật minh bạch tại thời điểm khảo sát và hiển thị đầy đủ trong hồ sơ chi tiết."
            elif any(w in q_lower for w in ['xuất xứ', 'nước nào', 'ở đâu', 'nguồn gốc', 'nhập khẩu']):
                answer = f"Sản phẩm {p_name} thuộc thương hiệu {p_brand}, xuất xứ ghi nhận là {p_origin}. Thông tin này được ghi nhận từ tem nhãn thực tế tại điểm bán {p_retailer} và liên kết nguồn xác minh thương hiệu."
            elif any(w in q_lower for w in ['mã lô', 'lô', 'hải quan', 'chứng chỉ', 'batch', 'lot']):
                answer = f"Đối với {p_name}: Nền tảng XuatXu thực hiện phân tầng thông tin - hiển thị tem nhãn quan sát thực tế tại điểm bán và công khai giới hạn xác minh cấp lô hàng (chưa khẳng định lô khi chưa có chứng từ gốc đối chiếu)."
            else:
                answer = f"{p_name}: {p_desc} Sản phẩm mang thương hiệu {p_brand}, xuất xứ {p_origin}, được ghi nhận tại điểm bán {p_retailer}."
                
            return jsonify({
                'success': True,
                'answer': answer,
                'source_ids': f"Hồ sơ {matched_prod.get('product_id')}",
                'source_nature': 'Ghi nhận thực tế tại VICHI MARKET',
                'matched': True
            })
            
        # 4. Câu hỏi chung về hệ thống
        if any(k in q_lower for k in ['xuatxu', 'hệ thống', 'làm sao', 'cách dùng', 'chức năng', 'lợi ích']):
            answer = "Hệ thống XuatXu giúp bạn: (1) Tra cứu hồ sơ minh bạch nông sản bán lẻ; (2) Quét và tạo mã QR truy cập nhanh; (3) Kiểm tra tính toàn vẹn dữ liệu với mô phỏng mã băm SHA-256; (4) Trợ lý AI giải đáp nguồn gốc và tem nhãn."
        elif any(k in q_lower for k in ['3 không', 'nguyên tắc', 'tẩy xanh', 'greenwashing', 'minh bạch']):
            answer = "Nguyên tắc 3 Không của XuatXu: (1) Không bịa đặt mã lô khi chưa có chứng từ gốc; (2) Không nhầm lẫn giữa cam kết thương hiệu và chứng nhận cấp lô; (3) Không tự đưa phán quyết cảm tính, minh bạch ranh giới xác minh."
        elif any(k in q_lower for k in ['sha256', 'hash', 'mã băm', 'mật mã', 'blockchain']):
            answer = "Mô phỏng SHA-256 trên XuatXu chứng minh tính toàn vẹn dữ liệu: nếu bất kỳ thông tin nào trong chuỗi (như tên cơ sở hay ngày thu hoạch) bị chỉnh sửa, chữ ký mã băm sẽ không khớp (FAIL) ngay lập tức."
        else:
            answer = f"Cảm ơn bạn đã hỏi về '{html.escape(user_q)}'. Bạn có thể nhấn vào các gợi ý câu hỏi chuẩn hóa bên trên, hoặc hỏi về thông tin xuất xứ, tem nhãn, giá cả của 10 loại trái cây trên hệ thống!"
            
        return jsonify({
            'success': True,
            'answer': answer,
            'source_ids': 'Kho tri thức XuatXu',
            'source_nature': 'Trợ lý thông tin xuất xứ',
            'matched': True
        })
        
    return jsonify({
        "success": False,
        "message": "Vui lòng nhập câu hỏi cần giải đáp."
    }), 400

@app.route('/api/tech-demo', methods=['GET'])
@app.route('/api/tech/demo-chain', methods=['GET'])
def api_tech_demo():
    """Mô phỏng kỹ thuật độc lập: 05 sự kiện giả định và chuỗi hash SHA-256."""
    data = get_all_data()
    events = data.get('tech_events', [])
    chain = data.get('tech_hash_chain', [])
    
    return jsonify({
        "success": True,
        "is_simulated": True,
        "onchain_verified": False,
        "banner": "DỮ LIỆU GIẢ LẬP – KHÔNG PHẢI CHỨNG TỪ CỦA VICHI",
        "description": "Mô phỏng kỹ thuật chuỗi băm SHA-256 phục vụ nghiên cứu học thuật – Không phải giao dịch blockchain on-chain",
        "events": events,
        "hash_chain": chain,
        "chain": chain
    })

@app.route('/api/tech-demo/verify', methods=['POST'])
@app.route('/api/tech/verify', methods=['POST'])
def api_tech_demo_verify():
    """Kiểm tra tính toàn vẹn của chuỗi băm SHA-256 (cho phép thử nghiệm sửa dữ liệu để phát hiện sai lệch)."""
    req = request.json or {}
    custom_chain = req.get('chain')
    
    data = get_all_data()
    chain = custom_chain if custom_chain is not None else data.get('tech_hash_chain', [])
    
    results = []
    prior = 'GENESIS_SHA256_SIM_ONLY'
    is_valid = True
    broken_step = None
    
    for idx, r in enumerate(chain, 1):
        prev_hash = r.get('previous_hash', '')
        payload = r.get('canonical_payload', '')
        expected_prev = prior
        calculated_hash = hashlib.sha256((expected_prev + '|' + payload).encode('utf-8')).hexdigest()
        
        step_valid = (prev_hash == expected_prev) and (r.get('sha256') == calculated_hash)
        if not step_valid and is_valid:
            is_valid = False
            broken_step = idx
            
        results.append({
            'step': idx,
            'record_id': r.get('record_id', f'SIM-H{idx:02d}'),
            'event_id': r.get('event_id', f'SIM-E{idx:02d}'),
            'previous_hash': prev_hash,
            'expected_previous_hash': expected_prev,
            'canonical_payload': payload,
            'sha256': r.get('sha256', ''),
            'calculated_hash': calculated_hash,
            'is_valid': step_valid,
            'local_hash_verified': step_valid,
            'onchain_verified': False
        })
        prior = r.get('sha256', calculated_hash)
        
    msg = "PASS: Toàn bộ 5 sự kiện giả định khớp chữ ký SHA-256. Chuỗi nhất quán cục bộ." if is_valid else f"FAIL: Phát hiện sai lệch tại bước #{broken_step}! Dữ liệu bị thay đổi đã phá vỡ tính toàn vẹn của chuỗi băm."
    
    return jsonify({
        "success": True,
        "is_valid": is_valid,
        "chain_valid": is_valid,
        "broken_step": broken_step,
        "message": msg,
        "records": results
    })
    
    return jsonify({
        "success": True,
        "is_valid": is_valid,
        "broken_step": broken_step,
        "message": msg,
        "records": results
    })

@app.route('/api/feedback', methods=['GET', 'POST'])
def api_feedback():
    """Tiếp nhận và lưu trữ phản hồi người dùng thực tế sau khi trải nghiệm hồ sơ."""
    if request.method == 'POST':
        req = request.json or {}
        name = html.escape(str(req.get('name', 'Khách tham quan')).strip()[:100])
        product_id = html.escape(str(req.get('product_id', '')).strip()[:50])
        amount = html.escape(str(req.get('amount', 'Vừa đủ')).strip()[:50])
        comment = html.escape(str(req.get('comment', '')).strip()[:500])
        
        if not comment:
            return jsonify({'success': False, 'message': 'Vui lòng nhập nội dung góp ý'}), 400
            
        feedback_item = {
            'id': int(time.time() * 1000),
            'name': name or 'Khách tham quan',
            'product_id': product_id,
            'amount': amount,
            'comment': comment,
            'created_at': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        feedbacks = []
        if os.path.exists(FEEDBACK_FILE):
            try:
                with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            except Exception:
                feedbacks = []
                
        feedbacks.insert(0, feedback_item)
        try:
            with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                json.dump(feedbacks[:100], f, ensure_ascii=False, indent=2)
        except Exception as e:
            return jsonify({'success': False, 'message': f'Lỗi lưu phản hồi: {e}'}), 500
            
        return jsonify({
            'success': True,
            'message': 'Cảm ơn bạn đã đóng góp phản hồi thực tế!',
            'feedback': feedback_item
        })
    else:
        # GET danh sách phản hồi thực
        feedbacks = []
        if os.path.exists(FEEDBACK_FILE):
            try:
                with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                    feedbacks = json.load(f)
            except Exception:
                feedbacks = []
        return jsonify({'success': True, 'feedbacks': feedbacks})

if __name__ == '__main__':
    # Chạy local server
    app.run(host='0.0.0.0', port=5000, debug=False)
