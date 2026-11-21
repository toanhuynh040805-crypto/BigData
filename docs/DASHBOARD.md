# Dashboard phiên bản đồ án cuối kỳ — Energy Intelligence

Dashboard Streamlit 7 màn hình bằng tiếng Việt, biểu đồ Plotly tương tác và giao diện responsive. Sử dụng bản tổng hợp UCI thật đã công bố trong thư mục results/uci/ (không phải dữ liệu giả lập).

## Chạy nhanh trên Windows, không cần tải PySpark

Nếu bạn đã clone repository vào ổ E và cài Streamlit/Plotly/Pandas:

~~~powershell
cd E:\BigData
git pull origin main
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
~~~

Nếu chưa có thư viện giao diện:

~~~powershell
cd E:\BigData
.\.venv\Scripts\python.exe -m pip install -r requirements-dashboard.txt --timeout 300 --retries 10
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
~~~

Mở http://localhost:8501. Để tắt, nhấn Ctrl+C trong Terminal đang chạy Streamlit.

PySpark (~318 MB) và Java 17 chỉ cần khi **tự chạy lại pipeline Spark**, không cần khi xem CSV/JSON có sẵn. Nếu muốn xử lý lại dữ liệu, xem [SETUP.md](SETUP.md).

## Hệ thống 7 màn hình

| Màn hình | Chức năng | Minh chứng cho báo cáo |
|---|---|---|
| Tổng quan | KPI, điện năng theo ngày và trung bình trượt, tháng, giờ cao điểm, insight tự động | Mục tiêu và kết quả xử lý dữ liệu |
| Xu hướng & cao điểm | Ngày trong tuần, ngày thường/cuối tuần, heatmap tháng-năm, IQR phát hiện ngày khác biệt | Phân tích mô tả và phát hiện bất thường |
| Nhánh thiết bị | Ba nhánh Wh→kWh, tỷ trọng/diễn biến, ước lượng điện năng chưa phân nhánh, kịch bản giảm giả định | Phân tích theo thiết bị |
| So sánh khu vực | OPSD năm 2019: 5 quốc gia, điện năng GWh và công suất MW, độ bao phủ theo giờ | Phân tích khu vực bằng dữ liệu thật, độc lập với UCI |
| Dự báo AI | MAE/RMSE/R², % cải thiện với baseline, biểu đồ thực tế-vs-dự báo, sai số theo tháng, tải dự báo | Quy trình mô hình hóa và đánh giá |
| Chất lượng dữ liệu | Tổng dòng, dòng lỗi/trùng, bao phủ từng ngày, ngày dưới 90%, quy tắc làm sạch | Tiền xử lý và độ tin cậy |
| Dữ liệu & báo cáo | Bảng lọc, tải CSV và JSON, kiến trúc, link GitHub/Word/PPT/UCI | Tính tái lập và minh chứng thực nghiệm |

## Bộ lọc và quy ước

- **Nguồn:** ưu tiên “UCI thật · Kết quả GitHub” để demo, tránh vô tình hiển thị dữ liệu synthetic do tự chạy ở máy.
- **Khoảng thời gian:** toàn kỳ, 12 tháng cuối, 90 ngày cuối hoặc chọn hai ngày cụ thể.
- **Độ bao phủ:** 0–100%; dùng để loại bỏ ngày thiếu số đo khỏi các biểu đồ phân tích. Mặc định giữ mọi ngày có quan sát.
- **Biểu đồ theo giờ:** dùng hourly_profile.csv cho **toàn bộ giai đoạn**. Giao diện gắn nhãn rõ là không chịu bộ lọc theo ngày.
- **Dự báo AI:** dùng kết quả train/test đã chạy và lưu trước, không huấn luyện lại từ trình duyệt và không thay đổi theo bộ lọc ngày.
- **Ngày bất thường:** phát hiện bằng IQR từ các ngày bao phủ ≥90%, chỉ là phát hiện thống kê, không chẩn đoán lỗi thiết bị.
- **Kịch bản tiết kiệm:** phép nhân giả định trên mức tiêu thụ quan sát; không đại diện cho hóa đơn hoặc hiệu quả cam kết.

## Số liệu thực nghiệm nguồn UCI

Nguồn file: results/uci/quality.json và results/uci/metrics.json.
- Bản ghi gốc: 2.075.259; bản ghi sạch: 2.049.280; bị loại: 25.979.
- Mô hình: train 1.089 ngày, test 273 ngày; Random Forest MAE 3,9731 và RMSE 5,4152 kWh/ngày; baseline MAE 5,0621.
- Dự báo lịch sử ngày 26/11/2010 khoảng 29,32 kWh. Không phải dự báo năm 2026.

## Kịch bản demo 5–8 phút

1. Mở Tổng quan: giới thiệu UCI, các KPI và xu hướng.
2. Mở Xu hướng: so sánh các thứ và heatmap, giải thích cách IQR gắn nhãn ngày khác biệt.
3. Mở Thiết bị: cho thấy ba nhánh điện, nhấn mạnh không có phân tích khu vực địa lý.
4. Mở Dự báo AI: chỉ ra MAE 3,973 vs baseline 5,062 và biểu đồ test.
5. Mở Chất lượng: chứng minh xử lý gần 2,1 triệu bản ghi bằng Spark; giải thích phút thiếu.
6. Mở Dữ liệu & báo cáo: tải CSV/JSON, dẫn đến Word/PPT và mã nguồn.

## Minh chứng và giới hạn quan trọng

- Số liệu UCI: một hộ ở Sceaux, Pháp, trong khoảng 2006–2010; không suy rộng ra vùng địa lý.
- Nguồn không có timezone/UTC offset, không tự hiệu chỉnh DST.
- Không biết điện năng của các phút bị thiếu; số liệu là ước lượng theo các mẫu đo được.
- Kết quả dự báo không chứng minh mô hình hoạt động ở năm hiện tại.
- File Word/PPT trong reports/ là bản nháp tạo tự động và phải cập nhật thông tin giảng viên, hai thành viên, đóng góp thực tế.


## Trang 7: So sánh khu vực địa lý

Kết quả vùng được đọc từ results/regions/ (OPSD 2019, MW và GWh), hoàn toàn độc lập với results/uci/ (UCI 2006–2010, kWh). Nguồn OPSD xem docs/REGIONS.md; cả hai tập được xử lý bằng Spark và công bố trên GitHub.

Không cần tải bộ OPSD 124 MB trên máy Windows nếu đã pull repository. Các bộ lọc ngày ở sidebar chỉ áp dụng cho nhánh UCI; trang so sánh khu vực dùng cùng năm 2019 và có bộ chọn quốc gia độc lập.
