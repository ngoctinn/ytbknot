# ytbknot

Plugin trích xuất và chuyển đổi video YouTube thành tài liệu học tập kỹ thuật chuyên sâu bằng Tiếng Việt cho Antigravity (AGY).

---

## 1. Giới thiệu

`ytbknot` là bộ công cụ học tập dành cho kỹ sư và người học chuyên sâu:
* **Quy trình thích ứng 2 pha:** Trinh sát nhanh metadata và transcript trong 2-3 giây, sau đó tự động phân loại video để trích xuất khung hình chuẩn xác mà không cần người dùng cấu hình phức tạp.
* **Tự động hóa toàn diện:** Lấy phụ đề, lọc phân đoạn tài trợ và quảng cáo qua SponsorBlock, chụp khung hình kỹ thuật và tổ chức bài học thành tài liệu Markdown.
* **Bộ ảnh độc lập:** Toàn bộ ảnh trích xuất từ video được lưu tách biệt tại thư mục `screenshots/` (hỗ trợ phân đoạn, chu kỳ `--interval`, phát hiện chuyển cảnh `scenes` hoặc mốc chỉ định).
* **Bài note 2 tầng chuẩn mực:**
  * **Tầng 1 (Tổng luận chuyên đề):** Đọc nhanh 5 phút để nắm trọn 100% tinh hoa, công thức và quy tắc cốt lõi.
  * **Tầng 2 (Bóc tách chi tiết):** Phân tích từng phân đoạn demo hoặc câu hỏi, đối chiếu đề bài, phương án, họ từ mở rộng và khung hình tương ứng.
* **Tiêu chuẩn trình bày:** 100% Tiếng Việt Kỹ thuật, không dùng bất kỳ emoji trang trí nào, tiêu đề ngắn gọn thuần Việt (2-4 từ, không ngoặc đơn tiếng Anh).
* **Lọc ảnh kỹ thuật:** AI tự động đọc kịch bản để tìm đúng khoảnh khắc có thao tác kỹ thuật thật (terminal, code trong IDE, sơ đồ kiến trúc), loại bỏ hoàn toàn ảnh chân dung người nói (talking head).

---

## 2. Cài đặt & Yêu cầu hệ thống

### Công cụ phụ thuộc:
* **Python 3.10+**
* **yt-dlp**
* **ffmpeg**
* **Node.js** (để yt-dlp giải mã JavaScript runtime của YouTube)

```bash
# Kiểm tra môi trường
python3 --version
yt-dlp --version
ffmpeg -version
node --version
```

### Vị trí plugin trong Antigravity:
```text
~/.gemini/config/plugins/ytbknot/
├── plugin.json
├── README.md
├── rules/
│   └── AGENTS.md
├── scripts/
│   └── ytbknot.py
└── skills/
    └── ytbknot/
        ├── SKILL.md
        └── references/
            └── learning-template.md
```

Lệnh thực thi CLI được gắn sẵn vào PATH: `ytbknot` (tại `~/.local/bin/ytbknot`).

---

## 3. Hướng dẫn sử dụng

### Sử dụng qua Slash Command trong Antigravity:
```text
/ytbknot https://www.youtube.com/watch?v=...
```

Khi được gọi, kỹ năng sẽ tự động thực thi theo quy trình 2 pha:
1. **Pha 1 (Trinh sát):** Tải nhanh metadata và transcript sạch (lưu cache, không chụp ảnh).
2. **Pha 2 (Trích xuất hành động thực tế):**
   * AI phân tích kịch bản để tìm mốc thời gian thao tác kỹ thuật cụ thể (terminal, code IDE, sơ đồ kiến trúc), tuyệt đối không chụp tại mốc đầu chương (tránh ảnh chân dung hoặc slide bìa).
   * Nếu có chương: AI chọn 1-2 mốc hành động then chốt nằm sâu trong thân từng chương.
   * Nếu không có chương: AI chọn 5-10 mốc thời gian kỹ thuật quan trọng nhất dọc bài giảng.
   * Nếu ngoại lệ (không có phụ đề hoặc thời lượng > 2 giờ): Mở hộp thoại hỏi ý định người dùng.

### Các tùy chọn qua Terminal CLI:

* **Trinh sát nhanh (chỉ lấy kịch bản và cache, không tạo thư mục):**
  ```bash
  ytbknot "https://www.youtube.com/watch?v=..." --no-save --clean-ads
  ```

* **Trích xuất theo các mốc thời gian chỉ định (tua nhanh trực tiếp, không nghẽn mạng):**
  ```bash
  ytbknot "https://www.youtube.com/watch?v=..." --screenshots "1:15,4:30,9:45" --force
  ```

* **Chụp ảnh theo chu kỳ thời gian:**
  ```bash
  ytbknot "https://www.youtube.com/watch?v=..." --interval 60 --clean-ads
  ```

* **Lấy thêm bình luận thảo luận từ cộng đồng:**
  ```bash
  ytbknot "https://www.youtube.com/watch?v=..." --comments
  ```

---

## 4. Cấu trúc kết quả đầu ra

Mỗi video được lưu trong một thư mục bài học riêng biệt:

```text
ytbknot_YYYY-MM-DD_slug-video/
├── screenshots/                     # Kho ảnh chụp màn hình độc lập
│   ├── 001_07m34s.png
│   ├── 002_15m09s.png
│   └── ...
├── thumbnail.jpg                    # Ảnh bìa HD
└── ytbknot_YYYY-MM-DD_slug.md       # Bài note 2 tầng chuẩn kỹ thuật
```
