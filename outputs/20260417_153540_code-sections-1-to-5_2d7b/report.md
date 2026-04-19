# QA Report: Code Sections 1 to 5

**Source URL**: `https://360.articulate.com/review/content/2d7bbaed-07ca-41ce-822c-8b51ff989ab9/review`  
**Execution mode**: Playwright browser pass via direct Rise asset URL resolved from the public Review 360 item on April 17, 2026  
**Sections tested**: `1. Act as ONE`, `2. Safeguard our Environment, Safety and Quality`, `3. Observe Ethical Conduct and Compliance with Laws and Regulations`, `4. Nurture an Inclusive Workplace and Respect for Human Rights`, `5. Enhance Information Security And Protection Of Assets`  

## Summary
This pass covered Chapter 2 sections `1` through `5` of the Code of Conduct. The live Rise asset behind the public Review 360 item was tested directly, with visible tabs, accordions, flip-cards, markers, scenario steps, and knowledge-check states reviewed across the requested scope.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Capitalisation Consistency | In section `1. Act as ONE`, the left navigation shows `1. Act as ONE`, while the in-page heading reads `1. Act As ONE`. | Inconsistent title casing weakens editorial consistency inside the same lesson. | Standardise the section title so the navigation label and in-page heading use the same casing. |
| ID-002 | **Minor** | Section Label Consistency | While viewing section `1. Act as ONE`, the lesson label above the page content reads `Lesson 3 - ONE Code of Conduct Introduction`. | Learners can lose orientation because the lesson label does not match the section currently on screen. | Update the lesson label so it matches section 1 and its correct numbering/title. |
| ID-003 | **Major** | Knowledge Check Logic | In section `2. Safeguard our Environment, Safety and Quality`, Q.1 already shows `Correct` on load while the draggable/selectable items and `SUBMIT` button are still visible. | Learners can receive success feedback before completing the interaction, which undermines assessment validity and can mask progress/scoring defects. | Reset the interaction state so the activity loads unanswered, shows no success feedback before a real attempt, and only marks `Correct` after valid learner input. |
| ID-004 | **Minor** | Section Label Consistency | While viewing section `2. Safeguard our Environment, Safety and Quality`, the lesson label above the page content reads `Lesson 4 - 1. Act as ONE`. | This creates numbering/title confusion and weakens learner orientation in the section sequence. | Update the lesson label so it matches section 2 and its correct numbering/title. |
| ID-005 | **Suggestion** | Content Presentation | In the `IMPROVEMENT OF SERVICE QUALITY` tab, the environment-focused sentence `We protect the environment and ecosystems by taking action on climate change, preventing marine pollution and using resources responsibly.` still appears below the service-quality copy. | If unintended, this blurs the distinction between tab topics and reduces content clarity. | Confirm whether that environment paragraph is meant to persist across tabs; if not, restrict each tab to its own topic-specific copy. |
| ID-006 | **Major** | Knowledge Check Logic | In section `3. Observe Ethical Conduct and Compliance with Laws and Regulations`, both Q.1 and Q.2 already display `Incorrect` and `TAKE AGAIN` on load before any learner answer is selected or submitted. | Premature failure feedback breaks learner trust and suggests the quiz state is not being initialised correctly. | Ensure both questions load unanswered, with no correctness feedback shown until the learner submits a real response. |
| ID-007 | **Minor** | Section Label Consistency | While viewing section `3. Observe Ethical Conduct and Compliance with Laws and Regulations`, the lesson label above the page content reads `Lesson 5 - 2. Safeguard our Environment, Safety and Quality`. | Learners can be unsure whether they are viewing section 2 or section 3, reducing navigation clarity. | Update the lesson label so it matches section 3 and its correct numbering/title. |
| ID-008 | **Suggestion** | Interaction Presentation | In the conflict-of-interest process inside section 3, `1 of 4`, `2 of 4`, `3 of 4`, and `4 of 4` content appear together in the same view after `START`, instead of feeling step-based. | If unintended, this weakens the instructional purpose of the stepper and can overwhelm the learner with all steps at once. | Confirm whether all steps are meant to be visible simultaneously; if not, render only the active step until the learner advances. |
| ID-009 | **Major** | Knowledge Check Logic | In section `4. Nurture an Inclusive Workplace and Respect for Human Rights`, Q.1 and Q.2 already show `Incorrect` and `TAKE AGAIN` immediately on load before any learner response is selected. | Premature failure feedback reduces learner trust and suggests the quiz state is not being initialised correctly. | Ensure each question starts blank and only shows correctness feedback after a real learner submission. |
| ID-010 | **Minor** | Section Label Consistency | While viewing section `4. Nurture an Inclusive Workplace and Respect for Human Rights`, the lesson label above the page content reads `Lesson 6 - 3. Observe Ethical Conduct and Compliance with Laws and Regulations`. | This creates numbering/title confusion and weakens orientation within the lesson sequence. | Update the lesson label so it reflects the actual section being viewed. |
| ID-011 | **Minor** | Grammar/Spelling | Section 4 contains the sentence `Our team connect with the students in Vietnam to donate and support for future generations`. | The incorrect verb agreement and awkward phrasing reduce professionalism and readability in a high-visibility section. | Rewrite it to something like `Our team connects with students in Vietnam to donate and support future generations.` |
| ID-012 | **Major** | Knowledge Check Logic | In section `5. Enhance Information Security And Protection Of Assets`, Q.1 and Q.2 already display `Incorrect` and `TAKE AGAIN` on load before any learner answer is selected or submitted. | Learners are shown failure feedback without interaction, which undermines assessment credibility and can hide scoring/progress defects. | Reset the assessment state so each question loads unanswered, with no failure feedback shown until the learner submits a real response. |
| ID-013 | **Minor** | Section Label Consistency | While viewing section `5. Enhance Information Security And Protection Of Assets`, the lesson label above the page content reads `Lesson 7 - 4. Nurture an Inclusive Workplace and Respect for Human Rights`. | This weakens orientation and can make learners think they are still in section 4. | Update the lesson label so it matches section 5 and its correct numbering/title. |

