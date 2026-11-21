# BigData – Phân tích dữ liệu tiêu thụ điện năng

Đồ án cuối kỳ môn **Nhập môn Big Data** – Đề tài 9.

Hệ thống phân tích dữ liệu tiêu thụ điện của một hộ gia đình bằng **Apache Spark/PySpark**, lưu kết quả Parquet, xây dựng mô hình **Random Forest Regression** để dự báo nhu cầu điện ngày tiếp theo, và trực quan hóa qua **Streamlit**.

> Trạng thái: mã nguồn đang được hoàn thiện. Chưa công bố điểm số mô hình nào là kết quả tái lập được trước khi chạy toàn bộ dữ liệu UCI.

## Cài đặt nhanh (Windows PowerShell)

Yêu cầu **Python 3.11**, **Java 17**, Git.

```powershell
git clone https://github.com/toanhuynh040805-crypto/BigData.git
cd BigData
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_data.py
python scripts/run_pipeline.py
streamlit run dashboard/app.py
```

Nếu muốn kiểm thử mà không cần tải UCI: `python scripts/generate_sample.py --days 70` và `python scripts/run_pipeline.py --input data/raw/household_power_consumption.txt`. Bộ mẫu là dữ liệu **tổng hợp nhân tạo**, không dùng để báo cáo độ chính xác khoa học.

Xem thêm [hướng dẫn đầy đủ](docs/SETUP.md), [kiến trúc](docs/ARCHITECTURE.md), [hướng dẫn demo](docs/DEMO.md) và [dàn ý báo cáo](docs/REPORT_OUTLINE.md).

## Dữ liệu

[UCI Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption), DOI [10.24432/C58K54](https://doi.org/10.24432/C58K54), giấy phép CC BY 4.0. Gồm 2.075.259 thời điểm đo từ tháng 12/2006 tới 11/2010 của **một** hộ gia đình ở Pháp. Các Sub_metering là **nhánh thiết bị trong hộ**, không phải vùng địa lý.

## Mục tiêu kỹ thuật

- Parse ngày dạng `d/M/yyyy` và `dd/MM/yyyy`; giữ nguyên **giờ hiển thị tại nguồn** khi nhóm theo ngày, không tự động suy diễn timezone/DST.
- Loại bản ghi thiếu công suất, thời gian sai và trùng thời điểm; thống kê chất lượng.
- Tổng hợp kWh từ công suất trung bình mỗi phút: `sum(Global_active_power)/60`, theo ngày/tháng/giờ; thống kê riêng ba nhánh sub-metering (Wh → kWh).
- Học từ các ngày **trước ngày dự báo** bằng lag-1, lag-7, rolling-7 và lịch; chia train/test theo thời gian, so sánh baseline ngày hôm trước.
- Xuất Parquet cùng các CSV/JSON nhỏ cho dashboard.

Dữ liệu 1 phút đo thiếu hoặc trùng sẽ ảnh hưởng tới ước lượng kWh; pipeline báo tỷ lệ bao phủ, không giả định rằng ngày thiếu mẫu có điện năng bằng 0.

## Tác giả và phạm vi

Repository phục vụ mục đích học tập. Không áp dụng kết quả của một hộ gia đình để khái quát cho toàn bộ khu vực. Quy trình hỗ trợ đường dẫn đầu vào HDFS nếu môi trường Hadoop đã được cấu hình; không cần Hadoop để chạy demo Spark local.
