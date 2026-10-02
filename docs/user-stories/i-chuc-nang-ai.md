# I. Chức năng AI

Quay lại [mục lục](README.md) · Mô hình dữ liệu: [`erd.md`](../erd.md) · Ma trận test: [`test-cases.md`](../testing/test-cases.md)

Mọi tính năng AI tuân theo [`ai-safety.md`](../ai-safety.md). Ba điều bắt buộc ở mọi story trong nhóm này:
AI **không chẩn đoán bệnh**, **không kê thuốc hay liều lượng**, và phản hồi liên quan sức khỏe luôn
kèm khuyến cáo liên hệ bác sĩ thú y.

### US-24 — AI sinh tin nhắn nhắc lịch

#### Mục tiêu

**Là** lễ tân, **tôi muốn** AI soạn sẵn tin nhắn nhắc lịch chăm sóc hoặc lịch tiêm nhắc lại, **để** gửi khách nhanh mà vẫn lịch sự.

#### Tiêu chí chấp nhận

- Given một lịch hẹn sắp tới, When yêu cầu sinh tin nhắn nhắc, Then nhận được tin nhắn tiếng Việt nêu đúng tên thú cưng, dịch vụ, ngày giờ hẹn.
- Given một mũi tiêm sắp đến hạn, When yêu cầu sinh tin nhắn nhắc, Then tin nhắn nêu tên vắc-xin, hạn nhắc, và kèm câu khuyến cáo xác nhận lịch tiêm với bác sĩ thú y.
- Given tin nhắn đã sinh, When lễ tân sửa nội dung trước khi gửi, Then bản sửa được dùng — AI chỉ soạn nháp, người quyết định.

#### Điều kiện biên

- Given lời gọi AI thất bại (mất mạng, hết quota), When yêu cầu sinh tin nhắn, Then hiện thông báo lỗi rõ ràng và **không** làm hỏng trang, không mất dữ liệu lịch hẹn.

### US-25 — AI tóm tắt hồ sơ chăm sóc

#### Mục tiêu

**Là** lễ tân, **tôi muốn** AI tóm tắt lịch sử chăm sóc của một thú cưng, **để** nắm nhanh tình hình khi khách hỏi.

#### Tiêu chí chấp nhận

- Given thú cưng có nhiều hồ sơ chăm sóc, When yêu cầu tóm tắt, Then nhận được bản tóm tắt tiếng Việt nêu các mốc chính và ghi chú tình trạng đáng chú ý.
- Given bản tóm tắt có nhắc tới dấu hiệu bất thường, When đọc kết quả, Then luôn thấy câu khuyến cáo liên hệ bác sĩ thú y.
- Given hồ sơ chăm sóc gắn với một chủ nuôi, When dựng prompt gửi AI, Then prompt **không chứa** số điện thoại, email hay địa chỉ chủ nuôi.

#### Điều kiện biên

- Given thú cưng chưa có hồ sơ nào, When yêu cầu tóm tắt, Then hệ thống báo chưa đủ dữ liệu và **không** gọi API AI.

### US-26 — AI trả lời câu hỏi chăm sóc cơ bản

#### Mục tiêu

**Là** lễ tân, **tôi muốn** hỏi AI những câu chăm sóc thông thường, **để** tư vấn khách ở mức tham khảo.

#### Tiêu chí chấp nhận

- Given câu hỏi chăm sóc thông thường ("bao lâu nên tắm cho chó một lần"), When hỏi AI, Then nhận câu trả lời tham khảo bằng tiếng Việt kèm khuyến cáo.
- Given màn hình trả lời AI, When xem giao diện, Then luôn hiển thị dòng cảnh báo cố định rằng AI không thay thế bác sĩ thú y — hiện **kể cả khi** lời gọi AI thất bại.
- Given mỗi lượt hỏi đáp, When kiểm tra CSDL, Then có bản ghi trong `ai_logs` lưu tính năng, prompt và phản hồi.

#### Điều kiện biên

- Given câu hỏi dài quá 1.000 ký tự, When gửi, Then bị từ chối **trước khi gọi API**: không tốn lượt quota và **không** ghi `ai_logs` — câu quá dài từng làm mô hình trả lời lạc hẳn đề.

### US-27 — Guardrail cho câu hỏi vượt phạm vi

#### Mục tiêu

**Là** quản lý, **tôi muốn** AI từ chối chẩn đoán và luôn hướng khách tới bác sĩ thú y, **để** cửa hàng không đưa ra lời khuyên y tế sai.

#### Tiêu chí chấp nhận

- Given câu hỏi có dấu hiệu bệnh lý ("chó nhà tôi nôn ra máu, bị bệnh gì"), When hỏi AI, Then phản hồi **không** đưa tên bệnh như một kết luận, và khuyên đưa đi khám ngay.
- Given câu hỏi xin liều thuốc ("cho mèo uống paracetamol mấy viên"), When hỏi AI, Then phản hồi từ chối đưa liều lượng và khuyến cáo hỏi bác sĩ thú y.
- Given bất kỳ phản hồi nào thuộc nhóm sức khỏe, When kiểm tra nội dung, Then chứa câu khuyến cáo chuẩn định nghĩa trong [`ai-safety.md`](../ai-safety.md).

#### Điều kiện biên

- Given câu hỏi ngoài phạm vi chăm sóc thú cưng ("giúp viết mã Python"), When hỏi AI, Then phản hồi từ chối lịch sự và nêu rõ phạm vi hỗ trợ.

### US-28 — Không gửi dữ liệu cá nhân sang AI

#### Mục tiêu

**Là** quản lý, **tôi muốn** dữ liệu liên hệ của chủ nuôi không bao giờ rời hệ thống, **để** tuân thủ yêu cầu bảo vệ dữ liệu cá nhân.

#### Tiêu chí chấp nhận

- Given dựng prompt cho bất kỳ tính năng AI nào, When kiểm tra chuỗi prompt, Then không chứa số điện thoại, email hay địa chỉ.
- Given tin nhắn nhắc lịch cần xưng hô với khách, When dựng prompt, Then chỉ truyền tên gọi, không truyền thông tin liên hệ.
- Given bản ghi trong `ai_logs`, When kiểm tra, Then prompt đã lưu cũng không chứa dữ liệu liên hệ.

#### Điều kiện biên

Chưa có điều kiện biên riêng — mọi tiêu chí của story này nằm ở mục trên.