## What Was Verified

- Opened the public Review 360 item and captured the review-shell state.
- Resolved and tested the current live Rise asset served by the review item.
- `1. Act as ONE`:
- Opened both role reveals: `Top Management` and `ONE Employees`.
- Traversed both scenario questions and verified the correct `No` path through to `Scenario Complete!` and `Go to Section 2 of the Code`.
- `2. Safeguard our Environment, Safety and Quality`:
- Reviewed the visible landing copy and clicked all three commitment tabs: `PURSUIT OF SAFETY`, `SAFEGUARDING OUR ENVIRONMENT`, and `IMPROVEMENT OF SERVICE QUALITY`.
- Inspected the initial state of the matching interaction and its feedback state.
- `3. Observe Ethical Conduct and Compliance with Laws and Regulations`:
- Reviewed the visible section content, opened both bribery accordions, and triggered the conflict-of-interest `START` flow.
- Surfaced visible flip-card content and inspected both visible knowledge-check questions and answer options.
- `4. Nurture an Inclusive Workplace and Respect for Human Rights`:
- Reviewed the visible section content, clicked both diversity tabs, opened visible flip-cards, and opened the visible marker interactions.
- Inspected both visible knowledge-check questions and their initial states.
- `5. Enhance Information Security And Protection Of Assets`:
- Reviewed the visible section content, opened visible asset-protection flip-cards, checked the three data-privacy tabs, and opened the visible marker interactions.
- Inspected both visible knowledge-check questions and their initial states.

## Notes

- The current live course differs from some older reports in this repository. This report reflects only what was directly observed in the live browser pass on April 17, 2026.
- Evidence for this pass is stored in the sibling `artifacts/` folder, including the review-shell probe, section probe, and full-page screenshots for sections 1 to 5.

## Bản Dịch Tiếng Việt

**Nguồn URL**: `https://360.articulate.com/review/content/2d7bbaed-07ca-41ce-822c-8b51ff989ab9/review`  
**Chế độ chạy**: kiểm tra bằng Playwright trên direct Rise asset URL được bóc ra từ public Review 360 item vào ngày 17/04/2026  
**Các mục đã kiểm tra**: `1. Act as ONE`, `2. Safeguard our Environment, Safety and Quality`, `3. Observe Ethical Conduct and Compliance with Laws and Regulations`, `4. Nurture an Inclusive Workplace and Respect for Human Rights`, `5. Enhance Information Security And Protection Of Assets`  

## Tóm tắt
Lần chạy này bao phủ các section `1` đến `5` của Chapter 2 trong Code of Conduct. Phần Rise asset live nằm phía sau public Review 360 item đã được test trực tiếp, bao gồm việc rà soát các tab, accordion, flip-card, marker, bước scenario, và trạng thái knowledge check trong toàn bộ phạm vi được yêu cầu.

