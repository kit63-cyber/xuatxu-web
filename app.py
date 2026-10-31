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
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Cấu hình BASE URL và Scheme cho môi trường Render / Production
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'https://xuatxu-web.onrender.com').rstrip('/')
app.config['PREFERRED_URL_SCHEME'] = 'https'

@app.after_request
def add_no_cache_headers(response):
    if response.mimetype == 'text/html':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    return response

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
        "simulated_journeys": load_csv('MO_PHONG_HANH_TRINH.csv'),
        "simulated_documents": load_csv('MO_PHONG_DANH_MUC_CHUNG_TU.csv'),
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
            'consumer_banner': p.get('consumer_banner', ''),
            'profile_type': p.get('profile_type', ''),
            'simulation_notice': p.get('simulation_notice', ''),
            'price_display': p.get('price_display', ''),
            'price_nature': p.get('price_nature', ''),
            'photo_nature': p.get('photo_nature', ''),
            'country_nature': p.get('country_nature', '')
        })

    return jsonify({
        "success": True,
        "positioning": "XuatXu – Biết nguồn, hiểu bằng chứng",
        "products": clean_products,
        "qa_list": data['ai_hoi_dap'],
        "knowledge_list": data['ai_kien_thuc'],
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
    
    # Nguồn tham khảo liên quan (tổng hợp từ sản phẩm, thẻ hiển thị, bằng chứng, tuyên bố và liên kết nguồn)
    used_source_ids = set()
    for raw_src in [product.get('source_ids', '')]:
        for sid in re.findall(r'SRC-[A-Z0-9-]+', str(raw_src)):
            used_source_ids.add(sid)
    for c in cards:
        for sid in re.findall(r'SRC-[A-Z0-9-]+', str(c.get('source_ids', ''))):
            used_source_ids.add(sid)
    for e in evidences:
        for sid in re.findall(r'SRC-[A-Z0-9-]+', str(e.get('source_id', ''))):
            used_source_ids.add(sid)
    for cl in claims:
        for sid in re.findall(r'SRC-[A-Z0-9-]+', str(cl.get('source_id', ''))):
            used_source_ids.add(sid)
    for psl in data.get('product_source_links', []):
        if psl.get('product_id') == pid and psl.get('source_id'):
            used_source_ids.add(psl.get('source_id').strip())
            
    sources = [s for s in data['nguon_tham_khao'] if s.get('source_id') in used_source_ids]
    
    # 12 câu hỏi đáp chuẩn hóa & 12 mục tri thức chuẩn hóa lọc theo sản phẩm (tổng 108 câu & 108 tri thức trên 9 sản phẩm)
    faqs = [q for q in data['ai_hoi_dap'] if q.get('product_id') == pid]
    knowledge_items = [k for k in data['ai_kien_thuc'] if k.get('product_id') == pid]
    is_sim = product.get('profile_type') == 'SIMULATED_IMPORT_EXPANSION'
    
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
        "knowledge_items": knowledge_items,
        "journeys": [],  # Rỗng đối với hồ sơ thực tế tại VICHI theo đúng bộ dữ liệu v1.1
        "ledger": [],    # Mô phỏng SHA-256 được trình diễn trong tab riêng
        "simulated_journey": [j for j in data['simulated_journeys'] if j.get('product_id') == pid] if is_sim else [],
        "simulated_documents": [d for d in data['simulated_documents'] if d.get('product_id') == pid] if is_sim else [],
        "is_simulated": is_sim,
        "qr_target_url": qr_target_url
    })

