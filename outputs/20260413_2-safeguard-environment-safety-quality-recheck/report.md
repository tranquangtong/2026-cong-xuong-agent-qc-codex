# QA Report: 2. Safeguard our Environment, Safety and Quality

**Source URL**: `https://360.articulate.com/review/content/7b72d754-b16e-4d51-9083-1ae84d185ad9/review`  
**Execution mode**: Playwright browser pass via direct Rise asset URL resolved from the review item  
**Section tested**: `2. Safeguard our Environment, Safety and Quality`  

## Summary
This pass focused on section `2. Safeguard our Environment, Safety and Quality`, including all visible tabs and the Knowledge Check area. The public Review 360 link currently exposes only an `Item not found | Review 360` shell for signed-out access, so the actual QC pass was executed against the direct Rise asset behind that review item.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Major** | Knowledge Check Logic | The matching Knowledge Check already shows `Correct` before any drag-and-drop interaction or submission is performed. The initial section state includes the quiz plus a visible `Correct` label above `Go to Section 3 of the Code`. | Learners can receive pre-resolved feedback without completing the activity, which invalidates assessment logic and undermines trust in the check. | Reset the matching interaction so no correctness feedback appears until the learner has completed the drag-and-drop and explicitly submitted the answer. |
| ID-002 | **Minor** | Section Label Consistency | The page shows `Lesson 4 - 1. Act as ONE` directly above the section heading `2. Safeguard our Environment, Safety and Quality`. | This weakens orientation and can make learners think they are still in section 1. | Update the lesson label so it matches section 2 and its correct numbering/title. |
| ID-003 | **Major** | Content Mapping / Tab Consistency | Content from the environment theme remains visible under other tabs. In the `PURSUIT OF SAFETY` state, the environment sentence `We protect the environment and ecosystems by taking action on climate change, preventing marine pollution and using resources responsibly.` is still shown. In the `IMPROVEMENT OF SERVICE QUALITY` state, that same environment sentence also remains visible below the service-quality copy. | Learners may receive mixed or misleading tab content, which weakens comprehension and makes the section feel unreliable. | Review the tab-content mapping so each tab displays only its own intended copy and no carry-over text from another commitment area remains visible. |

## What Was Verified

- Opened the public Review 360 link and confirmed the current shell only exposes a signed-out `Item not found` wrapper.
- Opened the direct Rise asset URL associated with the review item.
- Navigated specifically to section `2. Safeguard our Environment, Safety and Quality`.
- Verified all visible tab states in the section:
  - `PURSUIT OF SAFETY`
  - `SAFEGUARDING OUR ENVIRONMENT`
  - `IMPROVEMENT OF SERVICE QUALITY`
- Captured full-page screenshots for the section and tab states that were exercised.
- Reached the Knowledge Check area and confirmed it is a matching/drag-and-drop activity.
- Verified that the quiz state is already showing `Correct` before learner interaction.

## Notes

- Because the matching interaction is already in an invalid pre-resolved state, this pass could not meaningfully verify a clean wrong-path versus right-path learner journey for the Knowledge Check.
- The artifacts bundle includes the public-shell probe, the section probe with tab states, and screenshots for the exercised states.

## Bản Dịch Tiếng Việt

**Nguồn URL**: `https://360.articulate.com/review/content/7b72d754-b16e-4d51-9083-1ae84d185ad9/review`  
**Chế độ chạy**: kiểm tra bằng Playwright trên direct Rise asset URL được bóc ra từ review item  
**Mục đã kiểm tra**: `2. Safeguard our Environment, Safety and Quality`  

## Tóm tắt
Lần kiểm tra này tập trung vào mục `2. Safeguard our Environment, Safety and Quality`, bao gồm toàn bộ các tab đang hiển thị và khu vực Knowledge Check. Link public Review 360 hiện chỉ hiển thị lớp shell `Item not found | Review 360` đối với trạng thái chưa đăng nhập, nên phần QC thực tế được thực hiện trên direct Rise asset phía sau review item đó.

## Findings

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Major** | Logic Knowledge Check | Knowledge Check dạng matching đã hiển thị `Correct` ngay cả trước khi learner thực hiện thao tác kéo-thả hoặc submit. Ở trạng thái đầu của section, quiz đã đi kèm nhãn `Correct` nằm ngay trên `Go to Section 3 of the Code`. | Learner có thể nhận feedback như thể đã làm đúng dù chưa hoàn thành hoạt động, làm sai logic đánh giá và giảm độ tin cậy của bài kiểm tra. | Reset matching interaction để không có feedback đúng/sai nào xuất hiện cho tới khi learner hoàn thành kéo-thả và bấm submit rõ ràng. |
| ID-002 | **Minor** | Tính nhất quán nhãn section | Trang hiển thị `Lesson 4 - 1. Act as ONE` ngay phía trên tiêu đề `2. Safeguard our Environment, Safety and Quality`. | Điều này làm giảm khả năng định hướng và có thể khiến learner nghĩ rằng họ vẫn đang ở section 1. | Cập nhật nhãn lesson để khớp với section 2 cùng số thứ tự và tiêu đề chính xác. |
| ID-003 | **Major** | Mapping nội dung / Tính nhất quán giữa các tab | Nội dung thuộc chủ đề môi trường vẫn xuất hiện dưới các tab khác. Ở trạng thái `PURSUIT OF SAFETY`, câu `We protect the environment and ecosystems by taking action on climate change, preventing marine pollution and using resources responsibly.` vẫn còn hiển thị. Ở trạng thái `IMPROVEMENT OF SERVICE QUALITY`, chính câu môi trường đó cũng vẫn nằm dưới phần copy về service quality. | Learner có thể nhận nội dung lẫn hoặc sai ngữ cảnh giữa các tab, làm giảm khả năng hiểu và khiến section kém đáng tin cậy. | Rà soát mapping nội dung của từng tab để mỗi tab chỉ hiển thị đúng copy của nó, không còn text sót lại từ commitment area khác. |

## Những gì đã được xác minh

- Đã mở public Review 360 link và xác nhận lớp shell hiện tại chỉ hiển thị wrapper `Item not found` ở trạng thái chưa đăng nhập.
- Đã mở direct Rise asset URL gắn với review item đó.
- Đã điều hướng đúng tới mục `2. Safeguard our Environment, Safety and Quality`.
- Đã xác minh toàn bộ các trạng thái tab đang hiển thị trong section:
  - `PURSUIT OF SAFETY`
  - `SAFEGUARDING OUR ENVIRONMENT`
  - `IMPROVEMENT OF SERVICE QUALITY`
- Đã chụp full-page screenshot cho section và các trạng thái tab đã đi qua.
- Đã đi tới khu vực Knowledge Check và xác nhận đây là activity dạng matching/kéo-thả.
- Đã xác nhận quiz đang hiển thị `Correct` ngay cả trước khi learner tương tác.

## Ghi chú

- Vì matching interaction đã ở trạng thái lỗi, tức đã bị “giải sẵn”, nên lần pass này không thể xác minh một hành trình wrong-path và right-path sạch cho Knowledge Check.
- Bundle artifacts đã bao gồm public-shell probe, section probe với các trạng thái tab, và screenshot cho các trạng thái đã được kiểm tra.