## Findings

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Minor** | Tính nhất quán viết hoa | Ở section `1. Act as ONE`, điều hướng bên trái hiển thị `1. Act as ONE`, trong khi tiêu đề trong trang hiển thị `1. Act As ONE`. | Việc viết hoa không nhất quán làm giảm tính đồng bộ biên tập trong cùng một lesson. | Chuẩn hóa tiêu đề section để nhãn điều hướng và tiêu đề trong trang dùng cùng một kiểu viết hoa. |
| ID-002 | **Minor** | Tính nhất quán nhãn section | Khi xem section `1. Act as ONE`, nhãn lesson phía trên nội dung hiển thị `Lesson 3 - ONE Code of Conduct Introduction`. | Learner có thể bị lệch định hướng vì nhãn lesson không khớp với section đang hiển thị. | Cập nhật nhãn lesson để khớp với section 1 cùng số thứ tự và tiêu đề chính xác. |
| ID-003 | **Major** | Logic Knowledge Check | Ở section `2. Safeguard our Environment, Safety and Quality`, Q.1 đã hiển thị `Correct` ngay khi tải lên, trong khi các item có thể chọn/kéo thả và nút `SUBMIT` vẫn còn hiển thị. | Learner có thể nhận phản hồi thành công trước khi hoàn thành tương tác, làm giảm tính hợp lệ của assessment và có thể che giấu lỗi progress/scoring. | Reset trạng thái tương tác để activity tải lên ở trạng thái chưa trả lời, không hiển thị phản hồi thành công trước một lần làm bài thật, và chỉ đánh dấu `Correct` sau input hợp lệ của learner. |
| ID-004 | **Minor** | Tính nhất quán nhãn section | Khi xem section `2. Safeguard our Environment, Safety and Quality`, nhãn lesson phía trên nội dung hiển thị `Lesson 4 - 1. Act as ONE`. | Điều này gây nhầm lẫn về số thứ tự/tiêu đề và làm giảm khả năng định hướng của learner. | Cập nhật nhãn lesson để khớp với section 2 cùng số thứ tự và tiêu đề chính xác. |
| ID-005 | **Suggestion** | Trình bày nội dung | Trong tab `IMPROVEMENT OF SERVICE QUALITY`, câu về môi trường `We protect the environment and ecosystems by taking action on climate change, preventing marine pollution and using resources responsibly.` vẫn xuất hiện bên dưới phần copy riêng của tab service-quality. | Nếu đây không phải chủ đích thiết kế, nó làm mờ ranh giới giữa các chủ đề tab và giảm độ rõ ràng của nội dung. | Xác nhận đoạn về môi trường có được chủ đích giữ lại trên mọi tab hay không; nếu không, giới hạn mỗi tab chỉ hiển thị nội dung đúng chủ đề của tab đó. |
| ID-006 | **Major** | Logic Knowledge Check | Ở section `3. Observe Ethical Conduct and Compliance with Laws and Regulations`, cả Q.1 và Q.2 đều đã hiển thị `Incorrect` và `TAKE AGAIN` ngay khi tải lên, trước khi learner chọn hoặc submit đáp án. | Phản hồi thất bại xuất hiện quá sớm làm giảm niềm tin của learner và cho thấy trạng thái quiz có thể chưa được khởi tạo đúng. | Bảo đảm cả hai câu hỏi tải lên ở trạng thái chưa trả lời và không hiển thị feedback đúng/sai cho tới khi learner submit thật. |
| ID-007 | **Minor** | Tính nhất quán nhãn section | Khi xem section `3. Observe Ethical Conduct and Compliance with Laws and Regulations`, nhãn lesson phía trên nội dung hiển thị `Lesson 5 - 2. Safeguard our Environment, Safety and Quality`. | Learner có thể không chắc mình đang ở section 2 hay section 3, làm giảm độ rõ ràng khi điều hướng. | Cập nhật nhãn lesson để khớp với section 3 cùng số thứ tự và tiêu đề chính xác. |
| ID-008 | **Suggestion** | Trình bày tương tác | Trong luồng conflict-of-interest của section 3, nội dung `1 of 4`, `2 of 4`, `3 of 4`, và `4 of 4` xuất hiện cùng lúc trong cùng một view sau khi bấm `START`, thay vì mang cảm giác step-by-step. | Nếu đây không phải chủ đích thiết kế, nó làm yếu mục tiêu hướng dẫn theo từng bước và có thể khiến learner bị quá tải thông tin. | Xác nhận xem tất cả các bước có phải được hiển thị đồng thời hay không; nếu không, chỉ render bước đang active cho tới khi learner chuyển bước. |
| ID-009 | **Major** | Logic Knowledge Check | Ở section `4. Nurture an Inclusive Workplace and Respect for Human Rights`, Q.1 và Q.2 đã hiển thị `Incorrect` và `TAKE AGAIN` ngay khi tải lên trước khi learner chọn đáp án. | Phản hồi thất bại xuất hiện quá sớm làm giảm niềm tin của learner và cho thấy trạng thái quiz có thể chưa được khởi tạo đúng. | Bảo đảm mỗi câu hỏi bắt đầu ở trạng thái trống và chỉ hiển thị feedback đúng/sai sau một lần submit thật của learner. |
| ID-010 | **Minor** | Tính nhất quán nhãn section | Khi xem section `4. Nurture an Inclusive Workplace and Respect for Human Rights`, nhãn lesson phía trên nội dung hiển thị `Lesson 6 - 3. Observe Ethical Conduct and Compliance with Laws and Regulations`. | Điều này gây nhầm lẫn về số thứ tự/tiêu đề và làm giảm khả năng định vị của learner trong chuỗi lesson. | Cập nhật nhãn lesson để phản ánh đúng section đang được xem. |
| ID-011 | **Minor** | Ngữ pháp/Chính tả | Section 4 có câu `Our team connect with the students in Vietnam to donate and support for future generations`. | Lỗi hòa hợp động từ và cách diễn đạt gượng làm giảm tính chuyên nghiệp và độ mượt khi đọc trong một phần nội dung có độ hiển thị cao. | Viết lại theo hướng như `Our team connects with students in Vietnam to donate and support future generations.` |
| ID-012 | **Major** | Logic Knowledge Check | Ở section `5. Enhance Information Security And Protection Of Assets`, Q.1 và Q.2 đều đã hiển thị `Incorrect` và `TAKE AGAIN` ngay khi tải lên trước khi learner chọn hoặc submit đáp án. | Learner bị hiển thị phản hồi thất bại mà chưa tương tác, làm giảm độ tin cậy của assessment và có thể che giấu lỗi scoring/progress. | Reset trạng thái assessment để mỗi câu hỏi tải lên ở trạng thái chưa trả lời và không hiển thị phản hồi thất bại cho tới khi learner submit thật. |
| ID-013 | **Minor** | Tính nhất quán nhãn section | Khi xem section `5. Enhance Information Security And Protection Of Assets`, nhãn lesson phía trên nội dung hiển thị `Lesson 7 - 4. Nurture an Inclusive Workplace and Respect for Human Rights`. | Điều này làm giảm khả năng định hướng và có thể khiến learner nghĩ rằng họ vẫn đang ở section 4. | Cập nhật nhãn lesson để khớp với section 5 cùng số thứ tự và tiêu đề chính xác. |

