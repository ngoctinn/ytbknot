# ytbknot Plugin Rules (Antigravity)

## 0. Activation Signals
Khi kích hoạt hoặc chạy bất kỳ tác vụ nào liên quan đến plugin `ytbknot` (skill hoặc subagent):
- Format (ytbknot-* only): `> 🎬 **YTBKNOT** → <name> activated`
- Ví dụ: `> 🎬 **YTBKNOT** → ytbknot activated`, `> 🎬 **YTBKNOT** → ytbknot-index activated`, `> 🎬 **YTBKNOT** → ytbknot-writer agent activated`
- Xuất chính xác 1 dòng tín hiệu ở đầu lượt phản hồi.

Quy tắc bắt buộc khi kích hoạt skill `ytbknot`:

## 1. Mặc định Tiếng Việt Kỹ Thuật
- Toàn bộ nội dung phân tích và ghi chú học tập PHẢI viết bằng **Tiếng Việt**.
- Thuật ngữ kỹ thuật tiếng Anh chuẩn (như *Git Worktree*, *Context Window*, *MCP Server*, *Connection Pooling*, *Unit Test*...) giữ nguyên từ ngữ gốc, có giải thích bản chất ở bảng thuật ngữ.
- **Cấm chèn tiếng Anh trong ngoặc đơn dạng song ngữ rườm rà**: Tuyệt đối KHÔNG viết kiểu `Tiếng Việt (English)` trong toàn bộ bài viết (ví dụ: cấm viết `Tuần tự hóa (Serialization)`, `Độ phức tạp chu trình (Cyclomatic Complexity)`, `Môi trường cô lập (Sandboxed Environment)`). Đã có bảng thuật ngữ tra cứu riêng, trong nội dung bài viết chỉ dùng một cách gọi duy nhất (hoặc từ thuần Việt gãy gọn, hoặc thuật ngữ gốc tiếng Anh), không lặp lại từ trong ngoặc đơn.
- Văn phong khách quan, gãy gọn, tập trung vào bản chất kỹ thuật và giải pháp. Tuyệt đối không dùng từ ngữ sáo rỗng hoặc đao to búa lớn.

## 2. Tiêu Chuẩn Trình Bày: Không Emoji & Tiêu Đề Ngắn Gọn
- **Tuyệt đối không dùng emoji/icon trang trí** (cấm các biểu tượng như bóng đèn, ngọn lửa, tên lửa...).
- **Tiêu đề (H2, H3) phải cực kỳ ngắn gọn, thuần Tiếng Việt**: Không chêm tiếng Anh vào ngoặc đơn `(...)` ở tiêu đề. Tiêu đề dứt khoát từ 2 đến 4 từ.

