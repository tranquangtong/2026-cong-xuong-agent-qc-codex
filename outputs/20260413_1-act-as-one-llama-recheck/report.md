# QA Report: 1. Act As ONE

**Source URL**: `https://360.articulate.com/review/content/7b72d754-b16e-4d51-9083-1ae84d185ad9/review`  
**Execution mode**: Playwright browser pass via direct Rise asset URL resolved from the review item  
**Section tested**: `1. Act As ONE`  

## Summary
This pass focused on section `1. Act As ONE`, including the section heading, visible responsibility content, and the Knowledge Check flow. The public Review 360 link is currently returning an `Item not found | Review 360` shell for signed-out access, so the course QC was executed against the direct Rise asset captured from the review item's underlying asset URL.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Capitalisation Consistency | The left navigation shows `1. Act as ONE`, while the in-page heading shows `1. Act As ONE`. | Inconsistent casing weakens editorial consistency inside the same lesson. | Standardize the title so the navigation label and the in-page heading use the same casing. |
| ID-002 | **Major** | Grammar | The Top Management copy says `Top management act with integrity, showing the commitment in achieving the spirit and ideals set forth in this Code.` | This is a subject-verb agreement error in a highly visible standards statement and reduces language quality. | Change the sentence to `Top management acts with integrity...` or revise the subject so the verb agrees correctly. |
| ID-003 | **Minor** | Section Label Consistency | The page shows `Lesson 3 - Code of Conduct Introduction` directly above section `1. Act As ONE`. | Learners may lose orientation because the lesson label does not match the section currently being viewed. | Update the lesson label so it matches section 1 instead of the earlier introduction lesson. |

## What Was Verified

- Opened the public Review 360 link and confirmed that the current shell only exposes a signed-out `Item not found` wrapper.
- Opened the direct Rise asset URL associated with the review item.
- Navigated specifically to section `1. Act as ONE`.
- Clicked both visible interactives:
  - `Top Management`
  - `ONE Employees`
- Verified the Knowledge Check entry state:
  - prompt `Is this compliant with ONE's Code of Conduct?`
  - choices `Yes` and `No`
- Verified the incorrect path:
  - selecting `Yes` shows `Try Again!`
- Verified the correct path:
  - selecting `No` shows `Correct!`
  - a `CONTINUE` control appears after the correct answer

## Notes

- This pass did not produce a separate finding for the `ONE Employees` reveal copy because the evidence captured in this run was not strong enough to support a precise language or logic defect.
- The report reflects only what was directly visible and reproducible in the live browser pass.

## Bản Dịch Tiếng Việt

**Nguồn URL**: `https://360.articulate.com/review/content/7b72d754-b16e-4d51-9083-1ae84d185ad9/review`  
**Chế độ chạy**: kiểm tra bằng Playwright trên direct Rise asset URL được bóc ra từ review item  
**Mục đã kiểm tra**: `1. Act As ONE`  

## Tóm tắt
Lần kiểm tra này tập trung vào mục `1. Act As ONE`, bao gồm tiêu đề section, phần nội dung trách nhiệm đang hiển thị, và luồng Knowledge Check. Link public Review 360 hiện đang trả về lớp shell `Item not found | Review 360` đối với trạng thái chưa đăng nhập, nên phần QC course được thực hiện trên direct Rise asset URL nằm sau review item đó.

## Findings

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Tính nhất quán viết hoa | Điều hướng bên trái hiển thị `1. Act as ONE`, trong khi tiêu đề trong trang hiển thị `1. Act As ONE`. | Việc viết hoa không nhất quán làm giảm tính đồng bộ biên tập trong cùng một bài học. | Chuẩn hóa tiêu đề để nhãn điều hướng và tiêu đề trong trang dùng cùng một kiểu viết hoa. |
| ID-002 | **Major** | Ngữ pháp | Nội dung Top Management hiển thị câu `Top management act with integrity, showing the commitment in achieving the spirit and ideals set forth in this Code.` | Đây là lỗi hòa hợp chủ ngữ - động từ trong một câu chuẩn mực xuất hiện rất nổi bật, làm giảm chất lượng ngôn ngữ của khóa học. | Đổi câu thành `Top management acts with integrity...` hoặc chỉnh lại chủ ngữ để động từ hòa hợp đúng. |
| ID-003 | **Minor** | Tính nhất quán nhãn section | Trang hiển thị `Lesson 3 - Code of Conduct Introduction` ngay phía trên section `1. Act As ONE`. | Learner có thể bị mất định hướng vì nhãn lesson không khớp với section mà họ đang xem. | Cập nhật nhãn lesson để khớp với section 1 thay vì lesson introduction trước đó. |

## Những gì đã được xác minh

- Đã mở public Review 360 link và xác nhận lớp shell hiện tại chỉ hiển thị wrapper `Item not found` dành cho trạng thái chưa đăng nhập.
- Đã mở direct Rise asset URL gắn với review item đó.
- Đã điều hướng đúng tới section `1. Act as ONE`.
- Đã click cả 2 interactive đang hiển thị:
  - `Top Management`
  - `ONE Employees`
- Đã xác minh trạng thái vào Knowledge Check:
  - câu hỏi `Is this compliant with ONE's Code of Conduct?`
  - hai lựa chọn `Yes` và `No`
- Đã xác minh nhánh trả lời sai:
  - chọn `Yes` sẽ hiện `Try Again!`
- Đã xác minh nhánh trả lời đúng:
  - chọn `No` sẽ hiện `Correct!`
  - sau đáp án đúng có nút `CONTINUE`

## Ghi chú

- Lần chạy này chưa tạo finding riêng cho phần copy ẩn của `ONE Employees` vì bằng chứng thu được chưa đủ mạnh để kết luận một lỗi ngôn ngữ hoặc logic cụ thể.
- Report này chỉ phản ánh những gì đã nhìn thấy và tái hiện được rõ ràng trong lần chạy browser thực tế.
