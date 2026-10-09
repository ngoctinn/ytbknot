# Hướng Dẫn Định Danh Người Nói (Speaker Diarization Guide)

Áp dụng khi người dùng truyền cờ `--speakers` hoặc khi video là dạng phỏng vấn (interview), podcast, tọa đàm (panel discussion) có từ 2 người nói trở lên.

## Nguyên Tắc Nhận Diện
1. **Phân tích Metadata:** Dựa vào tiêu đề, phần mô tả (description) và thông tin kênh để xác định danh tính của Host (người dẫn) và Guest (khách mời).
2. **Phân tích Ngữ cảnh:** Tìm các đoạn giới thiệu ("Chào mừng bạn đến với...", "Hôm nay chúng ta có khách mời là..."), cách các nhân vật xưng hô với nhau để gắn nhãn đúng tên người nói.
3. **Fallback Nhãn Thống Nhất:** Nếu không xác định được tên riêng, dùng nhãn vai trò nhất quán: `**Người dẫn chương trình (Host):**`, `**Khách mời 1:**`, `**Khách mời 2:**`.
4. **Nhất quán:** Khi một nhân vật được xác định tên ở giữa video, cập nhật lại nhãn tên cho toàn bộ các đoạn phát biểu trước đó của nhân vật đó.

## Quy Cách Trình Bày Đối Thoại

- Mỗi lượt phát biểu bắt đầu bằng tên người nói in đậm: `**[Tên người nói]:** `
- Cuối mỗi đoạn phát biểu bắt buộc gắn kèm mốc thời gian: `[HH:MM:SS → HH:MM:SS]`
- Đoạn nói dài được ngắt thành các đoạn văn 2–4 câu. Các đoạn tiếp theo của CÙNG một người nói KHÔNG lặp lại nhãn tên, chỉ cần gắn timestamp ở cuối đoạn.

### Ví dụ chuẩn:
```markdown
**Nguyễn Văn A:** Vấn đề lớn nhất của việc mở rộng hệ thống microservices không nằm ở công nghệ, mà nằm ở ranh giới dữ liệu giữa các dịch vụ. [00:02:15 → 00:02:24]

Nếu bạn chia nhỏ database quá sớm, bạn sẽ phải đối mặt với bài toán distributed transactions cực kỳ phức tạp. [00:02:24 → 00:02:35]

**Trần Thị B (Host):** Vậy theo anh, khi nào một team nên bắt đầu phân tách dịch vụ từ monolith sang microservices? [00:02:36 → 00:02:42]
```
