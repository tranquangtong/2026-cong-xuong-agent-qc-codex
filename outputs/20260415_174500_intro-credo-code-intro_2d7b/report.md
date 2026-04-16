# QA Report: Course Introduction, ONE Business Credo, Code of Conduct Introduction

**Source URL**: `https://360.articulate.com/review/content/2d7bbaed-07ca-41ce-822c-8b51ff989ab9/review`  
**Execution mode**: Playwright browser pass via direct Rise asset URL resolved from the public Review 360 item  
**Sections tested**: `Course Introduction`, `ONE Business Credo`, `Code of Conduct Introduction`  

## Summary
This pass focused on the first three lessons of the course: `Course Introduction`, `ONE Business Credo`, and `Code of Conduct Introduction`. The public Review 360 page exposes the review shell and loads the course separately, so the interactive QC pass was executed against the direct Rise asset associated with this review item.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Section Label Consistency | While viewing `ONE Business Credo`, the lesson label above the page content reads `Lesson 1 - Course Introduction`. | Learners can lose orientation because the breadcrumb-style lesson label does not match the lesson currently on screen. | Update the lesson label so it matches `ONE Business Credo`. |
| ID-002 | **Minor** | Section Label Consistency | While viewing `Code of Conduct Introduction`, the lesson label above the page content reads `Lesson 2 - ONE Business Credo`. | This creates the same orientation issue at the start of Chapter 2 and weakens navigation clarity. | Update the lesson label so it matches `Code of Conduct Introduction`. |
| ID-003 | **Minor** | Grammar | In the `ONE Business Credo` knowledge check, the prompt and feedback use `As an ONE employee...` and `As an ONE employee, you must comply...`. | The repeated article error is visible in assessment content and reduces editorial quality. | Change both instances to `As a ONE employee...`. |
| ID-004 | **Minor** | Grammar | In `Code of Conduct Introduction`, Learning Objective 2 says `Apply the principles of our Business Credo to behaviour and conduct in workplace`. | The missing article makes the learning objective read awkwardly in a prominent instructional block. | Revise the sentence to `...to behaviour and conduct in the workplace`. |

## What Was Verified

- Opened the public Review 360 item and captured the review-shell state.
- Resolved and opened the direct Rise asset behind the review item.
- `Course Introduction`:
  - Reviewed the visible lesson content and instructions.
  - Verified that `I'm ready to explore the ONE Business Credo` routes to the `ONE Business Credo` lesson.
- `ONE Business Credo`:
  - Reviewed the landing content and verified the in-lesson `CONTINUE` action.
  - Clicked all five credo principle tabs:
    - `1. Act as ONE`
    - `2. Safeguard Our Environment, Safety, and Quality`
    - `3. Observe Ethical Conduct and Compliance With Laws and Regulations`
    - `4. Nurture an Inclusive Workplace and Respect for Human Rights`
    - `5. Enhance Information Security and Protection of Assets`
  - Verified Knowledge Check Q1 correct path by selecting the five valid credo principles.
  - Verified Knowledge Check Q2 wrong path with `Yes`.
  - Verified Knowledge Check Q2 correct path with `No`.
- `Code of Conduct Introduction`:
  - Reviewed the visible lesson content and learning objectives.
  - Verified that `Go to Section 1 of the Code` routes to section `1. Act as ONE`.

## Notes

- No blocking navigation defects were observed in the three tested lessons.
- Supporting evidence for this pass is stored in the sibling `artifacts/` folder, including the review-shell probe, section probe, and full-page screenshots.

## Bản Dịch Tiếng Việt

**Nguồn URL**: `https://360.articulate.com/review/content/2d7bbaed-07ca-41ce-822c-8b51ff989ab9/review`  
**Chế độ chạy**: kiểm tra bằng Playwright trên direct Rise asset URL được bóc ra từ public Review 360 item  
**Các mục đã kiểm tra**: `Course Introduction`, `ONE Business Credo`, `Code of Conduct Introduction`  

## Tóm tắt
Lần chạy này tập trung vào ba lesson đầu của khóa học: `Course Introduction`, `ONE Business Credo`, và `Code of Conduct Introduction`. Public Review 360 page hiện chủ yếu hiển thị review shell và tải course riêng ở phía sau, nên phần QC tương tác được thực hiện trên direct Rise asset gắn với review item này.

## Findings

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Tính nhất quán nhãn section | Khi đang xem `ONE Business Credo`, nhãn lesson phía trên nội dung lại hiển thị `Lesson 1 - Course Introduction`. | Learner có thể bị lệch định hướng vì nhãn lesson không khớp với lesson đang hiển thị trên màn hình. | Cập nhật nhãn lesson để khớp với `ONE Business Credo`. |
| ID-002 | **Minor** | Tính nhất quán nhãn section | Khi đang xem `Code of Conduct Introduction`, nhãn lesson phía trên nội dung lại hiển thị `Lesson 2 - ONE Business Credo`. | Điều này tạo ra cùng một vấn đề định hướng ở đầu Chapter 2 và làm giảm độ rõ ràng của điều hướng. | Cập nhật nhãn lesson để khớp với `Code of Conduct Introduction`. |
| ID-003 | **Minor** | Ngữ pháp | Trong knowledge check của `ONE Business Credo`, câu hỏi và feedback dùng `As an ONE employee...` và `As an ONE employee, you must comply...`. | Lỗi mạo từ này lặp lại trong nội dung assessment, làm giảm chất lượng biên tập. | Đổi cả hai chỗ thành `As a ONE employee...`. |
| ID-004 | **Minor** | Ngữ pháp | Trong `Code of Conduct Introduction`, Learning Objective 2 ghi `Apply the principles of our Business Credo to behaviour and conduct in workplace`. | Việc thiếu mạo từ làm câu objective đọc chưa tự nhiên trong một khối nội dung hướng dẫn nổi bật. | Sửa thành `...to behaviour and conduct in the workplace`. |

## Những gì đã được xác minh

- Đã mở public Review 360 item và chụp lại trạng thái review shell.
- Đã bóc và mở direct Rise asset phía sau review item.
- `Course Introduction`:
  - Đã rà nội dung lesson và phần instructions đang hiển thị.
  - Đã xác minh nút `I'm ready to explore the ONE Business Credo` điều hướng đúng sang lesson `ONE Business Credo`.
- `ONE Business Credo`:
  - Đã rà nội dung đầu lesson và xác minh hành động `CONTINUE` bên trong lesson.
  - Đã click đủ 5 tab principle:
    - `1. Act as ONE`
    - `2. Safeguard Our Environment, Safety, and Quality`
    - `3. Observe Ethical Conduct and Compliance With Laws and Regulations`
    - `4. Nurture an Inclusive Workplace and Respect for Human Rights`
    - `5. Enhance Information Security and Protection of Assets`
  - Đã xác minh nhánh đúng của Knowledge Check Q1 bằng cách chọn đủ 5 principle hợp lệ.
  - Đã xác minh nhánh sai của Knowledge Check Q2 với đáp án `Yes`.
  - Đã xác minh nhánh đúng của Knowledge Check Q2 với đáp án `No`.
- `Code of Conduct Introduction`:
  - Đã rà nội dung lesson và các learning objectives đang hiển thị.
  - Đã xác minh nút `Go to Section 1 of the Code` điều hướng đúng sang mục `1. Act as ONE`.

## Ghi chú

- Không ghi nhận lỗi điều hướng mang tính chặn ở ba lesson đã test.
- Evidence hỗ trợ cho lần chạy này nằm trong thư mục `artifacts/` cùng bundle, bao gồm review-shell probe, section probe, và full-page screenshots.
