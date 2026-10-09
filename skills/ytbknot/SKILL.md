---
name: ytbknot
description: "Trích xuất và chuyển đổi video YouTube thành tài liệu học tập kỹ thuật chuyên sâu bằng Tiếng Việt cho Antigravity (AGY). AI tự động phân tích kịch bản để chụp chính xác các khung hình kỹ thuật (code, terminal, sơ đồ), lưu bộ ảnh độc lập, bài note 2 tầng thuần Việt, không emoji, tiêu đề ngắn gọn."
user-invocable: true
argument-hint: "<youtube-url> [url2] [url3] [--interval <seconds>] [--clean-ads] [--screenshots [chapters|scenes|timestamps]] [--comments] [--transcript-only] [--no-save] | --check"
allowed-tools: "run_command, view_file, write_to_file, ask_question"
---

Phân tích URL YouTube từ người dùng: <user_request>$ARGUMENTS</user_request>

## Bước 0 — Kiểm tra môi trường phụ thuộc

```bash
python3 --version && yt-dlp --version && ffmpeg -version 2>&1 | head -1
```

---

## Bước 1 — Lấy Metadata & Kịch bản Transcript

1. Chạy trích xuất metadata và transcript sạch:
   ```bash
   ytbknot "[URL]" --output-base "." [--clean-ads] [--interval 60] [--force]
   ```
2. Đọc transcript để hiểu sâu toàn bộ luồng bài giảng.

---

## Bước 2 — Trích Xuất Bộ Ảnh Độc Lập & Lọc Khung Hình Thông Minh

> **QUY TẮC BỘ ẢNH:**
> 1. Bộ ảnh được lưu độc lập tại `<OUTPUT_FOLDER>/screenshots/`.
> 2. Có thể dùng `--interval <giây>` (ví dụ: `--interval 60` hoặc `120`) để tự động chia nhỏ thời gian chụp dày đặc.
> 3. AI đọc kịch bản để chọn đúng giây tác giả thực sự thao tác màn hình, cấm nhồi ảnh chân dung (talking head).

---

## Bước 3 — Định dạng bài note chuẩn 2 tầng (Thuần Việt, Không Emoji)

- **100% Tiếng Việt Kỹ thuật**.
- **Tuyệt đối không emoji/icon trang trí**.
- **Tiêu đề H2, H3 cực kỳ ngắn gọn (2-4 từ, không ngoặc đơn tiếng Anh)**.
- **Tầng 1 (Tổng luận chuyên đề):** Đọc nhanh 5 phút nắm 100% tinh hoa và công thức.
- **Tầng 2 (Bóc tách chi tiết từng câu / khung hình):** Đi sâu từng trường hợp, phân tích đầy đủ các phương án A-B-C-D và họ từ mở rộng.

---

## Bước 4 — Báo cáo kết quả

Lưu file ghi chú vào `<OUTPUT_FOLDER>/<slug>.md` và thông báo cho người dùng đường dẫn thư mục bài học và số lượng ảnh đã trích xuất.