@app.route('/api/generate-qr', methods=['GET'])
def generate_qr():
    """Tạo ảnh QR Code HTTPS màu đen chuẩn trỏ chính xác đến hồ sơ sản phẩm (đã kiểm tra product_id trong SAN_PHAM.csv)."""
    product_id = request.args.get('product_id', '').strip()
    target_url = request.args.get('url', '').strip()
    
    data = get_all_data()
    valid_products = {p.get('product_id'): p for p in data.get('san_pham', []) if p.get('product_id')}
    for p in data.get('san_pham', []):
        if p.get('slug') and p.get('product_id'):
            valid_products[p.get('slug')] = p
            
    base_url = get_base_url()
    
    if product_id:
        if product_id not in valid_products:
            return jsonify({"success": False, "message": "Mã sản phẩm không nằm trong SAN_PHAM.csv"}), 400
        canonical_id = valid_products[product_id].get('product_id')
        final_url = f"{base_url}/#detail/{canonical_id}"
    elif target_url:
        # Chỉ cho phép host đã cấu hình trong PUBLIC_BASE_URL hoặc đường dẫn nội bộ
        allowed_host = PUBLIC_BASE_URL.replace('https://', '').replace('http://', '').split('/')[0]
        if target_url.startswith('/#detail/') or target_url.startswith('#detail/'):
            req_pid = target_url.split('#detail/')[-1].strip()
            canonical_id = valid_products.get(req_pid, {}).get('product_id', 'P-ENVY-VICHI-01')
            final_url = f"{base_url}/#detail/{canonical_id}"
        elif allowed_host and allowed_host in target_url:
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

def _detect_product_from_question(q_lower, products):
    """Nhận diện 1 trong 9 sản phẩm từ câu hỏi tự do của người dùng (dùng ranh giới từ chính xác)."""
    product_patterns = [
        ('P-GRAPE-SIM-03', [r'\bnho sữa\b', r'\bshine muscat\b', r'\bnho hàn\b', r'\bnho\b']),
        ('P-BLUBERRY-SIM-04', [r'\bblueberry\b', r'\bviệt quất\b', r'\bbluberry\b']),
        ('P-CHERRY-SIM-05', [r'\bcherry\b', r'\banh đào\b']),
        ('P-ORANGE-SIM-06', [r'\bcam navel\b', r'\bcam ai cập\b', r'\bnavel\b', r'\bquả cam\b', r'\btrái cam\b']),
        ('P-PEAR-SIM-07', [r'\blê nâu\b', r'\blê hàn quốc\b', r'\bk-pear\b', r'\beloasis\b', r'\bquả lê\b', r'\btrái lê\b']),
        ('P-MANDARIN-SIM-08', [r'\bquýt úc\b', r'\bquýt nhập khẩu\b', r'\bmandarin\b', r'\bquýt\b']),
        ('P-KUMQUAT-SIM-09', [r'\bkim quất\b', r'\bkumquat\b', r'\btắc đài loan\b']),
        ('P-ENVY-VICHI-01', [r'\benvy\b', r'\btáo envy\b', r't&g', r'\btáo\b']),
        ('P-ZESPRI-VICHI-01', [r'\bzespri\b', r'\bkiwi\b', r'\bsungold\b'])
    ]
    for pid, patterns in product_patterns:
        if pid.lower() in q_lower or any(re.search(pat, q_lower) for pat in patterns):
            return next((p for p in products if p.get('product_id') == pid), None)
    return None

