# Hướng dẫn sử dụng Petcare — dành cho người không biết gì về máy tính

Tài liệu này viết cho **chủ cửa hàng, lễ tân, nhân viên chăm sóc và khách hàng**. Bạn không cần biết lập trình.
Chỗ nào cần gõ lệnh, tài liệu ghi rõ **gõ chính xác từng chữ** và cho biết kết quả đúng trông như thế nào.

> Phần kỹ thuật (cho người lập trình) nằm ở [`README.md`](README.md). Tài liệu này chỉ nói về **cách dùng**.

---

## Mục lục

1. [Petcare là gì và làm được gì](#1-petcare-là-gì-và-làm-được-gì)
2. [Ai được làm gì (phân quyền)](#2-ai-được-làm-gì-phân-quyền)
3. [Bật phần mềm lần đầu](#3-bật-phần-mềm-lần-đầu)
4. [Dùng thử với dữ liệu có sẵn (chế độ demo)](#4-dùng-thử-với-dữ-liệu-có-sẵn-chế-độ-demo)
5. [Dành cho nhân viên: làm việc hằng ngày](#5-dành-cho-nhân-viên-làm-việc-hằng-ngày)
6. [Dành cho quản lý: những việc chỉ quản lý làm được](#6-dành-cho-quản-lý-những-việc-chỉ-quản-lý-làm-được)
7. [Dành cho khách hàng: cổng khách](#7-dành-cho-khách-hàng-cổng-khách)
8. [Trợ lý AI: dùng được gì, không dùng được gì](#8-trợ-lý-ai-dùng-được-gì-không-dùng-được-gì)
9. [Những điều phần mềm KHÔNG làm](#9-những-điều-phần-mềm-không-làm)
10. [Gặp sự cố thì làm gì](#10-gặp-sự-cố-thì-làm-gì)
11. [Giải thích từ ngữ](#11-giải-thích-từ-ngữ)

---

## 1. Petcare là gì và làm được gì

Petcare là phần mềm quản lý **cửa hàng dịch vụ thú cưng** (tắm, cắt móng, cắt tỉa lông, spa, tiêm nhắc lại…).
Phần mềm chạy ngay trên trình duyệt web (Chrome, Edge, Firefox…), giống như vào một trang web bình thường.

**Với nhân viên cửa hàng**, phần mềm giúp:

| Việc | Cách phần mềm giúp |
|---|---|
| Quản lý chủ nuôi và thú cưng | Lưu họ tên, số điện thoại, địa chỉ; mỗi chủ nuôi có nhiều thú cưng. Tìm nhanh, **không cần gõ dấu** tiếng Việt |
| Bảng giá dịch vụ | Ai cũng xem được; chỉ quản lý sửa giá, ngừng bán hay bán lại |
| Đặt lịch hẹn | Tự **chặn trùng giờ** (cùng nhân viên hoặc cùng thú cưng), chặn ngoài giờ mở cửa **08:00–18:00** và chặn đặt vào quá khứ |
| Ghi hồ sơ chăm sóc | Sau mỗi buổi làm, nhân viên ghi tình trạng, việc đã làm, lời dặn. Ghi xong lịch tự chuyển sang "Hoàn thành" |
| Theo dõi tiêm phòng | Sổ tiêm từng thú cưng; danh sách mũi sắp đến hạn nhắc lại |
| Hóa đơn và thu tiền | Lập hóa đơn từ buổi đã hoàn thành; thu nhiều lần (tiền mặt, chuyển khoản, thẻ) |
| Thống kê | Doanh thu, số lượt dịch vụ, số khách theo khoảng ngày (chỉ quản lý) |
| Trợ lý AI | Soạn sẵn tin nhắn nhắc lịch, tóm tắt hồ sơ chăm sóc, trả lời câu hỏi chăm sóc cơ bản |

**Với khách hàng**, có một "cổng khách" riêng: khách tự đăng ký tài khoản, xem thú cưng, lịch hẹn, hóa đơn
của mình, xem giờ còn trống, xin đặt lịch và hỏi AI chuyện chăm sóc thường ngày.

---

## 2. Ai được làm gì (phân quyền)

Có **ba vai trò nhân viên** và **một loại khách**. Mỗi người đăng nhập bằng tài khoản riêng và chỉ thấy phần việc của mình.

| Việc | Quản lý | Lễ tân | Nhân viên chăm sóc | Khách hàng |
|---|:-:|:-:|:-:|:-:|
| Xem và sửa chủ nuôi, thú cưng | ✓ | ✓ | ✓ | — |
| Xem bảng giá dịch vụ | ✓ | ✓ | ✓ | — |
| **Sửa** giá, ngừng/bán lại dịch vụ | ✓ | — | — | — |
| Đặt, đổi, hủy lịch hẹn của cửa hàng | ✓ | ✓ | — | — |
| Xem "Lịch của tôi" | — | — | ✓ | — |
| Ghi hồ sơ chăm sóc | ✓ | — | ✓ | — |
| Ghi mũi tiêm phòng | ✓ | ✓ | ✓ | — |
| Lập hóa đơn, thu tiền, hủy hóa đơn | ✓ | ✓ | — | — |
| Duyệt khách nối hồ sơ, duyệt lịch khách xin | ✓ | ✓ | — | — |
| Soạn tin nhắc lịch bằng AI | ✓ | ✓ | — | — |
| Tóm tắt hồ sơ bằng AI, hỏi đáp AI (nhân viên) | ✓ | ✓ | ✓ | — |
| Thống kê doanh thu | ✓ | — | — | — |
| Tạo, khóa, mở khóa tài khoản nhân viên; đặt lại mật khẩu | ✓ | — | — | — |
| Xem bảng lượt dùng AI | ✓ | — | — | — |
| Xem thú cưng, lịch, hóa đơn **của chính mình** | — | — | — | ✓ |
| Xin đặt lịch, hỏi AI (10 lượt/ngày) | — | — | — | ✓ |

Cần biết thêm:

- Vào trang mình **không có quyền** thì phần mềm báo "không đủ quyền" (lỗi 403), không làm hỏng gì.
- **Một trình duyệt chỉ giữ một người đăng nhập.** Nhân viên đăng nhập sẽ đẩy khách ra và ngược lại. Muốn
  thử cả hai cùng lúc, dùng hai trình duyệt khác nhau hoặc một cửa sổ ẩn danh.
- Khách **không bao giờ** thấy dữ liệu của khách khác. Mở nhầm địa chỉ của người khác chỉ thấy "không tìm thấy".
- Nhân viên (mọi vai trò) **xem được câu hỏi khách đã hỏi AI**. Đây là quyết định có chủ ý của chủ dự án; vì vậy
  hãy dặn khách không gõ số điện thoại hay địa chỉ vào ô hỏi AI.

---

## 3. Bật phần mềm lần đầu

Bước này **chỉ làm một lần**, hoặc nhờ người quen máy tính làm giúp. Máy cần có **Python 3.11 trở lên**
(tải miễn phí tại python.org nếu chưa có).

1. Mở thư mục chứa phần mềm (thư mục có file `run.py`).
2. Mở cửa sổ gõ lệnh trong thư mục đó:
   - **Windows:** bấm vào thanh địa chỉ của thư mục, gõ `cmd`, nhấn Enter.
   - **Mac / Linux:** mở ứng dụng Terminal rồi dùng lệnh `cd` đến thư mục phần mềm.
3. Gõ đúng một lệnh rồi nhấn Enter:

   ```
   python run.py
   ```

4. Chờ vài phút lần đầu (phần mềm tự cài những thứ cần thiết). Khi xong, **trình duyệt tự mở** trang đăng nhập
   tại địa chỉ `http://127.0.0.1:8000`.
5. Đăng nhập bằng một tài khoản mẫu ở mục tiếp theo.
6. **Khi dùng xong:** quay lại cửa sổ gõ lệnh, nhấn **Ctrl + C** để tắt. Lần sau chỉ cần gõ lại `python run.py`.

> Lưu ý: cửa sổ gõ lệnh phải **mở suốt** trong lúc dùng. Đóng cửa sổ là phần mềm tắt.

Muốn xóa sạch dữ liệu để làm lại từ đầu: gõ `python run.py reset`, trả lời xác nhận, rồi gõ `python run.py`.
**Cẩn thận: lệnh này xóa hết dữ liệu thật.**

---

## 4. Dùng thử với dữ liệu có sẵn (chế độ demo)

Để xem phần mềm khi đã có "nhiều dữ liệu thật" (hàng trăm lịch, hóa đơn, nhiều khách) mà **không ảnh hưởng dữ
liệu chính**, dùng chế độ demo. Dữ liệu demo nằm trong file riêng tên `demo.db`.

**Bước 1 — Tạo dữ liệu demo** (làm một lần, làm lại bất cứ lúc nào để đưa về trạng thái ban đầu):

```
python tools/tao_du_lieu_demo.py
```

Kết quả đúng: cuối màn hình in danh sách tài khoản, bắt đầu bằng dòng `Mật khẩu chung: matkhau123`.

**Bước 2 — Chạy phần mềm bằng dữ liệu demo:**

- Mac / Linux:

  ```
  DATABASE_URL=sqlite:///demo.db AI_PROVIDER=fake python run.py
  ```

- Windows (PowerShell):

  ```
  $env:DATABASE_URL="sqlite:///demo.db"; $env:AI_PROVIDER="fake"; python run.py
  ```

(`AI_PROVIDER=fake` nghĩa là AI trả lời mẫu, không cần mạng và không tốn lượt thật.)

### Tài khoản có sẵn

Mật khẩu chung cho **tất cả**: `matkhau123`

**Nhân viên** (đăng nhập ở trang đầu tiên, `/login`):

| Tên đăng nhập | Vai trò |
|---|---|
| `quanly` | Quản lý — làm được mọi việc |
| `letan` | Lễ tân |
| `chamsoc1`, `chamsoc2` | Nhân viên chăm sóc |

**Khách hàng** (đăng nhập ở `/khach/dang-nhap`, dùng email):

| Email | Tình trạng để thử |
|---|---|
| `khach1@demo.test`, `khach2@demo.test`, `khach3@demo.test` | Đã nối hồ sơ — xem được thú cưng, lịch, hóa đơn |
| `khach4@demo.test` | Đang **chờ lễ tân duyệt** nối hồ sơ — đăng nhập vào lễ tân duyệt thử |
| `khach5@demo.test` | Bị **từ chối** nối hồ sơ (kèm lý do) |
| `khach6@demo.test` | Mới đăng ký, **chưa gửi** yêu cầu nối hồ sơ |
| `khach7@demo.test` | **Đã dùng hết 10 lượt AI** trong ngày — thử xem phần mềm báo gì |

Gợi ý kịch bản demo trọn vòng (khoảng 10 phút):

1. Đăng nhập `khach6@demo.test`, vào **Liên kết hồ sơ**, nhập số điện thoại `0901000003`, gửi yêu cầu.
2. Đăng xuất. Đăng nhập `letan`, vào **Liên kết khách**, bấm **Duyệt** yêu cầu vừa gửi.
3. Đăng xuất. Đăng nhập lại `khach6@demo.test`: đã thấy thú cưng, lịch, hóa đơn.
4. Vào **Giờ trống**, chọn thú cưng và dịch vụ, xem các khung còn trống, rồi **Xin đặt lịch** → lịch ở trạng thái "Chờ duyệt".
5. Đăng nhập `letan`, vào **Lịch chờ duyệt**, bấm **Duyệt**. Khách mở lại **Lịch hẹn** sẽ thấy "Đã đặt".

---

## 5. Dành cho nhân viên: làm việc hằng ngày

Đăng nhập tại `http://127.0.0.1:8000`. Trên cùng có menu; menu hiện ra tùy vai trò của bạn (mục 2).

- Sai mật khẩu **5 lần liên tiếp** thì bị khóa tạm **30 giây**, sai tiếp thì khóa lâu hơn (gấp đôi mỗi lần, tối đa 15 phút).
  Chờ hết thời gian rồi thử lại.
- Đổi mật khẩu: bấm **Đổi mật khẩu** trên menu. Mật khẩu **ít nhất 8 ký tự**.

### 5.1. Chủ nuôi và thú cưng

1. Bấm **Chủ nuôi** trên menu.
2. **Thêm chủ nuôi:** điền họ tên và số điện thoại (bắt buộc; số Việt Nam gồm 10 chữ số, bắt đầu bằng 0), email và
   địa chỉ (không bắt buộc) rồi bấm **Lưu**.
3. **Tìm kiếm:** gõ tên hoặc số điện thoại vào ô tìm. Có thể gõ **không dấu**: `do thi hang` vẫn tìm ra "Đỗ Thị Hằng".
4. Bấm tên chủ nuôi để mở hồ sơ: sửa thông tin, **thêm thú cưng** (tên, loài, giống, ngày sinh, cân nặng).
5. **Xóa:** chỉ xóa được chủ nuôi khi **không còn thú cưng** và không có tài khoản khách đang nối; chỉ xóa được thú
   cưng khi **chưa có lịch hẹn hoặc mũi tiêm**. Phần mềm giải thích lý do bằng tiếng Việt nếu bị chặn — đây là
   cách phần mềm giữ lịch sử, không phải lỗi.

### 5.2. Đặt lịch hẹn (quản lý, lễ tân)

1. Bấm **Lịch hẹn**.
2. Chọn **thú cưng, dịch vụ, nhân viên phụ trách, ngày, giờ**, bấm **Đặt lịch**.
3. Phần mềm sẽ **từ chối** và nói rõ lý do (kèm gợi ý khung giờ trống) nếu:
   - giờ nằm ngoài **08:00–18:00** (kể cả khi buổi làm kéo dài quá 18:00);
   - ngày giờ đã ở **quá khứ**;
   - nhân viên đó **đã có lịch** trùng giờ, hoặc thú cưng đó đã có lịch trùng giờ.
4. Mỗi lịch có nút **Đổi** (chọn giờ mới, vẫn được kiểm trùng) và **Hủy** (**bắt buộc ghi lý do**).
5. Nhân viên chăm sóc không đặt lịch, chỉ xem lịch được giao ở **Lịch của tôi**.

Các trạng thái của một lịch: **Chờ duyệt** (khách xin) → **Đã đặt** → **Đã đổi lịch** / **Đã hủy** / **Hoàn thành**.

### 5.3. Ghi hồ sơ chăm sóc (quản lý, nhân viên chăm sóc)

1. Sau buổi làm, mở lịch hẹn đó, bấm **Hồ sơ**.
2. Điền **Tình trạng thú cưng** (bắt buộc), **Việc đã làm**, **Dặn dò** rồi **Lưu**.
3. Lưu xong, lịch **tự chuyển sang "Hoàn thành"**. Đây là **cách duy nhất** để một lịch thành "Hoàn thành".
4. Mỗi lịch chỉ có **một** hồ sơ. Lịch chưa tới giờ, lịch đã hủy, lịch đang chờ duyệt thì không ghi hồ sơ được.

### 5.4. Tiêm phòng

- Bấm **Tiêm phòng** để xem các mũi **sắp đến hạn nhắc lại** của mọi thú cưng.
- Ghi mũi mới ở trang của từng thú cưng: tên vắc-xin, số mũi, ngày tiêm, ngày nhắc lại (phải **sau** ngày tiêm).

### 5.5. Hóa đơn và thu tiền (quản lý, lễ tân)

1. **Chỉ lập được hóa đơn cho lịch đã "Hoàn thành"**: mở lịch đó và bấm **Lập hóa đơn**. Mỗi lịch một hóa đơn.
2. Giá trên hóa đơn là giá **tại lúc lập**; sau này đổi bảng giá cũng không làm đổi hóa đơn cũ.
3. Trong hóa đơn, bấm **Thu tiền**: nhập số tiền và chọn hình thức (**Tiền mặt / Chuyển khoản / Thẻ**).
   Có thể thu **nhiều lần**. Trạng thái đi từ **Chưa thanh toán** → **Thanh toán một phần** → **Đã thanh toán**.
   Không thu quá số còn nợ.
4. **Hủy hóa đơn** (lập nhầm): chỉ được khi **chưa thu đồng nào**. Phần mềm **không có chức năng hoàn tiền**.

### 5.6. Duyệt khách hàng (quản lý, lễ tân)

**Liên kết khách** — khách tự đăng ký tài khoản, rồi xin nối với hồ sơ chủ nuôi bằng số điện thoại:

1. Bấm **Liên kết khách**: thấy các yêu cầu đang chờ.
2. **Đối chiếu** thông tin khách gửi với hồ sơ chủ nuôi (số điện thoại, tên).
3. Bấm **Duyệt** nếu đúng người, hoặc **Từ chối** (phải ghi lý do — khách sẽ đọc được).
4. Trường hợp có nhiều chủ nuôi nghi trùng, chọn đúng người trước khi duyệt.
5. Có thể **gỡ liên kết** của tài khoản đã duyệt khi nối nhầm.

**Lịch chờ duyệt** — lịch do khách xin:

1. Bấm **Lịch chờ duyệt**.
2. **Duyệt** → lịch thành "Đã đặt". **Từ chối** → phải ghi lý do, khách sẽ thấy ở "Ghi chú của cửa hàng".
3. Lịch chờ quá **24 giờ** mà chưa ai xử lý sẽ **tự chuyển sang "Đã hủy"** và khung giờ được mở lại cho người khác.
   Mỗi khách giữ tối đa **3 lịch chờ** cùng lúc.

---

## 6. Dành cho quản lý: những việc chỉ quản lý làm được

Đăng nhập bằng tài khoản `quanly` (hoặc tài khoản quản lý của cửa hàng bạn).

- **Sửa bảng giá** (menu **Dịch vụ**): sửa giá, thêm gói, **ngừng bán** hoặc **bán lại** dịch vụ/gói. Dịch vụ ngừng
  bán không chọn được cho lịch mới, nhưng hóa đơn cũ giữ nguyên.
- **Thống kê** (`/stats`): chọn khoảng ngày để xem số lượt dịch vụ, số khách và doanh thu, kèm bảng theo từng dịch vụ.
- **Tài khoản nhân viên** (`/users`): thêm nhân viên (tên đăng nhập, họ tên, vai trò, mật khẩu ban đầu), sửa họ tên và
  vai trò, **khóa / mở khóa** khi nhân viên nghỉ việc, **đặt lại mật khẩu** khi quên. Tên đăng nhập không được trùng.
- **Lượt AI** (`/ai/quota`): xem còn bao nhiêu lượt gọi AI thật. Có nút **đặt lại trạng thái chặn** khi hệ thống đoán
  sai là đã hết lượt.

---

## 7. Dành cho khách hàng: cổng khách

Địa chỉ: `http://127.0.0.1:8000/khach` (nếu cửa hàng đặt phần mềm trên mạng, họ sẽ đưa bạn địa chỉ thật).

### 7.1. Đăng ký và đăng nhập

1. Vào **Đăng ký**: nhập họ tên, email, mật khẩu (**ít nhất 8 ký tự**).
2. Phần mềm gửi một **thư xác minh** vào email của bạn. Bấm vào liên kết trong thư (hiệu lực **24 giờ**,
   chỉ dùng **một lần**). Không thấy thư thì xem cả mục **thư rác**.
3. **Đăng nhập** bằng email và mật khẩu.
4. **Quên mật khẩu:** bấm "Quên mật khẩu", nhập email, mở thư và bấm liên kết đặt lại (hiệu lực **1 giờ**, một lần).
5. **Đổi mật khẩu** bất cứ lúc nào ở mục **Đổi mật khẩu**.
6. Sai mật khẩu nhiều lần liên tiếp thì bị khóa tạm vài chục giây; chờ rồi thử lại.

### 7.2. Nối tài khoản với hồ sơ ở cửa hàng

Lúc mới đăng ký, bạn **chưa thấy gì** — đây là cố ý, để người lạ không xem được thú cưng của người khác.

1. Vào **Liên kết hồ sơ**, nhập **số điện thoại bạn đã đưa cho cửa hàng**, thêm ghi chú nếu muốn, bấm gửi.
2. Chờ **lễ tân đối chiếu và duyệt** (thường trong giờ làm việc).
3. Được duyệt thì mở lại trang chủ: bạn thấy thú cưng, lịch hẹn, hóa đơn. Bị từ chối thì đọc lý do, sửa lại thông tin
   rồi gửi lại.

### 7.3. Xem thông tin của mình

- **Thú cưng:** danh sách và chi tiết từng bé (loài, giống, ngày sinh, cân nặng) cùng **lịch sử tiêm phòng**. Khách chưa xem được hồ sơ chăm sóc nội bộ.
- **Lịch hẹn:** các lịch đã đặt, đang chờ, đã hủy (kèm lý do cửa hàng ghi).
- **Hóa đơn:** số tiền, đã trả bao nhiêu, còn nợ bao nhiêu.

Bạn **chỉ thấy dữ liệu của chính mình**.

### 7.4. Xem giờ trống và xin đặt lịch

1. Vào **Giờ trống**: chọn thú cưng, dịch vụ, ngày → xem các khung còn trống (trong **08:00–18:00**) theo từng nhân viên.
2. Vào **Xin đặt lịch**: chọn thú cưng, dịch vụ, nhân viên, ngày, giờ, ghi chú, rồi gửi.
3. Lịch ở trạng thái **Chờ duyệt**. Cửa hàng sẽ **duyệt** hoặc **từ chối kèm lý do**. Quá **24 giờ** không ai xử lý thì
   yêu cầu tự hủy — hãy gọi cửa hàng nếu cần gấp.
4. Mỗi khách có **tối đa 3 lịch chờ** cùng lúc; vượt thì phần mềm báo, hãy chờ cửa hàng xử lý bớt.
5. **Khách không tự hủy hay đổi lịch trên cổng**; muốn đổi, gọi cửa hàng.

### 7.5. Hỏi AI về chăm sóc thú cưng

1. Vào **Hỏi đáp**, gõ câu hỏi chăm sóc thường ngày (ví dụ "bao lâu nên tắm cho chó một lần?").
2. **Mỗi tài khoản tối đa 10 câu mỗi ngày.** Hết lượt thì nút bị khóa đến ngày hôm sau.
3. Câu trả lời **chỉ để tham khảo** và luôn kèm lời khuyên liên hệ bác sĩ thú y.
4. **Không gõ** số điện thoại, địa chỉ hay thông tin cá nhân vào ô hỏi.
5. Hỏi xin **thuốc hay liều lượng** sẽ bị từ chối, và vẫn **tính một lượt**.

---

## 8. Trợ lý AI: dùng được gì, không dùng được gì

| Ở đâu | Ai dùng | Làm gì |
|---|---|---|
| Nút **Soạn tin nhắc (AI)** ở Lịch hẹn và Tiêm phòng | Quản lý, lễ tân | Soạn sẵn tin nhắn nhắc khách. **Sửa được** trước khi gửi |
| Nút **Tóm tắt bằng AI** ở trang thú cưng | Nhân viên | Tóm tắt lịch sử chăm sóc của bé |
| Menu **Trợ lý AI** | Nhân viên | Hỏi đáp chăm sóc cơ bản |
| **Hỏi đáp** trong cổng khách | Khách | Như trên, 10 lượt/ngày |

Quy tắc an toàn **nằm sẵn trong phần mềm** (không phụ thuộc AI có "nghe lời" hay không):

- AI **không chẩn đoán bệnh, không kê thuốc, không nêu liều lượng**. Hỏi xin thuốc bị chặn trước khi gọi AI.
- Mọi câu trả lời về sức khỏe đều **kèm khuyến cáo** hỏi bác sĩ thú y.
- **Không gửi** số điện thoại, email, địa chỉ của chủ nuôi cho AI. Chỉ gửi nội dung chăm sóc thú cưng. Với khách,
  chỉ riêng câu hỏi được gửi đi.
- Nội dung do AI soạn **chỉ mang tính tham khảo**; con người phải đọc lại trước khi gửi cho khách.
- Ở chế độ thử (`AI_PROVIDER=fake`) AI chỉ trả một câu mẫu cố định; có thông báo hiện rõ trên trang.

---

## 9. Những điều phần mềm KHÔNG làm

Để khỏi hiểu lầm khi giới thiệu hay demo, đây là những giới hạn hiện tại:

| Giới hạn | Ghi chú |
|---|---|
| **Không có hoàn tiền** | Hóa đơn đã thu tiền thì không hủy được; chỉ hủy được hóa đơn chưa thu |
| **Khách không tự hủy/đổi lịch** | Chỉ xin đặt mới; đổi hoặc hủy phải liên hệ cửa hàng |
| **Khách không thanh toán trực tuyến** | Khách chỉ **xem** hóa đơn; tiền thu tại quầy do nhân viên ghi |
| **Không tự gửi tin nhắn cho khách** | AI soạn tin nháp; nhân viên tự copy gửi qua Zalo/SMS/điện thoại |
| **Không phải phần mềm y tế** | Không chẩn đoán, không kê đơn. Chỉ lưu sổ chăm sóc và nhắc lịch |
| **Không có hàng tồn kho, bán hàng, chấm công, lương** | Chỉ làm dịch vụ chăm sóc, lịch, tiêm, hóa đơn |
| **Một cửa hàng, một cơ sở dữ liệu** | Chưa hỗ trợ nhiều chi nhánh |
| **Giờ mở cửa cố định 08:00–18:00** | Đổi giờ phải nhờ người lập trình sửa |
| **Một trình duyệt, một người đăng nhập** | Muốn đóng vai nhiều người cùng lúc phải dùng nhiều trình duyệt/cửa sổ ẩn danh |
| **AI hạn mức** | Bản AI thật dùng gói miễn phí nên có giới hạn lượt; hết lượt sẽ báo lỗi AI chứ không làm hỏng phần khác |
| **Nhân viên đọc được câu khách hỏi AI** | Quyết định có chủ ý; dặn khách đừng gõ thông tin cá nhân vào ô hỏi |
| **Dữ liệu nằm trên máy chạy phần mềm** | Cần tự **sao lưu** file `petcare.db`; mất máy là mất dữ liệu |
| **Nhân viên không tự lấy lại mật khẩu bằng email** | Nhân viên quên mật khẩu thì quản lý đặt lại ở `/users` |

Hai lỗi nhỏ đã biết, **chưa sửa** (không làm mất dữ liệu):

- **Thư giả khi chạy thử trên máy mình:** ở chế độ thử, thư xác minh email của khách lẽ ra hiện trong cửa sổ gõ lệnh
  nhưng hiện chưa hiện. Cửa hàng thật cần cấu hình gửi email thật (nhờ người lập trình).
- **Ô chọn tròn ở trang "Liên kết khách" của nhân viên có thể hiện rất to** khi có nhiều chủ nuôi nghi trùng. Vẫn bấm chọn
  được, chỉ xấu giao diện.

---

## 10. Gặp sự cố thì làm gì

| Hiện tượng | Cách xử lý |
|---|---|
| Gõ `python run.py` báo không tìm thấy `python` | Chưa cài Python, hoặc thử gõ `python3 run.py` |
| Trình duyệt không mở / báo không vào được | Chắc chắn cửa sổ gõ lệnh vẫn đang chạy; tự mở `http://127.0.0.1:8000` |
| Báo cổng 8000 bận | Gõ `python run.py --port 9000` rồi mở `http://127.0.0.1:9000` |
| Đăng nhập báo "thử lại sau … giây" | Sai mật khẩu quá nhiều lần; đợi hết thời gian rồi thử lại. Quản lý có thể đặt lại mật khẩu cho nhân viên ở `/users` |
| Quên mật khẩu quản lý | Nhờ người lập trình đặt lại; hoặc làm lại từ đầu bằng `python run.py reset` (**mất hết dữ liệu**) |
| Báo "không đủ quyền" (403) | Tài khoản của bạn không có quyền ở trang đó — xem mục 2 |
| Không đặt được lịch | Đọc câu báo lỗi đỏ: thường là ngoài 08:00–18:00, ở quá khứ hoặc trùng giờ |
| Không lập được hóa đơn | Lịch chưa "Hoàn thành" — ghi hồ sơ chăm sóc trước |
| Không xóa được chủ nuôi / thú cưng | Còn thú cưng, lịch hoặc mũi tiêm liên quan; phần mềm giữ lịch sử có chủ ý |
| Khách không thấy dữ liệu sau khi đăng ký | Chưa nối hồ sơ hoặc lễ tân chưa duyệt — xem mục 7.2 |
| Khách không nhận được thư xác minh | Xem mục thư rác; hoặc nhờ người lập trình kiểm tra cấu hình email |
| AI báo lỗi | Có thể hết lượt AI trong ngày hoặc mất mạng. Phần còn lại của phần mềm vẫn dùng bình thường |
| Dữ liệu mẫu bị lệch ngày | Dữ liệu mẫu tính theo ngày lúc tạo; tạo lại bằng `python run.py reset` (dữ liệu chính) hoặc chạy lại `python tools/tao_du_lieu_demo.py` (dữ liệu demo) |

**Sao lưu dữ liệu:** dữ liệu thật nằm trong file `petcare.db` cạnh `run.py`. Tắt phần mềm rồi **chép file này** ra ổ USB
hoặc nơi an toàn mỗi ngày/tuần là đủ. Khôi phục bằng cách chép ngược lại khi phần mềm đang tắt.

---

## 11. Giải thích từ ngữ

| Từ | Nghĩa |
|---|---|
| **Cổng khách** | Khu vực web dành riêng cho khách hàng của cửa hàng, địa chỉ có đuôi `/khach` |
| **Liên kết hồ sơ** | Việc nối tài khoản khách với hồ sơ chủ nuôi mà cửa hàng đã lưu |
| **Chờ duyệt** | Lịch khách xin nhưng cửa hàng chưa xác nhận |
| **Hồ sơ chăm sóc** | Ghi chép sau mỗi buổi làm: tình trạng, việc đã làm, lời dặn |
| **Hoàn thành** | Lịch đã có hồ sơ chăm sóc; chỉ lịch hoàn thành mới lập được hóa đơn |
| **Terminal / cửa sổ gõ lệnh** | Cửa sổ chữ đen hoặc trắng dùng để chạy lệnh `python run.py` |
| **Cơ sở dữ liệu** | Nơi phần mềm cất mọi thông tin; ở đây là file `petcare.db` (thật) hoặc `demo.db` (thử) |
| **AI giả (`fake`)** | Chế độ thử: AI trả câu mẫu cố định, không gọi dịch vụ AI thật |
| **Đăng xuất** | Thoát khỏi tài khoản; nên làm khi dùng máy chung |
