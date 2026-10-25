# XUATXU – BIẾT NGUỒN, HIỂU BẰNG CHỨNG
### NỀN TẢNG TRA CỨU, ĐỐI CHIẾU NGUỒN THAM CHIẾU VÀ DIỄN GIẢI THÔNG TIN NÔNG SẢN NHẬP KHẨU

> **Bản hoàn thiện phục vụ Vòng Chung kết SV NCKH Thành phố Đà Nẵng 2026**  
> Phiên bản: `v1.1 (25/10/2026)`  
> Đơn vị thí điểm bối cảnh bán lẻ: **VICHI MARKET**  
> Nền tảng triển khai: **Python Flask / WSGI Gunicorn / Render (HTTPS)**

---

## 1. ĐỊNH VỊ VÀ NGUYÊN TẮC MINH BẠCH

XuatXu là nền tảng hỗ trợ người tiêu dùng Việt Nam tra cứu thông tin sản phẩm nông sản nhập khẩu, đối chiếu nguồn tham chiếu và hiểu rõ phạm vi bằng chứng tại điểm bán. Thông qua mã QR, hồ sơ thông tin tại điểm bán và công cụ giải thích, XuatXu giúp người mua phân biệt:
- **Thông tin ghi nhận tại điểm bán:** Ảnh bao bì, tem nhãn, giá bán lẻ ở thời điểm chụp.
- **Thông tin do thương hiệu công bố:** Giới thiệu xuất xứ, chương trình quản lý chất lượng chung từ website chính thức của thương hiệu.
- **Thông tin chưa thể xác minh theo lô:** Minh bạch khoảng trống dữ liệu khi chưa có mã lô hoặc chứng từ nhập khẩu gốc.

### Nguyên tắc "3 KHÔNG":
1. **Không tự tạo dữ liệu giả:** Không tự bịa số tờ khai hải quan, số giấy kiểm dịch thực vật hay mã lô khi chưa có tài liệu gốc.
2. **Không đánh đồng phạm vi:** Nguồn cấp thương hiệu hoặc chính sách của nhà trồng không tự động áp dụng thành chứng chỉ cấp lô của sản phẩm tại cửa hàng.
3. **Không gọi mô phỏng là on-chain:** Chuỗi băm SHA-256 phục vụ nghiên cứu được tách thành khu vực kỹ thuật độc lập; không gọi là giao dịch blockchain on-chain.

---

## 2. PHẠM VI DỮ LIỆU CUỐI CÙNG

Hệ thống quản lý chuẩn hóa **02 hồ sơ sản phẩm thực tế** ghi nhận tại VICHI MARKET:
1. **`P-ENVY-VICHI-01`**: Táo ENVY đóng túi 1 kg – ghi nhận tại VICHI.
   - Ảnh thực tế: `/static/images/vichi_envy_bag.jpg`
   - Nhãn ghi nhận: T&G / TONY FRUIT, giá bán lẻ thời điểm chụp 185.000 đ/túi.
   - Nguồn tham chiếu: Câu chuyện ENVY (`SRC-ENVY-01`), Nuôi trồng ENVY (`SRC-ENVY-02`).
   - Phạm vi xác minh: Chưa có mã lô, tờ khai hải quan hay chứng nhận môi trường riêng theo lô cho túi táo tại VICHI.
2. **`P-ZESPRI-VICHI-01`**: Kiwi vàng Zespri New Zealand hộp 4 quả – ghi nhận tại VICHI.
   - Ảnh thực tế: `/static/images/vichi_zespri_gold_4.jpg`
   - Nhãn ghi nhận: New Zealand, giá 170.000 đ/hộp, mã bán lẻ nội bộ `SP12345950`.
   - Nguồn tham chiếu: Zespri Product Line (`SRC-ZESPRI-01`), Zespri System Assurance (`SRC-ZESPRI-02`).
   - Phạm vi xác minh: Mã `SP12345950` là mã siêu thị, không phải mã lô. Không gán Organic của hộp 3 quả (`vichi_zespri_organic_3_REFERENCE.jpg`) cho hộp kiwi vàng 4 quả.

---

## 3. CẤU TRÚC THƯ MỤC NGUỒN

