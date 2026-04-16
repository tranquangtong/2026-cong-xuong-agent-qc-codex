# QA Report: 1. Act as ONE
**Course**: [Legal & GA] ONE Business Credo & Code of Conduct  
**Section tested**: `1. Act as ONE`  
**Test date**: 2026-04-12  
**Method**: Browser-assisted QC on the public Articulate Review item, with interactive traversal of all visible reveal items and Knowledge Check steps.

## Summary
The section is generally functional: both reveal items open correctly, the Knowledge Check advances through multiple scenarios, incorrect answers trigger retry feedback, and the scenario reaches a completed state. The main issues found are editorial consistency and language quality rather than broken functionality.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Capitalisation Consistency | The left navigation lists `1. Act as ONE`, while the section heading on the page reads `1. Act As ONE`. | Inconsistent title casing weakens editorial consistency inside the same lesson. | Standardize the section title so the sidebar and the in-page heading use the same casing. |
| ID-002 | **Major** | Grammar/Spelling | In the `Top Management` reveal, the text says: `Top management act with integrity...` | This is a subject-verb agreement error and reduces professionalism in compliance training content. | Change to `Top management acts with integrity...` or rewrite the subject as plural if `act` is intended. |
| ID-003 | **Minor** | British English Consistency | In the `ONE Employees` reveal, the text says: `prioritizing fairness and respect.` | The course requirements and stored QA lessons emphasize consistent British English. | Change `prioritizing` to `prioritising`. |
| ID-004 | **Suggestion** | UI Label Style | Visible interactive labels such as `Top Management`, `ONE Employees`, and `Go to Section 2 of the Code` are not in ALL CAPS, while `project_x_req.md` states button labels must be ALL CAPS. | If that requirement applies to this course, the UI styling is inconsistent with the project standard. | Confirm whether the ALL-CAPS button rule applies to this item; if yes, standardize the visible CTA/interactive labels. |

## What Was Verified
- Opened the public Articulate Review item and navigated specifically to `1. Act as ONE`.
- Clicked both reveal items: `Top Management` and `ONE Employees`.
- Advanced the Knowledge Check past the first scenario.
- Verified the first scenario marks `No` as correct and displays explanatory feedback.
- Advanced to the second scenario (`The silent bystander`).
- Verified an incorrect answer produces `Try Again!`.
- Verified the correct answer (`No`) produces the expected explanation.
- Continued until the section reached `Scenario Complete!`.

## Notes
- No broken navigation or dead click targets were observed within this section.
- The Knowledge Check contains more than one step, so stopping after the first question would miss required coverage.
- Supporting screenshots for this run are stored in the sibling `artifacts/` folder.

## Bản Dịch Tiếng Việt
**Khóa học**: [Legal & GA] ONE Business Credo & Code of Conduct  
**Mục đã kiểm tra**: `1. Act as ONE`  
**Ngày kiểm tra**: 2026-04-12  
**Phương pháp**: QC có hỗ trợ trình duyệt trên Review item public của Articulate, bao gồm đi qua toàn bộ reveal item đang hiển thị và các bước của Knowledge Check.

### Tóm tắt
Nhìn chung mục này hoạt động được: cả hai reveal item đều mở đúng, Knowledge Check chuyển qua nhiều tình huống, câu trả lời sai sẽ hiện phản hồi thử lại, và kịch bản kết thúc ở trạng thái hoàn tất. Các vấn đề chính được phát hiện nằm ở tính nhất quán biên tập và chất lượng ngôn ngữ hơn là lỗi hỏng chức năng.

### Các lỗi/phát hiện

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Tính nhất quán viết hoa | Điều hướng bên trái hiển thị `1. Act as ONE`, trong khi tiêu đề trong trang hiển thị `1. Act As ONE`. | Việc viết hoa không nhất quán làm giảm tính đồng bộ biên tập trong cùng một bài học. | Chuẩn hóa tiêu đề mục để sidebar và tiêu đề trong trang dùng cùng một kiểu viết hoa. |
| ID-002 | **Major** | Ngữ pháp/Chính tả | Trong reveal `Top Management`, nội dung ghi: `Top management act with integrity...` | Đây là lỗi hòa hợp chủ ngữ - động từ và làm giảm tính chuyên nghiệp của nội dung đào tạo compliance. | Đổi thành `Top management acts with integrity...` hoặc viết lại chủ ngữ ở dạng số nhiều nếu muốn giữ `act`. |
| ID-003 | **Minor** | Tính nhất quán British English | Trong reveal `ONE Employees`, nội dung ghi: `prioritizing fairness and respect.` | Yêu cầu của khóa học và các bài học QA đã lưu đều nhấn mạnh việc dùng nhất quán British English. | Đổi `prioritizing` thành `prioritising`. |
| ID-004 | **Suggestion** | Kiểu hiển thị nhãn UI | Các nhãn interactive nhìn thấy như `Top Management`, `ONE Employees`, và `Go to Section 2 of the Code` không viết HOA toàn bộ, trong khi `project_x_req.md` quy định nhãn nút phải là ALL CAPS. | Nếu requirement đó áp dụng cho khóa học này thì UI đang không đồng nhất với tiêu chuẩn dự án. | Xác nhận requirement ALL CAPS có áp dụng cho item này hay không; nếu có, chuẩn hóa các CTA/interactive label hiển thị về dạng ALL CAPS. |

### Nội dung đã xác minh
- Đã mở public Articulate Review item và điều hướng đúng tới mục `1. Act as ONE`.
- Đã click cả hai reveal item: `Top Management` và `ONE Employees`.
- Đã đi qua Knowledge Check vượt qua tình huống đầu tiên.
- Đã xác minh ở tình huống đầu tiên, đáp án `No` được chấm đúng và có phản hồi giải thích.
- Đã chuyển sang tình huống thứ hai (`The silent bystander`).
- Đã xác minh câu trả lời sai sẽ hiện `Try Again!`.
- Đã xác minh câu trả lời đúng (`No`) sẽ hiện phần giải thích mong đợi.
- Đã tiếp tục cho tới khi section đạt trạng thái `Scenario Complete!`.

### Ghi chú
- Không phát hiện lỗi điều hướng hỏng hoặc click target chết trong phạm vi mục này.
- Knowledge Check của mục này có nhiều hơn một bước, nên nếu dừng sau câu đầu tiên sẽ bỏ sót phạm vi test bắt buộc.
- Các ảnh chụp hỗ trợ cho lần chạy này được lưu trong thư mục `artifacts/` cùng cấp.
