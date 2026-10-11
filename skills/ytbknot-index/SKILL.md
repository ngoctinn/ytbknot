---
name: ytbknot-index
description: "Lập chỉ mục toàn bộ Playlist hoặc Kênh YouTube thành lộ trình học tập định dạng Todo List, tự động dựng cây thư mục bài giảng (Scaffolding) và đồng bộ tiến độ học tập theo thời gian thực."
user-invocable: true
argument-hint: "<playlist-or-channel-url> [--category <name>] [--limit <number>] [--no-scaffold] [--output-base <path>]"
allowed-tools: "run_command, view_file, write_to_file, ask_question"
---

Phân tích yêu cầu lập chỉ mục Playlist / Kênh YouTube từ người dùng: <user_request>$ARGUMENTS</user_request>

## 1. Kiểm tra môi trường & Tham số

Xác định URL và các tùy chọn:
- **URL**: Link playlist (`...playlist?list=...`) hoặc kênh (`.../@channel/videos` hoặc `.../@channel`).
- **`--category <tên>`**: Danh mục môn học (nếu có).
- **`--limit <số>`**: Giới hạn số lượng video (ví dụ `--limit 20`).
- **`--no-scaffold`**: Chỉ tạo `00_INDEX.md` mà không tạo thư mục con cho từng bài.

---

## 2. Thực thi Lập Chỉ Mục & Dựng Khung Học Tập

Chạy lệnh lập chỉ mục siêu tốc bằng `ytbknot`:

```bash
ytbknot "[URL]" --index $([ -n "$CATEGORY" ] && echo "--category $CATEGORY") $([ -n "$LIMIT" ] && echo "--limit $LIMIT")
```

Lệnh sẽ:
1. Quét toàn bộ danh sách video (tên, thời lượng, ID) chỉ trong 2-4 giây qua chế độ flat-playlist.
2. Tự động tính toán tổng số bài và tổng thời lượng học tập.
3. Tạo Master Dashboard `00_INDEX.md` với thanh tiến độ `[░░░░░░░░░░░░░░░░░░░░] 0/N (0.0%)` và checklist `- [ ]`.
4. Scaffold sẵn cây thư mục con cho từng bài giảng (`01_slug/`, `02_slug/`...) kèm file `README.md` hướng dẫn lệnh chạy ngay.

---

## 3. Báo Cáo Lộ Trình & Hướng Dẫn Bắt Đầu

1. Đọc file `00_INDEX.md` tại đường dẫn `INDEX_FOLDER` được trả về.
2. Báo cáo kết quả rõ ràng, chuyên nghiệp:
   - **Tên khóa học / Kênh**: Tiêu đề chính.
   - **Tổng quy mô**: Số lượng video & tổng thời gian cần để hoàn thành toàn bộ khóa.
   - **Đường dẫn thư mục**: Vị trí lưu trữ lộ trình học tập.
   - **Thanh tiến độ**: Hiển thị thanh tiến độ trực quan.
3. **Chủ động đề xuất bắt đầu bài học kế tiếp (Bài `01`)**:
   - Tác tử không bắt người dùng tự gõ terminal. Tác tử nêu rõ bài 01 và hỏi người dùng có muốn bắt đầu xử lý ngay bài 01 hay không, hoặc tự động bắt đầu nếu người dùng đã yêu cầu từ đầu.
   - Cung cấp sẵn lệnh CLI tham khảo phụ trợ nếu người dùng muốn lưu trữ ngoài.

---

## 4. Kiểm Tra & Đồng Bộ Tiến Độ (Khi Người Dùng Hỏi Thăm)

Khi người dùng hỏi về tiến độ (ví dụ *"Hôm nay học bài nào?"*, *"Tiến độ khóa học Networks ra sao?"*):
1. Đọc file `00_INDEX.md` trong thư mục khóa học.
2. Tìm bài học kế tiếp còn mang dấu `- [ ]` đầu tiên.
3. Báo cáo phần trăm đã hoàn thành và cung cấp link / lệnh bắt đầu bài tiếp theo.