```
xuatxu-web-main/
├── app.py                      # Flask Backend: API init, product-detail, QR HTTPS, AI Ask, Tech Demo, Feedback
├── requirements.txt            # Flask, qrcode[pil], Pillow, gunicorn
├── render.yaml                 # Cấu hình triển khai tự động lên Render
├── data/                       # Bộ 22 tệp CSV chuẩn hóa v1.1
│   ├── SAN_PHAM.csv            # 02 hồ sơ sản phẩm
│   ├── LO_HANG.csv             # 02 bản ghi meta nội bộ (lot_code rỗng, không tự tạo mã lô)
│   ├── PUBLIC_DISPLAY_CARDS.csv# 08 thẻ hiển thị tuyển chọn (3 thông tin + 1 giới hạn/sản phẩm)
│   ├── BANG_CHUNG.csv          # 14 bản ghi bằng chứng chi tiết
│   ├── CLAIM_EVIDENCE.csv      # 06 tình huống đối chiếu tuyên bố - bằng chứng
│   ├── NGUON_THAM_KHAO.csv     # 12 nguồn tham chiếu chính thức
│   ├── AI_HOI_DAP.csv          # 19 cặp hỏi đáp chuẩn hóa có nguồn
│   ├── AI_KIEN_THUC.csv        # Cơ sở kiến thức cho trợ lý
│   ├── DEMO_EVENTS.csv         # 05 sự kiện giả định cho mô phỏng SHA-256
│   ├── DEMO_HASH_CHAIN.csv     # Chuỗi băm SHA-256 liên kết phục vụ kiểm tra toàn vẹn
│   ├── KIEM_THU.csv            # Ma trận 16 kịch bản kiểm thử (T01 - T16: Đã PASS)
│   └── user_feedback.json      # Lưu trữ bền vững phản hồi người dùng thực tế
├── static/
│   ├── style.css               # Giao diện responsive 360px - desktop, thiết kế phân lớp
│   └── images/                 # Ảnh thực tế tại VICHI
│       ├── vichi_envy_bag.jpg
│       ├── vichi_zespri_gold_4.jpg
│       └── vichi_zespri_organic_3_REFERENCE.jpg
└── templates/
    └── index.html              # Frontend hoàn chỉnh: 6 Tab chức năng (Home, QR, Detail, AI, Tech, About)
```

---

## 4. HƯỚNG DẪN CHẠY LOCAL VÀ TRIỂN KHAI RENDER

### 4.1. Chạy trên máy tính cá nhân (Local Development)
```bash
# 1. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 2. Khởi chạy ứng dụng Flask
python app.py
```
Ứng dụng sẽ chạy tại: `http://localhost:5000` hoặc `http://127.0.0.1:5000`.

### 4.2. Triển khai lên Render (Production Cloud)
- **Runtime:** Python 3.14+ (hoặc Python 3.11/3.12)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Environment Variables:**
  - `PUBLIC_BASE_URL`: `https://xuatxu-web.onrender.com`
- Hệ thống tự động kích hoạt HTTPS và sinh mã QR HTTPS an toàn trỏ trực tiếp đến `#detail/P-ENVY-VICHI-01` và `#detail/P-ZESPRI-VICHI-01`.

---

## 5. HỆ THỐNG API CHUẨN HÓA

| Endpoint | Phương thức | Mô tả chức năng |
| :--- | :---: | :--- |
| `GET /api/init` | GET | Trả về 02 hồ sơ sản phẩm sạch, định vị XuatXu và danh sách hỏi đáp |
| `GET /api/product-detail/<pid>` | GET | Trả về 03 thẻ thông tin có nguồn, 01 hộp giới hạn xác minh, bằng chứng và URL QR HTTPS |
| `GET /api/generate-qr` | GET | Sinh ảnh PNG mã QR cho hồ sơ sản phẩm (tham số `product_id`) |
| `POST /api/ai-ask` | POST | Trợ lý giải thích: Trả lời câu hỏi dựa trên 19 nội dung có nguồn `[SRC-...]` |
| `GET /api/tech-demo` | GET | Trả về 05 sự kiện giả định và chuỗi hash SHA-256 (gắn nhãn mô phỏng rõ ràng) |
| `POST /api/tech-demo/verify` | POST | Kiểm tra tính toàn vẹn chuỗi SHA-256, hỗ trợ test can thiệp dữ liệu |
| `POST /api/feedback` | POST | Tiếp nhận phản hồi đánh giá thực tế của người dùng và lưu trữ bền vững |

