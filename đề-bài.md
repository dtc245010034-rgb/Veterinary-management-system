Hệ thống quản lý thú cưng và lịch chăm sóc có tích hợp AI
1. Mô tả bài toán

Cửa hàng dịch vụ thú cưng cần quản lý thú cưng, chủ nuôi, lịch spa/tắm/grooming, lịch tiêm phòng nhắc lại, dịch vụ và thanh toán. Chủ nuôi thường cần nhắc lịch và hướng dẫn chăm sóc cơ bản. Hệ thống cần quản lý dịch vụ thú cưng và tích hợp AI sinh nhắc lịch, tóm tắt hồ sơ chăm sóc và trả lời câu hỏi chăm sóc thông thường ở mức tham khảo.
2. Mục tiêu

- Quản lý chủ nuôi, thú cưng, lịch dịch vụ, hồ sơ chăm sóc, thanh toán.
- Tích hợp AI để nhắc lịch, tóm tắt hồ sơ và trả lời câu hỏi chăm sóc cơ bản.
- Sử dụng AI trong SDLC để phân tích, thiết kế, code, test và tài liệu.
3. Yêu cầu chức năng
3.1. Chức năng quản lý
1. Đăng nhập và phân quyền quản lý, lễ tân, nhân viên chăm sóc.
2. Quản lý chủ nuôi và thú cưng.
3. Quản lý dịch vụ chăm sóc, bảng giá, gói dịch vụ.
4. Đặt lịch chăm sóc, đổi lịch, hủy lịch.
5. Ghi nhận hồ sơ chăm sóc và ghi chú tình trạng.
6. Quản lý lịch nhắc tiêm/phòng bệnh ở mức thông tin.
7. Lập hóa đơn và theo dõi thanh toán.
8. Thống kê lượt dịch vụ, doanh thu, khách quay lại.
3.2. Chức năng AI
1. AI sinh tin nhắn nhắc lịch chăm sóc hoặc lịch tiêm nhắc.
2. AI tóm tắt hồ sơ chăm sóc của thú cưng.
3. AI trả lời câu hỏi chăm sóc thông thường với cảnh báo hỏi bác sĩ thú y khi cần.
4. Yêu cầu kỹ thuật

- Backend FastAPI/Flask/Django; frontend React/Vue/HTML.
- CSDL SQLite/MySQL/PostgreSQL.
- AI Engine OpenAI/Gemini/Claude/Hugging Face/Ollama.
- Có cảnh báo AI không thay thế bác sĩ thú y.
- Có test cho lịch hẹn, hóa đơn, hồ sơ và AI.
5. Dữ liệu đầu vào, đầu ra và dữ liệu hệ thống

- Dữ liệu chính: chủ nuôi, thú cưng, dịch vụ, lịch hẹn, hồ sơ chăm sóc, hóa đơn.
- Đầu vào AI: lịch sử chăm sóc, lịch hẹn, câu hỏi chăm sóc cơ bản.
- Đầu ra AI: tin nhắn nhắc lịch, tóm tắt hồ sơ, câu trả lời tham khảo.

Prompt mẫu:

System: Bạn là trợ lý chăm sóc thú cưng. Chỉ đưa thông tin tham khảo, không chẩn đoán bệnh. Khi có dấu hiệu bất thường, khuyên liên hệ bác sĩ thú y.
User: Hồ sơ chăm sóc: {{pet_care_history}}. Hãy tóm tắt tình trạng và viết tin nhắn nhắc lịch sắp tới.
6. Hướng dẫn sử dụng AI trong từng giai đoạn SDLC

- KT1: Dùng AI phân tích nghiệp vụ đặt lịch, chăm sóc, nhắc lịch; thiết kế use case và ERD.
- KT2: Dùng AI sinh CRUD chủ nuôi, thú cưng, dịch vụ, lịch; debug trùng lịch.
- KT3: Dùng AI thiết kế prompt an toàn, test câu hỏi vượt phạm vi y tế thú y.
- Cuối kỳ: Dùng AI viết README, báo cáo, slide và review dữ liệu cá nhân.
7. Mức độ khó

Trung bình: Hệ thống có lịch hẹn và hồ sơ chăm sóc; AI cần cảnh báo giới hạn khi trả lời câu hỏi liên quan sức khỏe thú cưng.
