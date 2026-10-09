---
name: ytbknot
description: "Trích xuất và chuyển đổi video YouTube thành tài liệu học tập kỹ thuật chuyên sâu bằng Tiếng Việt cho Antigravity (AGY). AI tự động phân tích kịch bản để chụp chính xác các khung hình kỹ thuật (code, terminal, sơ đồ), lưu bộ ảnh độc lập, bài note 2 tầng thuần Việt, không emoji, tiêu đề ngắn gọn."
user-invocable: true
argument-hint: "<youtube-url> [url2] [url3] [--interval <seconds>] [--clean-ads] [--screenshots [chapters|scenes|timestamps]] [--comments] [--transcript-only] [--no-save] | --check"
allowed-tools: "run_command, view_file, write_to_file, ask_question"
---

Phân tích URL YouTube từ người dùng: <user_request>$ARGUMENTS</user_request>

## Kiểm tra môi trường

```bash
python3 --version && yt-dlp --version && ffmpeg -version 2>&1 | head -1
```

---

## Trinh sát dữ liệu

1. Chạy lệnh trinh sát nhanh chỉ lấy metadata và kịch bản sạch, tự động lưu vào cache cục bộ:
   ```bash
   ytbknot "[URL]" --no-save --clean-ads
   ```
2. Đọc metadata và transcript từ kết quả trả về để xác định độ dài, số lượng chương và ngữ cảnh bài giảng.

---

## Trích xuất ảnh

Dựa trên kết quả trinh sát, AI tự động chọn 1 trong 3 nhánh thực thi:

1. **Nhánh có phân đoạn**: Nếu video có từ 3 chương trở lên với mốc thời gian cụ thể:
   ```bash
   ytbknot "[URL]" --screenshots chapters --force
   ```
2. **Nhánh kịch bản kỹ thuật**: Nếu video không có phân đoạn nhưng có phụ đề:
   - AI rà soát kịch bản tìm 5 đến 10 mốc thời gian xuất hiện thao tác terminal, soạn thảo code hoặc sơ đồ kiến trúc.
   - Loại bỏ hoàn toàn các phân đoạn tác giả chỉ nói chuyện (talking head).
   - Chạy lệnh trích xuất chính xác các mốc đã lọc (sử dụng lại cache, không tải lại YouTube):
   ```bash
   ytbknot "[URL]" --screenshots "<ts1>,<ts2>,<ts3>,..." --force
   ```
3. **Nhánh ngoại lệ**: Chỉ kích hoạt khi video không có phụ đề hoặc thời lượng vượt quá 2 giờ:
   - Gọi công cụ `ask_question` để người dùng chọn: tóm tắt lý thuyết, quét chuyển cảnh chuyên sâu (`--screenshots scenes`), hoặc nhập mốc thời gian thủ công.

---

## Định dạng ghi chú

- **100% Tiếng Việt Kỹ thuật**.
- **Tuyệt đối không emoji/icon trang trí**.
- **Tiêu đề H2, H3 cực kỳ ngắn gọn (2-4 từ, thuần Việt, không chèn tiếng Anh trong ngoặc đơn)**.
- **Tầng 1 (Tổng luận chuyên đề):** Đọc nhanh 5 phút nắm 100% tinh hoa, quy tắc và kiến trúc cốt lõi.
- **Tầng 2 (Bóc tách chi tiết):** Đi sâu từng phân đoạn, gắn kèm hình ảnh kỹ thuật tương ứng, phân tích bản chất và bài toán thực tế.
- Bố cục bắt buộc: Thuật ngữ -> Tổng luận chuyên đề -> Bóc tách chi tiết -> Trích dẫn then chốt -> Lệnh &amp; Công cụ -> Đánh đổi & Rủi ro.

---

## Báo cáo kết quả

Lưu file ghi chú vào `<OUTPUT_FOLDER>/<slug>.md` và thông báo cho người dùng đường dẫn thư mục bài học cùng số lượng ảnh đã trích xuất.