---

## 6. KẾT QUẢ KIỂM THỬ 16 KỊCH BẢN (KIEM_THU.csv)

Tất cả 16 kịch bản kiểm thử đã được chạy tự động và nghiệm thu đạt chuẩn (**PASS** ngày 25/10/2026):

| Mã | Kịch bản | Kết quả mong đợi | Trạng thái thực tế |
| :---: | :--- | :--- | :---: |
| **T01** | Mở hồ sơ ENVY bằng HTTPS | Hiển thị túi ENVY tại VICHI, không tạo số lô giả | **PASS** |
| **T02** | Mở hồ sơ Zespri qua QR HTTPS | Đúng hộp 4 quả, không gộp Organic | **PASS** |
| **T03** | Ảnh sản phẩm từ static/images | Tải được ảnh VICHI thật, có chú thích | **PASS** |
| **T04** | Hiển thị nguồn ENVY | T&G/ENVY có URL công khai; không gán xuất xứ Mỹ cho lô | **PASS** |
| **T05** | Hiển thị nguồn Zespri | Có link Zespri System Assurance, không gán chứng chỉ cấp lô | **PASS** |
| **T06** | Trạng thái chứng từ trống | Không tự điền số tờ khai hoặc kiểm dịch | **PASS** |
| **T07** | Phân biệt SKU kiwi Organic và thường | Không gắn nhãn Organic cho hộp 4 quả | **PASS** |
| **T08** | Phân biệt mã SP bán lẻ với mã lô | SP12345950 hiển thị là mã bán lẻ, không phải mã lô | **PASS** |
| **T09** | Thông tin táo bán rời không gán vào túi | Giá 205.000 đ/kg chỉ ở biến thể bán rời | **PASS** |
| **T10** | Dữ liệu tình huống mô phỏng | Hành trình demo hiển thị tab riêng, không dưới hồ sơ thật | **PASS** |
| **T11** | Giải thích kiểm dịch | Nêu chưa có bằng chứng theo lô, không kết luận có | **PASS** |
| **T12** | Giải thích xuất xứ ENVY | Không khẳng định Mỹ cho túi ENVY tại VICHI khi thiếu bằng chứng | **PASS** |
| **T13** | Không có phản hồi khách giả | Đã loại bỏ bình luận WinMart giả và lượt quét demo | **PASS** |
| **T14** | Bảo mật và cấu hình Render | Debug mode tắt; HTTPS QR sinh hợp lệ, không lỗi | **PASS** |
| **T15** | Hồ sơ kỹ thuật trống không crash | Dữ liệu hành trình rỗng vẫn mở bình thường | **PASS** |
| **T16** | Hiển thị giới hạn xác minh | Hộp giới hạn xác minh hiển thị đầy đủ trên cả 2 hồ sơ | **PASS** |

---

## 7. QUY TRÌNH VẬN HÀNH & BẢO TRÌ DỮ LIỆU

Khi có sản phẩm hoặc tài liệu mới, thực hiện quy trình 7 bước:
1. **Tiếp nhận thông tin:** Chụp ảnh bao bì, tem nhãn tại điểm bán (độ phân giải rõ, đọc được thông tin).
2. **Kiểm tra nguồn thương hiệu:** Tìm website chính thức của nhà trồng / đơn vị phân phối, lưu đường dẫn và thời điểm kiểm tra.
3. **Phân loại phạm vi:** Điền vào `PUBLIC_DISPLAY_CARDS.csv` và `BANG_CHUNG.csv` với các giá trị `scope`: `RETAIL_OBSERVATION`, `BRAND_ONLY`, `LIMITATION`.
4. **Kiểm tra ranh giới xác minh:** Nếu không có chứng từ hải quan/kiểm dịch kèm mã lô, giữ `verified_for_lot = False` và soạn nội dung hộp *Phạm vi xác minh*.
5. **Cập nhật hỏi đáp trợ lý:** Thêm các câu hỏi liên quan vào `AI_HOI_DAP.csv` kèm mã nguồn trích dẫn.
6. **Kiểm thử tự động:** Chạy script kiểm thử để đảm bảo không vi phạm quy tắc dữ liệu.
7. **Triển khai phiên bản:** Cập nhật lên Git / Render, kiểm tra camera điện thoại quét QR trên thiết bị thật.
