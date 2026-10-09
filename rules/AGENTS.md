# ytbknot Plugin Rules (Antigravity)

Quy tắc bắt buộc khi kích hoạt skill `ytbknot`:

## 1. Mặc định Tiếng Việt Kỹ Thuật
- Toàn bộ nội dung phân tích và ghi chú học tập PHẢI viết bằng **Tiếng Việt**.
- Thuật ngữ kỹ thuật tiếng Anh chuẩn (như *Git Worktree*, *Context Window Drift*, *MCP Server*, *Linter*, *Unit Test*...) giữ nguyên từ ngữ gốc, có giải thích bản chất ở bảng thuật ngữ.
- Văn phong khách quan, gãy gọn, tập trung vào bản chất kỹ thuật và giải pháp. Tuyệt đối không dùng từ ngữ sáo rỗng hoặc đao to búa lớn.

## 2. Tiêu Chuẩn Trình Bày: Không Emoji & Tiêu Đề Ngắn Gọn
- **Tuyệt đối không dùng emoji/icon trang trí** (cấm các biểu tượng như bóng đèn, ngọn lửa, tên lửa...).
- **Tiêu đề (H2, H3) phải cực kỳ ngắn gọn, thuần Tiếng Việt**: Không chêm tiếng Anh vào ngoặc đơn `(...)` ở tiêu đề. Tiêu đề dứt khoát từ 2 đến 4 từ.

## 3. Khung Hình Thông Minh: Tách Biệt Bộ Ảnh & Khớp Nội Dung
- **Tách biệt bộ ảnh:** Bộ ảnh nằm riêng tại `<OUTPUT_FOLDER>/screenshots/`, file note nằm độc lập ở thư mục bài giảng.
- **AI lọc khung hình có căn cứ:**
  - Không chụp mù quáng ở mốc đầu chapter.
  - Phải phân tích kịch bản để tìm chính xác giây tác giả **thực sự show màn hình code, gõ lệnh terminal, mở VS Code hoặc chiếu sơ đồ**.
  - **Bài giảng thao tác màn hình (Live-coding / Terminal)**: Bắt khung hình ngay khi thao tác lệnh hoặc đoạn mã được thực thi hoàn tất.
  - **Bài giảng giải đề, slide trình chiếu hoặc bảng viết (Slide-based / Whiteboard / Problem-solving)**:
    - BẮT BUỘC chụp tại mốc **CUỐI PHÂN ĐOẠN** của từng câu/mục (ngay trước khi giảng viên chuyển sang nội dung kế tiếp từ 2 đến 5 giây).
    - Đây là thời điểm màn hình hiển thị trọn vẹn 100% nội dung ghi chú viết tay, lời giải chi tiết, phân tích đáp án và các từ vựng mở rộng mà giảng viên đã tổng hợp (tránh chụp đầu phân đoạn khi slide còn trắng trơn).
- **Cấm nhồi ảnh chân dung tác giả (Talking Head):**
  - Những phân đoạn tác giả chỉ ngồi nói chuyện chay bằng miệng mà không có màn hình code/slide: **Không chụp ảnh rác**. Chỉ tóm tắt luận điểm kỹ thuật bằng lời.

## 4. Cấu Trúc Ghi Chú Theo Mức Độ Chi Tiết

Mặc định áp dụng mức độ `standard` nếu người dùng không chỉ định. Khi có yêu cầu hoặc cờ `--detail`:

* **Mức độ Tóm lược (`--detail brief`):**
  - Giữ: `Thuật ngữ`, `Tổng luận chuyên đề`, `Lệnh & Công cụ`, `Đánh đổi & Rủi ro`.
  - Lược bỏ: Mục `Bóc tách chi tiết` để đọc nhanh trong 2-3 phút.
  - Số lượng ảnh: Chỉ chụp 2-4 ảnh kiến trúc hoặc sơ đồ cốt lõi nhất.

* **Mức độ Tiêu chuẩn (`--detail standard` - Mặc định):**
  - Cấu trúc 2 tầng chuẩn mực: Đọc nhanh Tầng 1 và bóc tách theo từng khối 10-15 phút ở Tầng 2.

* **Mức độ Siêu chi tiết (`--detail deep`):**
  - **Dòng thời gian vi mô (Micro-timeline):** Mục `Bóc tách chi tiết` chia nhỏ theo từng mốc 1-3 phút hoặc từng câu hỏi/thao tác lệnh đơn lẻ.
  - Mỗi tiểu mục bắt buộc gắn mốc thời gian dạng `### [HH:MM:SS] Tên phân đoạn`.
  - Phân tích cặn kẽ 100% bối cảnh, câu lệnh, phản hồi của hệ thống, logic giải thích và các ngoại lệ/edge cases mà tác giả nhắc tới.
  - Trích xuất ảnh dày đặc cho từng bước thực thi hoặc slide thay đổi nội dung.

```markdown
# [Tên Video / Tiêu đề bài giảng]

* **Kênh:** [Tên kênh] | **Thời lượng:** [HH:MM:SS] | **Ngày:** [YYYY-MM-DD]
* **Video:** [URL gốc]

---

## Thuật ngữ
(Bảng tra cứu thuật ngữ và từ viết tắt: Thuật ngữ | Tiếng Anh | Giải thích)

## Tổng luận chuyên đề
(Tầng 1: Đọc nhanh 5 phút nắm 100% tinh hoa, phân loại theo 3-4 chuyên đề lớn kèm công thức và quy tắc vàng)

## Bóc tách chi tiết
(Tầng 2: Đi sâu từng câu hỏi hoặc phân đoạn theo timeline; đầy đủ đề bài/thao tác, phân tích từng phương án/dòng lệnh, kiến thức mở rộng và khung hình tương ứng)

## Trích dẫn then chốt
(3-5 câu phát biểu nguyên văn đắt giá nhất từ transcript kèm link timestamp)

## Lệnh & Công cụ
(Khối lệnh CLI copy dùng ngay hoặc công thức nhận diện nhanh)

## Đánh đổi & Rủi ro
(Đánh đổi tài nguyên, chi phí token, điểm mù và nguy cơ thực tế)
```
