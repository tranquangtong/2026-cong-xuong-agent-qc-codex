# QA Report: 4. Nurture an Inclusive Workplace and Respect for Human Rights
**Course**: [Legal & GA] ONE Business Credo & Code of Conduct  
**Section tested**: `4. Nurture an Inclusive Workplace and Respect for Human Rights`  
**Test date**: 2026-04-12  
**Method**: Headless Playwright verification with tab checks and on-screen content inspection.

## Summary
The section content is readable and the two diversity tabs are clickable, but the Knowledge Check again loads with incorrect feedback before learner interaction. There is also a lesson-label mismatch and a visible grammar issue in the section body.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| ID-001 | **Major** | Knowledge Check Logic | Q.1 and Q.2 already show `Incorrect` and `TAKE AGAIN` immediately on load before any learner response is selected. | Premature failure feedback breaks learner trust and suggests the quiz state is not being initialized correctly. | Ensure each question starts blank and only shows correctness feedback after a real learner submission. |
| ID-002 | **Minor** | Section Label Consistency | The page shows `Lesson 6 - 3. Observe Ethical Conduct and Compliance with Laws and Regulations` above the heading `4. Nurture an Inclusive Workplace and Respect for Human Rights`. | This creates numbering/title confusion and weakens orientation within the lesson sequence. | Update the lesson label so it reflects the actual section being viewed. |
| ID-003 | **Minor** | Grammar/Spelling | The sentence `Our team connect with the students in Vietnam to donate and support for future generations` contains incorrect verb agreement and awkward phrasing. | The wording reduces professionalism and readability in a high-visibility social contribution section. | Rewrite to something like `Our team connects with students in Vietnam to donate and support future generations.` |
| ID-004 | **Suggestion** | Content Relevance / Proof Point | The line `ONE has been recognized as one of the Straits Times Singapore's Best Employers` appears as a standalone proof point without date, context, or source framing. | Without supporting context, the claim can feel disconnected from the surrounding instructional content. | Consider adding a year/source context or integrating the statement more clearly into the narrative. |

## What Was Verified
- Opened the public review item and navigated directly to section 4.
- Clicked both visible tabs:
  - `WE BUILD THE HOUSE`
  - `OUR PEOPLE MAKE IT HOME`
- Reviewed the visible content for diversity, harassment, neutrality, human rights, and forced labour sections.
- Inspected both visible Knowledge Check questions and answer states.

## Notes
- I did not fully traverse every flip-card or numbered harassment interaction in this pass; the report focuses on the highest-signal visible defects and the recurring assessment-state problem.
- Supporting screenshots for this run are stored in the sibling `artifacts/` folder.

## Bản Dịch Tiếng Việt
**Khóa học**: [Legal & GA] ONE Business Credo & Code of Conduct  
**Mục đã kiểm tra**: `4. Nurture an Inclusive Workplace and Respect for Human Rights`  
**Ngày kiểm tra**: 2026-04-12  
**Phương pháp**: Xác minh bằng Playwright headless, có kiểm tra các tab và nội dung hiển thị trên màn hình.

### Tóm tắt
Nội dung của section này đọc được và hai tab diversity đều bấm được, nhưng Knowledge Check lại tiếp tục tải lên với phản hồi sai trước khi learner có tương tác. Ngoài ra còn có nhãn lesson bị lệch và một lỗi grammar nhìn thấy trong phần nội dung thân bài.

### Các lỗi/phát hiện

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| ID-001 | **Major** | Logic Knowledge Check | Q.1 và Q.2 đều đã hiển thị `Incorrect` và `TAKE AGAIN` ngay khi tải lên trước khi learner chọn đáp án. | Việc hiện phản hồi thất bại quá sớm làm giảm niềm tin của learner và cho thấy trạng thái quiz có thể chưa được khởi tạo đúng. | Bảo đảm mỗi câu hỏi bắt đầu ở trạng thái trống và chỉ hiển thị feedback đúng/sai sau một lần submit thật của learner. |
| ID-002 | **Minor** | Tính nhất quán nhãn section | Trang hiển thị `Lesson 6 - 3. Observe Ethical Conduct and Compliance with Laws and Regulations` phía trên heading `4. Nurture an Inclusive Workplace and Respect for Human Rights`. | Điều này gây nhầm lẫn về số thứ tự/tiêu đề và làm giảm khả năng định vị của learner trong chuỗi bài học. | Cập nhật nhãn lesson để phản ánh đúng section đang được xem. |
| ID-003 | **Minor** | Ngữ pháp/Chính tả | Câu `Our team connect with the students in Vietnam to donate and support for future generations` chứa lỗi hòa hợp động từ và cách diễn đạt gượng. | Câu chữ này làm giảm tính chuyên nghiệp và độ mượt khi đọc trong một phần nội dung có độ hiển thị cao. | Viết lại theo hướng như `Our team connects with students in Vietnam to donate and support future generations.` |
| ID-004 | **Suggestion** | Mức độ liên quan của nội dung / proof point | Dòng `ONE has been recognized as one of the Straits Times Singapore's Best Employers` xuất hiện như một proof point đứng riêng, không có mốc thời gian, ngữ cảnh hoặc nguồn tham chiếu. | Nếu thiếu ngữ cảnh hỗ trợ, claim này có thể tạo cảm giác rời rạc so với mạch nội dung đang trình bày. | Cân nhắc thêm năm/nguồn hoặc tích hợp câu này rõ ràng hơn vào phần narrative. |

### Nội dung đã xác minh
- Đã mở review item public và điều hướng trực tiếp tới section 4.
- Đã click cả hai tab hiển thị:
  - `WE BUILD THE HOUSE`
  - `OUR PEOPLE MAKE IT HOME`
- Đã rà soát nội dung hiển thị về diversity, harassment, neutrality, human rights, và forced labour.
- Đã kiểm tra trạng thái hiển thị của cả hai câu hỏi trong Knowledge Check.

### Ghi chú
- Mình chưa đi hết từng flip-card hoặc từng interactive đánh số trong phần harassment ở pass này; report tập trung vào các defect tín hiệu mạnh nhất đang nhìn thấy và lỗi lặp lại về trạng thái assessment.
- Các ảnh chụp hỗ trợ cho lần chạy này được lưu trong thư mục `artifacts/` cùng cấp.