## 3. Khung Hình Thông Minh: Tách Biệt Bộ Ảnh & Khớp Nội Dung
- **Tách biệt bộ ảnh:** Bộ ảnh nằm riêng tại `<OUTPUT_FOLDER>/screenshots/`, file note nằm độc lập ở thư mục bài giảng.
- **Tối ưu WebP chất lượng cao:** Toàn bộ ảnh chụp màn hình, sơ đồ và ảnh bìa lưu ở định dạng **WebP** (sử dụng chế độ Lossless hoặc Near-Lossless chất lượng 90-95%) để giảm 80-90% dung lượng so với PNG mà vẫn giữ nguyên độ sắc nét của mã nguồn và sơ đồ.
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
  - **Nguyên tắc cốt lõi:** Ghi chú phải có giá trị **thay thế hoàn toàn video** — người học đọc bài viết có thể nắm trọn vẹn 100% kiến thức (tự giải được đề, gõ theo được code, hiểu rõ kiến trúc) mà không cần phải mở lại video để dò xem tác giả đang nói gì.
  - **Dòng thời gian vi mô (Micro-timeline):** Mục `Bóc tách chi tiết` chia nhỏ theo từng mốc 1-3 phút hoặc từng câu hỏi/thao tác lệnh đơn lẻ.
  - **Link mốc thời gian bấm được (Clickable Timestamp Link):** Mỗi tiểu mục bắt buộc gắn link mốc thời gian dẫn thẳng đến giây đó trên YouTube, định dạng: `### [[HH:MM:SS](<URL_VIDEO>&t=<GIÂY>s)] Tên phân đoạn` (hoặc `### [HH:MM:SS](<URL_VIDEO>&t=<GIÂY>s) Tên phân đoạn`). Tuyệt đối không để mốc thời gian dạng text chết không bấm được.
  - Trích xuất ảnh dày đặc cho từng bước thực thi hoặc slide thay đổi nội dung.
  - **Nhận diện thể loại bài giảng (Lecture Archetypes):** AI tự động nhận diện bài giảng thuộc thể loại nào dưới đây để áp dụng khung bóc tách tương ứng, tuyệt đối KHÔNG tóm tắt đại khái:
    1. **Bài giảng Coding và kỹ thuật thực hành:**
       - *Mã nguồn đầy đủ:* Trích xuất code block hoặc câu lệnh thực tế (không mô tả chay bằng lời).
       - *Bóc tách chi tiết:* Giải thích rõ mục đích của từng cú pháp, tham số, annotation, cấu hình và phản hồi kết quả terminal hoặc DevTools.
    2. **Bài giảng Giải đề, luyện thi hoặc ngoại ngữ:**
       - *Đầy đủ đề bài:* Ghi rõ câu hỏi, ngữ cảnh và toàn bộ các phương án lựa chọn (A, B, C, D).
       - *Phân tích từng phương án:* Chỉ rõ tại sao phương án này đúng, tại sao các phương án khác sai (bẫy ngữ pháp, lỗi logic, từ khóa gây nhiễu).
       - *Mở rộng kiến thức:* Tổng hợp bảng từ vựng chuyên ngành, ngữ pháp cốt lõi hoặc công thức liên quan xuất hiện trong câu đó.
    3. **Bài giảng Lý thuyết, sơ đồ hoặc kiến trúc:**
       - *Bóc tách sơ đồ:* Phân tích từng luồng dữ liệu, từng thành phần hiển thị trên màn hình hoặc bảng vẽ.
       - *Cơ chế vận hành:* Làm rõ nguyên lý hoạt động nội tại, điều kiện kích hoạt, công thức toán hoặc kinh tế và các định luật liên quan.
       - *Đánh đổi và ngoại lệ:* Ghi nhận đầy đủ các tình huống ngoại lệ, rủi ro và sự đánh đổi mà giảng viên phân tích.
    4. **Hướng dẫn Công cụ và giao diện:**
       - *Quy trình từng bước:* Liệt kê chính xác đường dẫn click chuột, menu, phím tắt hoặc thông số cấu hình cụ thể trên từng màn hình.
       - *Ý nghĩa tham số:* Giải thích tác dụng thực tế của các tùy chọn được bật hoặc tắt trong công cụ.

```markdown
# [Tên Video / Tiêu đề bài giảng]

* **Kênh:** [Tên kênh] | **Thời lượng:** [HH:MM:SS] | **Ngày:** [YYYY-MM-DD]
* **Video:** [URL gốc]

---

## Thuật ngữ
(Bảng tra cứu thuật ngữ và từ viết tắt: Thuật ngữ | Giải thích)

## Tổng luận chuyên đề
(Tầng 1: Đọc nhanh 5 phút nắm 100% tinh hoa, phân loại theo 3-4 chuyên đề lớn kèm công thức và quy tắc vàng)

## Bóc tách chi tiết
(Tầng 2: Đi sâu từng câu hỏi hoặc phân đoạn theo timeline; tiêu đề mỗi tiểu mục BẮT BUỘC chứa link timestamp bấm được dạng `### [[HH:MM:SS](URL?t=Xs)] Tên phân đoạn`; đầy đủ đề bài/thao tác, phân tích từng phương án/dòng lệnh, kiến thức mở rộng và khung hình tương ứng)

## Trích dẫn then chốt
(3-5 câu phát biểu nguyên văn đắt giá nhất từ transcript kèm link timestamp)

## Lệnh & Công cụ
(Khối lệnh CLI, công cụ phần mềm hoặc công thức do CHÍNH BÀI GIẢNG / TÁC GIẢ đề cập)

## Đánh đổi & Rủi ro
(Đánh đổi tài nguyên, chi phí token, điểm mù và nguy cơ thực tế)
```