## Những gì đã được xác minh

- Đã mở public Review 360 item và chụp lại trạng thái review shell.
- Đã bóc và test Rise asset live hiện tại được phục vụ bởi review item.
- `1. Act as ONE`:
- Đã mở đủ hai phần reveal `Top Management` và `ONE Employees`.
- Đã đi qua cả hai câu hỏi scenario và xác minh nhánh đúng `No` đến `Scenario Complete!` và `Go to Section 2 of the Code`.
- `2. Safeguard our Environment, Safety and Quality`:
- Đã rà nội dung hiển thị và click đủ ba tab `PURSUIT OF SAFETY`, `SAFEGUARDING OUR ENVIRONMENT`, và `IMPROVEMENT OF SERVICE QUALITY`.
- Đã kiểm tra trạng thái ban đầu của matching interaction và feedback đi kèm.
- `3. Observe Ethical Conduct and Compliance with Laws and Regulations`:
- Đã rà nội dung hiển thị, mở cả hai accordion về bribery, và kích hoạt luồng `START` của conflict-of-interest.
- Đã làm lộ phần flip-card đang hiển thị và kiểm tra cả hai câu hỏi knowledge check cùng các đáp án nhìn thấy.
- `4. Nurture an Inclusive Workplace and Respect for Human Rights`:
- Đã rà nội dung hiển thị, click cả hai tab diversity, mở các flip-card đang hiển thị, và mở các marker interaction đang thấy.
- Đã kiểm tra cả hai câu hỏi knowledge check cùng trạng thái ban đầu của chúng.
- `5. Enhance Information Security And Protection Of Assets`:
- Đã rà nội dung hiển thị, mở các flip-card về asset protection đang thấy, kiểm tra ba tab data privacy, và mở các marker interaction đang thấy.
- Đã kiểm tra cả hai câu hỏi knowledge check cùng trạng thái ban đầu của chúng.

## Ghi chú

- Live course hiện tại đã khác với một số report cũ có sẵn trong repo. Report này chỉ phản ánh những gì được quan sát trực tiếp trong lần chạy browser live ngày 17/04/2026.
- Evidence của lần chạy này nằm trong thư mục `artifacts/` cùng bundle, gồm review-shell probe, section probe, và các ảnh chụp full-page cho section 1 đến 5.
