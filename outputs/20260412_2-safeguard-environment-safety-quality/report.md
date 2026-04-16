# QA Report: 2. Safeguard our Environment, Safety and Quality
**Course**: [Legal & GA] ONE Business Credo & Code of Conduct  
**Section tested**: `2. Safeguard our Environment, Safety and Quality`  
**Test date**: 2026-04-12  
**Method**: Headless Playwright verification with tab traversal and on-screen content inspection.

## Summary
The section loads and the three visible tabs are clickable, but the main issue is in the Knowledge Check: the drag-and-drop activity appears to be pre-marked as correct before any learner interaction. There is also a title/lesson-label inconsistency in the section header area.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Major** | Knowledge Check Logic | On initial load of section 2, the drag-and-drop activity already shows `Correct` before any drag/drop action is performed. The page still displays draggable/selectable items and a `SUBMIT` button at the same time. | Learners may receive completion feedback without actually answering the question, which undermines assessment validity and can hide scoring/progress defects. | Reset the interaction state so the activity starts unanswered, shows no success feedback before submission, and only marks `Correct` after a valid learner attempt. |
| ID-002 | **Minor** | Section Label Consistency | The page shows `Lesson 4 - 1. Act as ONE` directly above the section heading `2. Safeguard our Environment, Safety and Quality`. | This creates confusion about whether the learner is in section 1 or section 2 and weakens navigation clarity. | Update the lesson label so it matches the current section title and numbering. |
| ID-003 | **Suggestion** | Content Presentation | In the `IMPROVEMENT OF SERVICE QUALITY` tab, the environment-focused sentence `We protect the environment and ecosystems by taking action on climate change, preventing marine pollution and using resources responsibly.` still appears below the tab-specific service quality content. | If this is unintended carry-over from another tab, it can blur the distinction between tab topics and reduce content clarity. | Confirm whether the environment paragraph is meant to persist across all tabs; if not, restrict each tab to its own topic-specific copy. |

## What Was Verified
- Opened the public review item and navigated directly to `2. Safeguard our Environment, Safety and Quality`.
- Confirmed the section renders with three visible tabs:
  - `PURSUIT OF SAFETY`
  - `SAFEGUARDING OUR ENVIRONMENT`
  - `IMPROVEMENT OF SERVICE QUALITY`
- Clicked each tab and captured the resulting on-screen text.
- Inspected the Knowledge Check block and confirmed it is a drag-and-drop style mapping activity.
- Observed that the page shows `Correct` immediately, even before any learner action was performed.

## Notes
- I did not complete a real drag-and-drop submission in this pass because the pre-rendered `Correct` state is already the primary defect and may interfere with trustworthy interaction testing.
- Supporting screenshots for this run are stored in the sibling `artifacts/` folder.

## Bản Dịch Tiếng Việt
**Khóa học**: [Legal & GA] ONE Business Credo & Code of Conduct  
**Mục đã kiểm tra**: `2. Safeguard our Environment, Safety and Quality`  
**Ngày kiểm tra**: 2026-04-12  
**Phương pháp**: Xác minh bằng Playwright headless, đi qua các tab và kiểm tra nội dung hiển thị trên màn hình.

### Tóm tắt
Mục này tải lên bình thường và ba tab nhìn thấy đều bấm được, nhưng vấn đề chính nằm ở Knowledge Check: hoạt động drag-and-drop dường như đã bị đánh dấu đúng từ trước khi learner thực hiện bất kỳ tương tác nào. Ngoài ra còn có sự không nhất quán giữa tiêu đề section và nhãn lesson ở phần đầu trang.

### Các lỗi/phát hiện

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Major** | Logic Knowledge Check | Ngay khi vừa vào mục 2, hoạt động drag-and-drop đã hiển thị `Correct` trước khi thực hiện bất kỳ thao tác kéo/thả nào. Trang vẫn đồng thời hiển thị các item có thể chọn/kéo thả và nút `SUBMIT`. | Learner có thể nhận phản hồi hoàn thành mà không thực sự trả lời câu hỏi, làm giảm tính hợp lệ của assessment và có thể che giấu lỗi scoring/progress. | Reset trạng thái tương tác để hoạt động bắt đầu ở trạng thái chưa trả lời, không hiển thị phản hồi thành công trước khi submit, và chỉ đánh dấu `Correct` sau một lần trả lời hợp lệ. |
| ID-002 | **Minor** | Tính nhất quán nhãn section | Trang hiển thị `Lesson 4 - 1. Act as ONE` ngay phía trên tiêu đề section `2. Safeguard our Environment, Safety and Quality`. | Điều này gây nhầm lẫn cho learner về việc họ đang ở section 1 hay section 2 và làm giảm độ rõ ràng khi điều hướng. | Cập nhật nhãn lesson để khớp với tiêu đề và số thứ tự của section hiện tại. |
| ID-003 | **Suggestion** | Trình bày nội dung | Trong tab `IMPROVEMENT OF SERVICE QUALITY`, câu mang nội dung về môi trường `We protect the environment and ecosystems by taking action on climate change, preventing marine pollution and using resources responsibly.` vẫn xuất hiện bên dưới nội dung riêng của tab service quality. | Nếu đây là nội dung bị sót từ tab khác, nó sẽ làm mờ ranh giới giữa các chủ đề tab và giảm độ rõ ràng của nội dung. | Xác nhận đoạn về môi trường có được chủ đích giữ lại trên mọi tab hay không; nếu không, giới hạn mỗi tab chỉ hiển thị nội dung đúng chủ đề của tab đó. |

### Nội dung đã xác minh
- Đã mở review item public và điều hướng trực tiếp tới `2. Safeguard our Environment, Safety and Quality`.
- Đã xác nhận section render với ba tab hiển thị:
  - `PURSUIT OF SAFETY`
  - `SAFEGUARDING OUR ENVIRONMENT`
  - `IMPROVEMENT OF SERVICE QUALITY`
- Đã click từng tab và capture nội dung hiển thị trên màn hình sau khi click.
- Đã kiểm tra khối Knowledge Check và xác nhận đây là một activity dạng kéo-thả ghép cặp.
- Đã quan sát thấy trang hiển thị `Correct` ngay lập tức, trước cả khi learner có tương tác.

### Ghi chú
- Mình chưa hoàn thành một lần drag-and-drop thực sự trong pass này vì trạng thái `Correct` hiển thị sẵn đã là defect chính và có thể làm nhiễu việc kiểm tra interaction một cách đáng tin cậy.
- Các ảnh chụp hỗ trợ cho lần chạy này được lưu trong thư mục `artifacts/` cùng cấp.
