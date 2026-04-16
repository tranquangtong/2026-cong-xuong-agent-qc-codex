# Graphic QA Report
**Source**: Figma  
**File**: `-SAP-LEGAL`  
**Node**: `54:10`  
**Frame name**: `The Weekend 'Consultant' (Secondary Employment)`  
**Link**: https://www.figma.com/design/0jLgNwcxatnvLllVlOnOeN/-SAP-LEGAL?node-id=54-10&t=pRuzlF0La8iWfEno-1

## Summary
The illustration is visually polished and the day/night split communicates the “double life” idea well. The main risks are accessibility and instructional clarity at smaller sizes: some text is too small/light, several decorative details may not survive scaling, and the story relies heavily on implication rather than one or two clearer conflict-of-interest cues.

## Findings

| ID | Severity | Area | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| FG-001 | **Major** | WCAG / Text Legibility | The `10:00 AM` and `10:00 PM` labels are small, thin, and low-emphasis against very light backgrounds. | On smaller screens or inside e-learning cards, these labels may become hard to read and weaken the day/night narrative. | Increase text size and weight, and strengthen contrast so the time labels remain readable at reduced display sizes. |
| FG-002 | **Minor** | Visual Hierarchy | The right-hand scene contains many competing decorative elements at once: code badge, task cards, gears, map card, cat, gem shape, and laptop. | The viewer’s eye can scatter across the composition instead of focusing first on the character’s “secondary employment” context. | Reduce or soften one to two secondary decorative elements on the right side so the key story beats stand out faster. |
| FG-003 | **Minor** | Story Clarity | The left side clearly suggests office work and money pressure, but the right side’s “secondary job” meaning depends on interpretation of coding/UI symbols. | Some learners may understand “busy at night” but miss the compliance-specific idea of outside paid work or conflict of interest. | Add one clearer visual cue tied to freelance/side work, such as a contract, invoice, client brief, or explicit second-work marker. |
| FG-004 | **Suggestion** | Small-Scale Robustness | Fine details such as the mini dashboard cards, map markers, gears, and chart lines are dense and delicate. | If this frame is used in a smaller e-learning viewport, many details may blur into noise rather than support comprehension. | Prepare a simplified small-screen variant or reduce detail density in secondary UI ornaments. |

## What Was Checked
- Overall composition and balance
- Day/night narrative clarity
- Visual hierarchy and focal points
- Readability of text-like elements
- WCAG-oriented visual accessibility risks
- Suitability for scaled e-learning use

## Notes
- This pass focused on graphic QA only, not storyboard or copy QA.
- WCAG 2.2 was used as the accessibility baseline for visual legibility judgments.

## Bản Dịch Tiếng Việt
**Nguồn**: Figma  
**File**: `-SAP-LEGAL`  
**Node**: `54:10`  
**Tên frame**: `The Weekend 'Consultant' (Secondary Employment)`  
**Link**: https://www.figma.com/design/0jLgNwcxatnvLllVlOnOeN/-SAP-LEGAL?node-id=54-10&t=pRuzlF0La8iWfEno-1

### Tóm tắt
Minh họa này có chất lượng hình ảnh tốt và cách chia ngày/đêm truyền tải khá rõ ý tưởng về “cuộc sống hai mặt”. Rủi ro chính nằm ở khả năng tiếp cận và độ rõ ràng của thông điệp khi hiển thị ở kích thước nhỏ: một số phần text còn quá nhỏ/nhẹ, nhiều chi tiết trang trí có thể bị mất khi scale xuống, và câu chuyện hiện vẫn dựa khá nhiều vào sự suy diễn thay vì có thêm một hoặc hai tín hiệu rõ hơn về xung đột lợi ích.

### Các lỗi/phát hiện

| ID | Mức độ | Khu vực | Bằng chứng | Ảnh hưởng | Đề xuất sửa |
|---|---|---|---|---|---|
| FG-001 | **Major** | WCAG / Độ dễ đọc của text | Các nhãn `10:00 AM` và `10:00 PM` nhỏ, nét mảnh và không nổi bật nhiều trên nền rất sáng. | Trên màn hình nhỏ hoặc khi đặt trong card e-learning, các nhãn này có thể khó đọc và làm yếu đi ý nghĩa ngày/đêm của hình. | Tăng kích thước và độ đậm của chữ, đồng thời tăng contrast để các nhãn thời gian vẫn đọc được khi hiển thị ở kích thước nhỏ hơn. |
| FG-002 | **Minor** | Thứ bậc thị giác | Cảnh phía bên phải có nhiều chi tiết trang trí cạnh tranh nhau cùng lúc: badge code, các task card, bánh răng, bản đồ, con mèo, khối hình hồng, và laptop. | Ánh nhìn của người xem có thể bị phân tán, thay vì tập trung ngay vào bối cảnh “secondary employment” của nhân vật. | Giảm bớt hoặc làm nhẹ một đến hai chi tiết trang trí phụ ở bên phải để các điểm kể chuyện chính nổi bật hơn. |
| FG-003 | **Minor** | Độ rõ của câu chuyện | Bên trái gợi ý khá rõ về công việc văn phòng và áp lực tài chính, nhưng bên phải lại cần người xem tự suy ra ý “công việc thứ hai” qua các biểu tượng code/UI. | Một số learner có thể chỉ hiểu là “ban đêm đang bận làm việc” chứ chưa chắc hiểu rõ đây là tình huống ngoài giờ có thể liên quan đến conflict of interest. | Thêm một tín hiệu trực quan rõ hơn về freelance/side job như contract, invoice, client brief, hoặc một dấu hiệu cụ thể hơn về việc làm thêm. |
| FG-004 | **Suggestion** | Độ bền khi thu nhỏ | Các chi tiết nhỏ như mini dashboard cards, map marker, bánh răng và chart line khá dày và mảnh. | Nếu frame này được dùng trong viewport e-learning nhỏ, nhiều chi tiết có thể bị nhòe và trở thành nhiễu thay vì hỗ trợ người xem hiểu ý. | Chuẩn bị một biến thể đơn giản hơn cho màn hình nhỏ hoặc giảm mật độ chi tiết ở các yếu tố trang trí phụ. |

### Nội dung đã kiểm tra
- Tổng thể bố cục và độ cân bằng
- Mức độ rõ ràng của narrative ngày/đêm
- Thứ bậc thị giác và điểm nhấn
- Độ dễ đọc của các yếu tố dạng text
- Các rủi ro accessibility theo hướng nhìn WCAG
- Mức độ phù hợp khi dùng trong ngữ cảnh e-learning có thể bị scale nhỏ

### Ghi chú
- Pass này chỉ tập trung vào graphic QA, chưa đánh giá storyboard hoặc copy.
- WCAG 2.2 được dùng làm baseline để đánh giá khả năng đọc và accessibility ở góc độ hình ảnh.
