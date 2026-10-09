---
name: ytbknot
description: "Trích xuất và chuyển đổi video YouTube thành tài liệu học tập kỹ thuật chuyên sâu bằng Tiếng Việt cho Antigravity (AGY). AI tự động phân tích kịch bản để chụp chính xác các khung hình kỹ thuật (code, terminal, sơ đồ), lưu bộ ảnh độc lập, bài note 2 tầng thuần Việt, không emoji, tiêu đề ngắn gọn."
user-invocable: true
argument-hint: "<youtube-url> [url2] [url3] [--interval <seconds>] [--clean-ads] [--screenshots [chapters|timestamps]] [--comments] [--transcript-only] [--no-save] | --check"
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
2. Đọc metadata, danh sách chương và các khối kịch bản (`Semantic Chunks`) từ kết quả trả về.

---

## Phân khối bài giảng

Để bảo toàn 100% độ bao phủ và chiều sâu bài học, tránh hiện tượng trôi ngữ cảnh (Context Drift) với video dài:
- **Video dưới 45 phút**: Xử lý liền mạch toàn bộ bài giảng trong một chu trình.
- **Video trên 45 phút hoặc nhiều câu hỏi**:
  - Dựa vào danh sách `Semantic Chunks` (15-20 phút mỗi khối) hoặc cấu trúc câu hỏi (ví dụ `Question 101`, `Part 5`...).
  - Xử lý bóc tách chi tiết (Tầng 2) lần lượt theo từng khối, ghi nhận đầy đủ đề bài, giải thích phương án và kiến thức mở rộng.

---

## Trích xuất ảnh

**Quy tắc chọn khung hình theo ngữ cảnh:**
- **Không chụp đầu chương**: Giây bắt đầu chương hầu hết là slide tiêu đề hoặc người nói chuyện, không chứa nội dung kỹ thuật. Phân đoạn chương chỉ dùng để chia mục lục bài viết.
- **Bài giảng thao tác màn hình (Live-coding / Terminal)**: Bắt khung hình ngay khi thao tác lệnh hoặc đoạn mã được thực thi hoàn tất.
- **Bài giảng giải đề, slide trình chiếu hoặc bảng viết (Slide-based / Whiteboard / Problem-solving)**:
  * **Bắt buộc chụp tại mốc cuối phân đoạn** của từng câu/mục (ngay trước khi giảng viên chuyển sang nội dung kế tiếp từ 2 đến 5 giây).
  * Đây là thời điểm màn hình hiển thị trọn vẹn 100% nội dung ghi chú viết tay, lời giải chi tiết, phân tích đáp án và các từ vựng mở rộng mà giảng viên đã tổng hợp (tránh chụp đầu phân đoạn khi slide còn trắng trơn).
- **Tua nhanh trực tiếp**: Luôn sử dụng danh sách mốc thời gian cụ thể để ffmpeg nhảy cóc tức thời qua HTTP Range (1-2 giây mỗi ảnh), loại bỏ hoàn toàn nguy cơ bị YouTube bóp băng thông.

**Quy trình thực thi:**
1. **Trích xuất theo kịch bản (Bắt buộc)**:
   - Trong từng khối kịch bản, AI xác định chính xác các mốc giây tối ưu theo ngữ cảnh (cuối lời giải cho bài giảng slide/giải đề; sau khi chạy lệnh cho live-coding).
   - Loại bỏ hoàn toàn các phân đoạn nói chuyện phiếm (talking head).
   - Chạy lệnh trích xuất chính xác các mốc đã lọc (sử dụng lại cache, không tải lại YouTube):
   ```bash
   ytbknot "[URL]" --screenshots "<ts1>,<ts2>,<ts3>,..." --force
   ```
2. **Nhánh ngoại lệ**: Khi video không có bất kỳ phụ đề nào, gọi công cụ `ask_question` để người dùng cung cấp tài liệu hoặc nhập mốc thời gian thủ công.

---

## Định dạng ghi chú

- **100% Tiếng Việt Kỹ thuật**.
- **Tuyệt đối không emoji/icon trang trí**.
- **Tiêu đề H2, H3 cực kỳ ngắn gọn (2-4 từ, thuần Việt, không chèn tiếng Anh trong ngoặc đơn)**.
- **Tầng 1 (Tổng luận chuyên đề):** Đọc nhanh 5 phút nắm 100% tinh hoa, quy tắc và kiến trúc cốt lõi.
- **Tầng 2 (Bóc tách chi tiết):** Đi sâu từng khối / từng câu hỏi, gắn kèm hình ảnh kỹ thuật tương ứng, phân tích bản chất và bài toán thực tế.
- Bố cục bắt buộc: Thuật ngữ -> Tổng luận chuyên đề -> Bóc tách chi tiết -> Trích dẫn then chốt -> Lệnh &amp; Công cụ -> Đánh đổi & Rủi ro.

---

## Báo cáo kết quả

Lưu file ghi chú vào `<OUTPUT_FOLDER>/<slug>.md` và thông báo cho người dùng đường dẫn thư mục bài học cùng số lượng ảnh đã trích xuất.
