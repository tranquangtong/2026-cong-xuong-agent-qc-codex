# QA Report: Course Introduction, ONE Business Credo, ONE Code of Conduct Introduction

**Source URL**: `https://360.articulate.com/review/content/2d7bbaed-07ca-41ce-822c-8b51ff989ab9/review`  
**Execution mode**: Playwright browser pass via direct Rise asset URL resolved from the public Review 360 item on April 17, 2026  
**Sections tested**: `Course Introduction`, `ONE Business Credo`, `ONE Code of Conduct Introduction`  

## Summary
This pass covered the learner flow from the course landing experience through `Course Introduction`, `ONE Business Credo`, and `ONE Code of Conduct Introduction`. The public Review 360 shell was opened first, then the live Rise asset currently served behind that review item was tested directly for navigation, reveal content, and knowledge check behaviour.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Section Label Consistency | While viewing `ONE Business Credo`, the lesson label above the page content reads `Lesson 1 - Course Introduction`. | Learners can lose orientation because the lesson label does not match the lesson currently on screen. | Update the lesson label so it matches `ONE Business Credo`. |
| ID-002 | **Minor** | Section Label Consistency | While viewing `ONE Code of Conduct Introduction`, the lesson label above the page content reads `Lesson 2 - ONE Business Credo`. | This creates the same orientation problem at the start of Chapter 2 and weakens navigation clarity. | Update the lesson label so it matches `ONE Code of Conduct Introduction`. |
| ID-003 | **Minor** | Grammar | In the `ONE Business Credo` knowledge check, Q2 and its feedback use `As an ONE employee...` and `As an ONE employee, you must comply...`. | The repeated article error is visible in assessment content and reduces editorial quality. | Change both instances to `As a ONE employee...`. |
| ID-004 | **Minor** | Grammar | In `ONE Code of Conduct Introduction`, Learning Objective 2 says `Apply the principles of our Business Credo to behaviour and conduct in workplace.` | The missing article makes the learning objective read awkwardly in a prominent instructional block. | Revise the sentence to `...to behaviour and conduct in the workplace.` |

## What Was Verified

- Opened the public Review 360 item and captured the review-shell state.
- Resolved and tested the current live Rise asset served by the review item.
- `Course Introduction`:
- Reviewed the visible welcome copy, table of contents, and learner instructions.
- Verified that `I am ready to explore the ONE Business Credo` routes to `ONE Business Credo`.
- `ONE Business Credo`:
- Reviewed the landing content and verified the in-lesson `CONTINUE` action.
- Opened all five credo principle accordions and inspected the newly revealed on-screen text.
- Verified Knowledge Check Q1 correct path by selecting the five valid credo principles.
- Verified Knowledge Check Q2 wrong path with `Yes`, then correct path with `No`.
- Verified that the completion CTA routes forward to `ONE Code of Conduct Introduction`.
- `ONE Code of Conduct Introduction`:
- Reviewed the visible lesson copy and learning objectives.
- Verified that `Go to Section 1 of the Code` routes to `1. Act as ONE`.

## Notes

- No blocking navigation defects were observed in the tested scope.
- Evidence for this pass is stored in the sibling `artifacts/` folder, including the review-shell probe, section probe, and full-page screenshots.

## Bản Dịch Tiếng Việt

**Nguồn URL**: `https://360.articulate.com/review/content/2d7bbaed-07ca-41ce-822c-8b51ff989ab9/review`  
**Chế độ chạy**: kiểm tra bằng Playwright trên direct Rise asset URL được bóc ra từ public Review 360 item vào ngày 17/04/2026  
**Các mục đã kiểm tra**: `Course Introduction`, `ONE Business Credo`, `ONE Code of Conduct Introduction`  

## Tóm tắt
Lần chạy này bao phủ luồng learner từ màn hình mở đầu khóa học qua `Course Introduction`, `ONE Business Credo`, và `ONE Code of Conduct Introduction`. Public Review 360 shell được mở trước, sau đó phần Rise asset live đang nằm phía sau review item được test trực tiếp để kiểm tra navigation, nội dung reveal, và hành vi knowledge check.

## Findings

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Tính nhất quán nhãn section | Khi xem `ONE Business Credo`, nhãn lesson phía trên nội dung hiển thị `Lesson 1 - Course Introduction`. | Learner có thể bị lệch định hướng vì nhãn lesson không khớp với lesson đang hiển thị. | Cập nhật nhãn lesson để khớp với `ONE Business Credo`. |
| ID-002 | **Minor** | Tính nhất quán nhãn section | Khi xem `ONE Code of Conduct Introduction`, nhãn lesson phía trên nội dung hiển thị `Lesson 2 - ONE Business Credo`. | Điều này tạo ra cùng một vấn đề định hướng ở đầu Chapter 2 và làm giảm độ rõ ràng của điều hướng. | Cập nhật nhãn lesson để khớp với `ONE Code of Conduct Introduction`. |
| ID-003 | **Minor** | Ngữ pháp | Trong knowledge check của `ONE Business Credo`, Q2 và feedback dùng `As an ONE employee...` và `As an ONE employee, you must comply...`. | Lỗi mạo từ này lặp lại trong nội dung assessment và làm giảm chất lượng biên tập. | Đổi cả hai chỗ thành `As a ONE employee...`. |
| ID-004 | **Minor** | Ngữ pháp | Trong `ONE Code of Conduct Introduction`, Learning Objective 2 ghi `Apply the principles of our Business Credo to behaviour and conduct in workplace.` | Việc thiếu mạo từ khiến objective đọc chưa tự nhiên trong một khối nội dung hướng dẫn nổi bật. | Sửa thành `...to behaviour and conduct in the workplace.` |

## Những gì đã được xác minh

- Đã mở public Review 360 item và chụp lại trạng thái review shell.
- Đã bóc và test Rise asset live hiện tại được phục vụ bởi review item.
- `Course Introduction`:
- Đã rà nội dung welcome, mục lục, và phần hướng dẫn cho learner.
- Đã xác minh `I am ready to explore the ONE Business Credo` điều hướng đúng sang `ONE Business Credo`.
- `ONE Business Credo`:
- Đã rà nội dung mở đầu lesson và xác minh hành động `CONTINUE` bên trong lesson.
- Đã mở đủ cả 5 accordion principle và kiểm tra toàn bộ text mới hiện ra.
- Đã xác minh nhánh đúng của Knowledge Check Q1 bằng cách chọn đủ 5 principle hợp lệ.
- Đã xác minh nhánh sai của Knowledge Check Q2 với `Yes`, sau đó nhánh đúng với `No`.
- Đã xác minh CTA hoàn tất điều hướng tiếp sang `ONE Code of Conduct Introduction`.
- `ONE Code of Conduct Introduction`:
- Đã rà nội dung hiển thị và các learning objectives.
- Đã xác minh `Go to Section 1 of the Code` điều hướng đúng sang `1. Act as ONE`.

## Ghi chú

- Không ghi nhận lỗi điều hướng mang tính chặn trong phạm vi đã test.
- Evidence của lần chạy này nằm trong thư mục `artifacts/` cùng bundle, gồm review-shell probe, section probe, và các ảnh chụp full-page.
