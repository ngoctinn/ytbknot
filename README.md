# ytbknot

Plugin trích xuất và chuyển đổi video YouTube thành tài liệu học tập kỹ thuật chuyên sâu bằng Tiếng Việt cho Antigravity (AGY).

---

## 1. Giới thiệu

`ytbknot` là bộ công cụ học tập dành cho kỹ sư và người học chuyên sâu:
* **Tự động hóa toàn diện:** Lấy phụ đề (transcript), lọc phân đoạn tài trợ/quảng cáo qua SponsorBlock, chụp khung hình kỹ thuật và tổ chức bài học thành tài liệu Markdown.
* **Bộ ảnh độc lập:** Toàn bộ ảnh trích xuất từ video được lưu tách biệt tại thư mục `screenshots/` (hỗ trợ chụp dày theo chu kỳ `--interval`).
* **Bài note 2 tầng chuẩn mực:**
  * **Tầng 1 (Tổng luận chuyên đề):** Đọc nhanh 5 phút để nắm trọn 100% tinh hoa, công thức và quy tắc vàng.
  * **Tầng 2 (Bóc tách chi tiết):** Phân tích từng câu hỏi hoặc từng mốc demo: đề bài, dịch nghĩa, phân tích từng phương án A-B-C-D, họ từ mở rộng và khung hình tương ứng.
* **Tiêu chuẩn trình bày:** 100% Tiếng Việt Kỹ thuật, không dùng bất kỳ emoji trang trí nào, tiêu đề ngắn gọn thuần Việt (2-4 từ, không ngoặc đơn tiếng Anh).
* **AI-Curated Visuals:** AI tự động đọc kịch bản để tìm đúng khoảnh khắc có thao tác kỹ thuật thật (terminal, code, sơ đồ), cấm chụp ảnh chân dung người nói (talking head).

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
│   └── yt-extract.py
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

### Các tùy chọn nâng cao:

* **Chụp ảnh dày theo chu kỳ (khuyên dùng cho video bài giảng slide):**
  ```text
  /ytbknot https://www.youtube.com/watch?v=... --interval 60
  ```
  *(Cứ mỗi 60 giây tự động chụp 1 ảnh chất lượng cao lưu vào `screenshots/`).*

* **Lọc bỏ quảng cáo & phân đoạn tài trợ (SponsorBlock):**
  ```text
  /ytbknot https://www.youtube.com/watch?v=... --clean-ads
  ```

* **Lấy thêm bình luận thảo luận từ cộng đồng:**
  ```text
  /ytbknot https://www.youtube.com/watch?v=... --comments
  ```

* **Sử dụng trực tiếp qua Terminal CLI:**
  ```bash
  ytbknot "https://www.youtube.com/watch?v=JIVXPafQFKk" --output-base "." --interval 120 --clean-ads
  ```

---

## 4. Cấu trúc kết quả đầu ra

Mỗi video được lưu trong một thư mục bài học riêng biệt:

```text
yt-extract_YYYY-MM-DD_slug-video/
├── screenshots/                     # Kho ảnh chụp màn hình độc lập
│   ├── 001_07m34s.png
│   ├── 002_15m09s.png
│   └── ...
├── thumbnail.jpg                    # Ảnh bìa HD
└── yt-extract_YYYY-MM-DD_slug.md    # Bài note 2 tầng chuẩn kỹ thuật
```
