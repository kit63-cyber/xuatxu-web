# XUATXU – GÓI CẬP NHẬT DỮ LIỆU VÀ WEBSITE CUỐI CÙNG (30/10/2026)

## 1. Phạm vi phát hành
**Chính xác 9 hồ sơ, không có nông sản nội địa.**
- `P-ENVY-VICHI-01`, `P-ZESPRI-VICHI-01`: ảnh chụp ở VICHI và thông tin công khai cấp thương hiệu. **KHÔNG** có chứng từ/mã lô đã đối chiếu.
- 7 hồ sơ còn lại: **mô phỏng hoàn toàn để trình diễn danh mục**, không có hàng thực/điểm bán VICHI, không có giấy tờ nhập khẩu thật. Tên sản phẩm, nước xuất xứ, quy cách, giá, chủ thể, hành trình đều là giả định.
- Mô phỏng SHA-256 là mô phỏng tính toàn vẹn, **không phải blockchain on-chain**.

## 2. Cách triển khai để tránh lỗi phiên bản
**Khuyến nghị:** dùng cả thư mục `xuatxu-web-main` trong ZIP này làm bản mã nguồn duy nhất trên GitHub/Render. Đã đồng bộ `app.py`, `templates/index.html`, `static/style.css`, dữ liệu và ảnh VICHI. Không chép chỉ CSV lên giao diện cũ vì code cũ có giá/xuất xứ/sản phẩm nội địa gắn cứng.

Các bước:
1. Sao lưu Git repository và biến môi trường hiện tại. Xóa bản sao dự án lồng nhau trước khi deploy.
2. Đồng bộ **toàn bộ** các thư mục `data/`, `templates/`, `static/` và file `app.py`; giữ `requirements.txt`, `render.yaml` tương ứng.
3. Đặt `PUBLIC_BASE_URL=https://xuatxu-web.onrender.com` hoặc domain thật nhóm sở hữu. Không dùng domain giả định nếu chưa cấu hình.
4. Deploy lên Render và kiểm tra trang chủ có 9 sản phẩm, chỉ 2 nhãn `Ghi nhận tại VICHI` và 7 nhãn `Mô phỏng mở rộng`.
5. Trên điện thoại quét lại QR đã IN để chắc chắn mở đúng `#detail/P-ENVY-VICHI-01` / `#detail/P-ZESPRI-VICHI-01`.
6. Mở từng trang 7 sản phẩm phụ, kiểm tra 12 FAQ/sản phẩm, bảng nguồn/bằng chứng, 5 sự kiện giả định. Chạy thử mô phỏng SHA-256 sửa dữ liệu → fail.
7. Kiểm tra ảnh web trên trình duyệt có internet; nếu ảnh không tải, hệ thống dùng ảnh fallback SVG (không phải ảnh giả chụp tại VICHI). Muốn website hoàn toàn offline phải tải ảnh theo giấy phép và chuyển sang `/static/images/`.
8. Chạy toàn bộ checklist `QA_FINAL_RELEASE.csv` và ghi PASS/FAIL thực tế kèm ảnh/video log. **Không** coi các trạng thái PASS trong file bản cũ là kiểm thử phiên bản này.

## 3. Thành phần dữ liệu
- `SAN_PHAM.csv`: 9 hồ sơ + `profile_type`, `price_display`, trạng thái ảnh/giá/xuất xứ.
- `PUBLIC_DISPLAY_CARDS.csv`, `NGUON_THAM_KHAO.csv`, `BANG_CHUNG.csv`, `CLAIM_EVIDENCE.csv`, `PRODUCT_SOURCE_LINKS.csv`: nguồn và phạm vi.
- `AI_HOI_DAP.csv` và `AI_KIEN_THUC.csv`: câu hỏi–trả lời có phân biệt loại hồ sơ.
- `MO_PHONG_HANH_TRINH.csv`: 7 × 5 sự kiện giả định. Không đưa vào `HANH_TRINH.csv` của hai sản phẩm thực.
- `MO_PHONG_DANH_MUC_CHUNG_TU.csv`: loại giấy tờ sẽ cần trong triển khai thật, không tạo số giả.
- `DEMO_EVENTS.csv`, `DEMO_HASH_CHAIN.csv`: demo công nghệ độc lập.
- `IMAGE_LICENSE_REGISTER.csv` và `/static/image_credits.html`: nguồn và ghi công ảnh trên mạng.
- `VICHI_EVIDENCE_PHOTOS/`: ảnh gốc nhóm đã cung cấp.

## 4. Giới hạn cần công khai trước BGK
- Không tự nhận đã có truy xuất theo lô hoặc xác thực blockchain thực tế.
- 7 hồ sơ giả định chỉ phục vụ trình diễn; không được mô tả là 7 sản phẩm đã thử nghiệm tại VICHI.
- Không dùng giá mô phỏng như giá bán hàng, không dùng ảnh web như bằng chứng xuất xứ hoặc chứng nhận.
- Kết quả khảo sát thí điểm VICHI phải sử dụng dữ liệu báo cáo đã thu thập, không tự tạo feedback hay số lượt quét.

## 5. Chốt nghiệm thu
**Bản này là gói dữ liệu+mã nguồn nhất quán, đã được kiểm tra tĩnh.** Chưa phải chứng nhận website trên Render đã triển khai, chạy đúng trên mọi thiết bị hoặc ảnh web đã tải thành công ngoài đời. Sinh viên phải làm nghiệm thu sau deploy.
