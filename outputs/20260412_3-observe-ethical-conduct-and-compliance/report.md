# QA Report: 3. Observe Ethical Conduct and Compliance with Laws and Regulations
**Course**: [Legal & GA] ONE Business Credo & Code of Conduct  
**Section tested**: `3. Observe Ethical Conduct and Compliance with Laws and Regulations`  
**Test date**: 2026-04-12  
**Method**: Headless Playwright verification with interactive spot checks and on-screen content inspection.

## Summary
The section contains rich interactive content and the sampled interactive elements do open correctly, but the most significant issues are in the Knowledge Check state and answer content. The page also shows a lesson label mismatch similar to the previous sections.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Major** | Knowledge Check Logic | Both Q.1 and Q.2 already display `Incorrect` and `TAKE AGAIN` immediately on page load, before any learner answer is selected or submitted. | Learners are shown failure feedback without interaction, which breaks assessment credibility and can invalidate completion or scoring logic. | Reset the assessment state so each question loads unanswered, with no correctness feedback shown until the learner submits a response. |
| ID-002 | **Major** | Answer Content Integrity | In Q.2, option A reads: `Agree verbally: It makes sense for the industry to have a standard fee.n time and it isn't a finance role, there is no conflict.` | This answer contains stray text from another scenario, which makes the option visibly corrupted and confusing for the learner. | Clean the option text and ensure each answer choice contains only the intended content for this scenario. |
| ID-003 | **Minor** | Section Label Consistency | The page shows `Lesson 5 - 2. Safeguard our Environment, Safety and Quality` above the heading `3. Observe Ethical Conduct and Compliance with Laws and Regulations`. | The learner can be unsure whether they are viewing section 2 or section 3, reducing navigation clarity. | Update the lesson label so it matches the current section title and numbering. |
| ID-004 | **Suggestion** | Interaction Presentation | Some interactive sequences, such as the conflict-of-interest process, display `1 of 4`, `2 of 4`, `3 of 4`, and `4 of 4` content together in the same view instead of feeling step-based. | If unintended, this weakens the instructional purpose of the stepper and may overwhelm the learner with all stages at once. | Confirm whether all steps are meant to be visible simultaneously; if not, render only the active step until the learner advances. |

## What Was Verified
- Opened the public review item and navigated directly to section 3.
- Opened the bribery content titles:
  - `The "Indirect" Trap`
  - `High-Risk Interactions`
- Opened the insider trading actions:
  - `Action 1`
  - `Action 2`
- Checked the conflict-of-interest stepper around the `START` flow.
- Reviewed the on-screen Knowledge Check scenarios and answer options.

## Notes
- The drag-and-drop style activities in this section also show solved states (`Correct`) without a real interaction pass in this run, which supports the broader pattern of unstable assessment state initialization.
- Supporting screenshots for this run are stored in the sibling `artifacts/` folder.

## Bản Dịch Tiếng Việt
**Khóa học**: [Legal & GA] ONE Business Credo & Code of Conduct  
**Mục đã kiểm tra**: `3. Observe Ethical Conduct and Compliance with Laws and Regulations`  
**Ngày kiểm tra**: 2026-04-12  
**Phương pháp**: Xác minh bằng Playwright headless, có spot check một số interactive và kiểm tra nội dung hiển thị trên màn hình.

### Tóm tắt
Mục này có nhiều nội dung tương tác và các interactive được lấy mẫu đều mở đúng, nhưng các vấn đề nghiêm trọng nhất nằm ở trạng thái của Knowledge Check và nội dung đáp án. Trang cũng hiển thị nhãn lesson bị lệch tương tự các section trước.

### Các lỗi/phát hiện

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Major** | Logic Knowledge Check | Cả Q.1 và Q.2 đều đã hiển thị `Incorrect` và `TAKE AGAIN` ngay khi tải trang, trước khi learner chọn hoặc submit đáp án. | Learner bị hiển thị phản hồi thất bại mà chưa tương tác, làm hỏng độ tin cậy của assessment và có thể làm sai logic completion/scoring. | Reset trạng thái assessment để mỗi câu hỏi tải lên ở trạng thái chưa trả lời, không có feedback đúng/sai cho tới khi learner submit câu trả lời. |
| ID-002 | **Major** | Tính toàn vẹn nội dung đáp án | Ở Q.2, đáp án A hiển thị: `Agree verbally: It makes sense for the industry to have a standard fee.n time and it isn't a finance role, there is no conflict.` | Đáp án này bị lẫn text từ scenario khác, khiến lựa chọn hiển thị bị lỗi và gây khó hiểu cho learner. | Làm sạch nội dung đáp án và bảo đảm mỗi lựa chọn chỉ chứa đúng nội dung được thiết kế cho scenario đó. |
| ID-003 | **Minor** | Tính nhất quán nhãn section | Trang hiển thị `Lesson 5 - 2. Safeguard our Environment, Safety and Quality` phía trên heading `3. Observe Ethical Conduct and Compliance with Laws and Regulations`. | Learner có thể không chắc mình đang ở section 2 hay 3, làm giảm độ rõ ràng khi điều hướng. | Cập nhật nhãn lesson để khớp với tiêu đề và số thứ tự section hiện tại. |
| ID-004 | **Suggestion** | Trình bày tương tác | Một số interactive sequence, như quy trình conflict-of-interest, hiển thị cùng lúc nội dung `1 of 4`, `2 of 4`, `3 of 4`, và `4 of 4` trong cùng một view thay vì mang cảm giác step-by-step. | Nếu đây không phải chủ đích thiết kế, nó làm yếu mục tiêu hướng dẫn theo từng bước và có thể khiến learner bị quá tải thông tin. | Xác nhận xem tất cả các bước có phải được hiển thị đồng thời hay không; nếu không, chỉ render bước đang active cho tới khi learner chuyển bước. |

### Nội dung đã xác minh
- Đã mở review item public và điều hướng trực tiếp tới section 3.
- Đã mở các tiêu đề nội dung về bribery:
  - `The "Indirect" Trap`
  - `High-Risk Interactions`
- Đã mở các action về insider trading:
  - `Action 1`
  - `Action 2`
- Đã kiểm tra stepper conflict-of-interest quanh luồng `START`.
- Đã rà soát các scenario và đáp án hiển thị trong Knowledge Check.

### Ghi chú
- Các activity dạng drag-and-drop trong section này cũng hiển thị trạng thái đã giải (`Correct`) mà chưa có một lượt tương tác thật trong pass này, củng cố thêm pattern lỗi khởi tạo trạng thái assessment không ổn định.
- Các ảnh chụp hỗ trợ cho lần chạy này được lưu trong thư mục `artifacts/` cùng cấp.