@app.route('/api/ai-ask', methods=['POST'])
@app.route('/api/ai/ask', methods=['POST'])
def api_ai_ask():
    """Trợ lý giải thích thông tin có nguồn dựa trên AI_HOI_DAP.csv (108 câu) và AI_KIEN_THUC.csv (108 mục)."""
    req = request.json or {}
    user_q = (req.get('question') or req.get('user_q') or '').strip()
    qa_id = req.get('qa_id', '').strip()
    product_id = req.get('product_id', '').strip()
    
    data = get_all_data()
    qa_list = data.get('ai_hoi_dap', [])
    kb_list = data.get('ai_kien_thuc', [])
    products = data.get('san_pham', [])
    sources_dict = {s.get('source_id'): s for s in data.get('nguon_tham_khao', [])}
    
    matched_qa = None
    
    # 1. Ưu tiên khớp chính xác qa_id
    if qa_id:
        matched_qa = next((q for q in qa_list if q.get('qa_id') == qa_id), None)
        
    # Tự động nhận diện sản phẩm trong câu hỏi nếu chưa truyền product_id
    detected_product = None
    if user_q:
        detected_product = _detect_product_from_question(user_q.lower(), products)
    effective_pid = product_id or (detected_product.get('product_id') if detected_product else '')
    
    # 2. Khớp theo câu hỏi người dùng trong AI_HOI_DAP.csv
    if not matched_qa and user_q:
        q_norm = user_q.lower().strip()
        candidates = [q for q in qa_list if (not effective_pid or q.get('product_id') == effective_pid)]
        
        # Khớp chính xác câu hỏi
        for c in candidates:
            if c.get('user_question', '').lower().strip() == q_norm:
                matched_qa = c
                break
                
        # Khớp theo chủ đề (topic) + từ khóa có kiểm soát
        if not matched_qa:
            topic_hints = []
            if any(w in q_norm for w in ['xuất xứ', 'nước nào', 'nguồn gốc', 'trồng ở đâu']):
                topic_hints.extend(['origin', 'grower'])
            if any(w in q_norm for w in ['giá', 'bao nhiêu', 'tiền', 'đắt']):
                topic_hints.append('price')
            if any(w in q_norm for w in ['mã lô', 'số lô', 'lô hàng', 'lot', 'batch', 'thùng']):
                topic_hints.extend(['lot', 'sp_code', 'traceability'])
            if any(w in q_norm for w in ['chứng nhận', 'organic', 'hữu cơ', 'globalg.a.p', 'globalgap', 'biogro', 'môi trường', 'kiểm dịch', 'chứng chỉ']):
                topic_hints.extend(['certification', 'organic', 'gap', 'import_docs'])
            if any(w in q_norm for w in ['blockchain', 'sha-256', 'sha256', 'hash', 'mã băm', 'on-chain']):
                topic_hints.append('blockchain')
            if any(w in q_norm for w in ['tẩy xanh', 'greenwashing', 'gian lận']):
                topic_hints.append('greenwashing')
            if any(w in q_norm for w in ['hành trình', 'chuỗi cung ứng', 'nhập khẩu', 'tờ khai', 'vận chuyển']):
                topic_hints.extend(['journey', 'importer', 'import_docs'])
            if any(w in q_norm for w in ['ảnh', 'hình ảnh', 'wikimedia', 'minh họa', 'chụp']):
                topic_hints.extend(['photo', 'packaging'])
            if any(w in q_norm for w in ['vichi', 'siêu thị', 'thử nghiệm', 'bán tại', 'bán ở']):
                topic_hints.extend(['vichi_scope', 'simulation', 'overview'])
            if any(w in q_norm for w in ['qr', 'quét mã']):
                topic_hints.append('qr_scope')
            if any(w in q_norm for w in ['mô phỏng', 'giả định', 'thật không']):
                topic_hints.extend(['simulation', 'overview'])

            stop_words = {'có', 'không', 'là', 'gì', 'ở', 'tại', 'cho', 'của', 'và', 'này', 'được', 'như', 'thế', 'về', 'trong', 'với', 'hay', 'phải', 'từ', 'khi', 'đã', 'sẽ', 'cần', 'một', 'các', 'những', 'sản', 'phẩm'}
            words = [w for w in re.findall(r'[\w]+', q_norm) if len(w) > 1 and w not in stop_words]
            intent_terms = ['giá', 'bao nhiêu', 'xuất xứ', 'nước nào', 'quy cách', 'đóng gói', 'hành trình', 'tờ khai', 'hải quan', 'kiểm dịch', 'organic', 'bền vững', 'blockchain', 'hiểu nhầm', 'nguồn thông tin', 'chụp tại vichi', 'mã lô', 'tẩy xanh']
            best_score = 0
            
            for c in candidates:
                q_text = c.get('user_question', '').lower()
                ans_text = (c.get('recommended_answer') or c.get('official_answer') or '').lower()
                score = 0
                
                for term in intent_terms:
                    if term in q_norm and term in q_text:
                        score += 10
                for w in words:
                    if w in q_text:
                        score += 4
                    elif w in ans_text:
                        score += 1
                if q_text in q_norm or q_norm in q_text:
                    score += 8
                    
                if score > best_score:
                    best_score = score
                    matched_qa = c
                    
            if best_score < 4:
                matched_qa = None

    if matched_qa:
        prod_obj = next((p for p in products if p.get('product_id') == matched_qa.get('product_id')), None)
        is_sim_prod = (prod_obj and prod_obj.get('profile_type') == 'SIMULATED_IMPORT_EXPANSION')
        answer_text = matched_qa.get('recommended_answer') or matched_qa.get('official_answer') or ''
        source_ids = list(dict.fromkeys(re.findall(r'SRC-[A-Z0-9-]+', answer_text)))
        sources_info = [sources_dict[sid] for sid in source_ids if sid in sources_dict]
        
        return jsonify({
            "success": True,
            "answer": answer_text,
            "qa_id": matched_qa.get('qa_id'),
            "product_id": matched_qa.get('product_id'),
            "profile_type": prod_obj.get('profile_type') if prod_obj else '',
            "question": matched_qa.get('user_question'),
            "source_ids": ", ".join(source_ids) if source_ids else (matched_qa.get('source_policy') or ('SRC-SIM-POLICY' if is_sim_prod else 'Kho tri thức XuatXu')),
            "sources": sources_info,
            "source_nature": "SIMULATION_ONLY" if is_sim_prod else "Kho tri thức chuẩn hóa XuatXu",
            "matched": True
        })

    # 3. Tra cứu tiếp trong AI_KIEN_THUC.csv (108 mục tri thức chuẩn hóa) nếu chưa khớp trực tiếp câu hỏi
    if user_q and effective_pid:
        q_norm = user_q.lower()
        stop_words = {'có', 'không', 'là', 'gì', 'ở', 'đâu', 'tại', 'cho', 'của', 'và', 'này', 'được', 'như', 'thế', 'nào', 'bao', 'nhiêu', 'về', 'trong', 'với', 'hay', 'phải', 'từ', 'khi', 'đã', 'sẽ', 'cần', 'một', 'các', 'những', 'câu', 'hỏi', 'danh', 'mục', 'ngoài', 'hoàn', 'toàn'}
        kb_candidates = [k for k in kb_list if k.get('product_id') == effective_pid]
        best_kb = None
        best_kb_score = 0
        words = [w for w in re.findall(r'[\w]+', q_norm) if len(w) > 1 and w not in stop_words]
        for kb in kb_candidates:
            kb_text = ((kb.get('topic') or '') + ' ' + (kb.get('fact') or '') + ' ' + (kb.get('allowed_answer') or '')).lower()
            sc = sum(2 for w in words if w in kb_text)
            if sc > best_kb_score:
                best_kb_score = sc
                best_kb = kb
        if best_kb and best_kb_score >= 6:
            prod_obj = next((p for p in products if p.get('product_id') == effective_pid), None)
            is_sim_prod = (prod_obj and prod_obj.get('profile_type') == 'SIMULATED_IMPORT_EXPANSION')
            ans_text = best_kb.get('allowed_answer') or best_kb.get('fact') or ''
            source_ids = list(dict.fromkeys(re.findall(r'SRC-[A-Z0-9-]+', ans_text)))
            sources_info = [sources_dict[sid] for sid in source_ids if sid in sources_dict]
            return jsonify({
                "success": True,
                "answer": ans_text,
                "kb_id": best_kb.get('kb_id'),
                "product_id": effective_pid,
                "profile_type": prod_obj.get('profile_type') if prod_obj else '',
                "source_ids": ", ".join(source_ids) if source_ids else ('SRC-SIM-POLICY' if is_sim_prod else 'Kho tri thức XuatXu'),
                "sources": sources_info,
                "source_nature": "SIMULATION_ONLY" if is_sim_prod else "Kho tri thức chuẩn hóa XuatXu",
                "matched": True
            })

    # 4. Khi có sản phẩm (truyền qua product_id hoặc nhận diện từ câu hỏi) nhưng câu hỏi ngoài phạm vi kịch bản:
    # Phân biệt nghiêm ngặt VICHI_OBSERVED và SIMULATED_IMPORT_EXPANSION, tuyệt đối không khẳng định hàng giả định là hàng tại VICHI.
    if effective_pid and user_q:
        selected_product = next((p for p in products if p.get('product_id') == effective_pid), None)
        if selected_product:
            is_sim = selected_product.get('profile_type') == 'SIMULATED_IMPORT_EXPANSION'
            p_name = selected_product.get('display_name', effective_pid)
            if is_sim:
                answer = (
                    f"{p_name} thuộc nhóm Hồ sơ mô phỏng mở rộng (SIMULATED_IMPORT_EXPANSION): "
                    f"ảnh hiển thị là ảnh minh họa từ nguồn mở (Wikimedia Commons), còn xuất xứ ({selected_product.get('assumed_country_of_origin')}), "
                    f"mức giá ({selected_product.get('price_display')}) và hành trình 5 bước chỉ là dữ liệu giả định phục vụ trình diễn giao diện. "
                    f"Sản phẩm này KHÔNG thuộc 02 mẫu khảo sát thực địa tại VICHI MARKET và không thể xác minh thông tin lô hàng thực tế. [Nguồn: SRC-SIM-POLICY]"
                )
            else:
                answer = (
                    f"Đối với {p_name} (Hồ sơ thử nghiệm tại VICHI MARKET): hệ thống chỉ hiển thị thông tin quan sát được từ ảnh chụp nhãn tại điểm bán "
                    f"và thông tin công bố cấp thương hiệu. Câu hỏi này chưa có chứng từ cấp lô hàng (như mã lô, tờ khai hải quan hay giấy kiểm dịch) để đối chiếu; "
                    f"XuatXu không suy đoán ngoài phạm vi bằng chứng hiện có."
                )
            return jsonify({
                'success': True,
                'answer': answer,
                'product_id': effective_pid,
                'profile_type': selected_product.get('profile_type', ''),
                'source_nature': 'SIMULATION_ONLY' if is_sim else 'LIMITED_RETAIL_EVIDENCE',
                'source_ids': 'SRC-SIM-POLICY' if is_sim else 'Kho tri thức nguồn XuatXu',
                'matched': False
            })

    # 5. Câu hỏi chung về hệ thống / phương pháp luận (khi không hỏi riêng sản phẩm nào)
    if user_q:
        q_lower = user_q.lower()
        if any(k in q_lower for k in ['xuatxu', 'hệ thống', 'làm sao', 'cách dùng', 'chức năng', 'lợi ích']):
            answer = (
                "Hệ thống XuatXu hỗ trợ: (1) Tra cứu 02 hồ sơ thử nghiệm thực tế tại VICHI MARKET (Táo ENVY và Kiwi vàng Zespri) tách biệt rõ với 07 hồ sơ mô phỏng mở rộng; "
                "(2) Quét và tạo mã QR chuẩn HTTPS cho từng hồ sơ; (3) Trợ lý giải thích thông tin có nguồn (108 câu hỏi chuẩn hóa); "
                "(4) Mô phỏng kiểm tra tính toàn vẹn SHA-256 độc lập."
            )
        elif any(k in q_lower for k in ['3 không', 'nguyên tắc', 'tẩy xanh', 'greenwashing', 'minh bạch']):
            answer = (
                "Nguyên tắc minh bạch của XuatXu: (1) Không bịa đặt mã lô, tờ khai hải quan hay giấy kiểm dịch khi chưa có chứng từ gốc; "
                "(2) Không đánh đồng công bố cấp thương hiệu hoặc dòng sản phẩm khác với bằng chứng của từng lô tại điểm bán; "
                "(3) Không tự đưa cáo buộc tẩy xanh khi chỉ mới thiếu dữ liệu công khai."
            )
        elif any(k in q_lower for k in ['sha256', 'sha-256', 'hash', 'mã băm', 'mật mã', 'blockchain']):
            answer = (
                "Mô phỏng kiểm tra tính toàn vẹn SHA-256 trên XuatXu minh họa cơ chế phát hiện sửa đổi dữ liệu qua 05 sự kiện giả định: "
                "nếu một thông tin trong chuỗi bị chỉnh sửa, chữ ký băm sẽ báo lỗi (FAIL) ngay lập tức. Đây không phải giao dịch blockchain thực tế."
            )
        else:
            answer = (
                "Câu hỏi chưa khớp với dữ liệu đối chiếu trong kho tri thức. Vui lòng chọn một trong 108 câu hỏi gợi ý chuẩn hóa bên trên, "
                "hoặc nêu rõ tên sản phẩm (Táo ENVY, Kiwi Zespri, hay một trong 7 hồ sơ mô phỏng mở rộng) để hệ thống phản hồi đúng phạm vi bằng chứng."
            )
            
        return jsonify({
            'success': True,
            'answer': answer,
            'source_ids': 'Kho tri thức XuatXu',
            'source_nature': 'Trợ lý giải thích thông tin có nguồn',
            'matched': False
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

def _sanitize_feedback_text(text):
    """Ẩn thông tin định danh cá nhân (số điện thoại, email) trong nội dung phản hồi."""
    if not text:
        return ''
    cleaned = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[email ẩn]', str(text))
    cleaned = re.sub(r'(\+?\d[\d\s\-\.]{7,}\d)', '[SĐT ẩn]', cleaned)
    return cleaned

@app.route('/api/feedback', methods=['GET', 'POST'])
def api_feedback():
    """Tiếp nhận và lưu trữ phản hồi người dùng với cơ chế ẩn danh hóa PII công khai (W12 / Q20)."""
    if request.method == 'POST':
        req = request.json or {}
        product_id = html.escape(str(req.get('product_id', '')).strip()[:50])
        amount = html.escape(str(req.get('amount', 'Vừa đủ')).strip()[:50])
        raw_comment = _sanitize_feedback_text(str(req.get('comment', '')).strip()[:500])
        comment = html.escape(raw_comment)
        
        if not comment:
            return jsonify({'success': False, 'message': 'Vui lòng nhập nội dung góp ý'}), 400
            
        feedback_item = {
            'id': int(time.time() * 1000),
            'participant_label': 'Người dùng ẩn danh',
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
            'message': 'Cảm ơn bạn đã đóng góp phản hồi (thông tin cá nhân được tự động ẩn danh)!',
            'feedback': feedback_item
        })
    else:
        # GET công khai: chỉ trả về dữ liệu đã ẩn danh hóa hoàn toàn, không trả về tên/SĐT/email cá nhân
        feedbacks = []
        if os.path.exists(FEEDBACK_FILE):
            try:
                with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                    raw_list = json.load(f)
                    for item in raw_list:
                        feedbacks.append({
                            'id': item.get('id'),
                            'participant_label': 'Người dùng ẩn danh',
                            'product_id': item.get('product_id', ''),
                            'amount': item.get('amount', ''),
                            'comment': _sanitize_feedback_text(item.get('comment', '')),
                            'created_at': item.get('created_at', '')
                        })
            except Exception:
                feedbacks = []
        return jsonify({
            'success': True,
            'privacy_mode': 'ANONYMIZED_PUBLIC_VIEW',
            'total_count': len(feedbacks),
            'feedbacks': feedbacks
        })

if __name__ == '__main__':
    # Chạy local server
    app.run(host='0.0.0.0', port=5000, debug=False)
