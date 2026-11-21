# BigData – Phân tích dữ liệu tiêu thụ điện năng

Đồ án cuối kỳ môn **Nhập môn Big Data** – Đề tài 9.

Hệ thống phân tích dữ liệu tiêu thụ điện của một hộ gia đình bằng **Apache Spark/PySpark**, lưu kết quả Parquet, xây dựng mô hình **Random Forest Regression** để dự báo nhu cầu điện ngày tiếp theo, và trực quan hóa qua **Streamlit**.

> Trạng thái: pipeline UCI thật và bộ kiểm thử đã chạy thành công trên GitHub Actions; dashboard 6 màn hình đang được cập nhật để phục vụ demo đồ án.

## Cài đặt nhanh (Windows PowerShell)

Yêu cầu **Python 3.11**, **Java 17**, Git.

```powershell
git clone https://github.com/toanhuynh040805-crypto/BigData.git
cd BigData
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/download_data.py
python scripts/run_pipeline.py --data-provenance uci
streamlit run dashboard/app.py
```

Nếu muốn kiểm thử mà không cần tải UCI: `python scripts/generate_sample.py --days 70` và `python scripts/run_pipeline.py --input data/sample/household_power_consumption.txt --data-provenance synthetic`. Bộ mẫu là dữ liệu **tổng hợp nhân tạo**, không dùng để báo cáo độ chính xác khoa học.

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

## Kết quả thực nghiệm đã công bố

GitHub Actions đã chạy trực tiếp trên dữ liệu UCI gốc và lưu [bảng kết quả](results/uci/) cùng [báo cáo Word và slide PowerPoint dạng bản nháp](reports/).

- 2.075.259 bản ghi ban đầu; 2.049.280 bản ghi có công suất hợp lệ; 25.979 bản ghi thiếu công suất.
- Dữ liệu dùng cho mô hình: 1.362 ngày; train 1.089 ngày; test 273 ngày.
- Random Forest: MAE **3,9731**, RMSE **5,4152** kWh/ngày; baseline hôm trước: MAE **5,0621** kWh/ngày.
- Dự báo cho **26/11/2010** trên lịch sử đủ dữ liệu: khoảng **29,32 kWh**. Không phải dự báo thời điểm hiện tại.

Dashboard có 6 màn hình với đồ thị ngày/tháng, cao điểm, ba nhánh thiết bị, bất thường IQR, dự báo AI, chất lượng dữ liệu và xuất bảng CSV/JSON. Có thể mở từ kết quả UCI đã lưu trên GitHub, KHÔNG cần cài Java/PySpark để xem biểu đồ. Hướng dẫn chi tiết tại [docs/DASHBOARD.md](docs/DASHBOARD.md).

Các file Word/PPT do hệ thống sinh **chưa điền thông tin giảng viên, nhóm và phân công thực tế**; cần rà soát định dạng, nội dung trước khi nộp.

## Mở Dashboard trên ổ E: (nhẹ, không cần PySpark)

~~~powershell
cd E:\BigData
git pull origin main
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
~~~

Nếu thiếu thư viện, cài tối thiểu: `.\.venv\Scripts\python.exe -m pip install streamlit plotly pandas --timeout 300 --retries 10`. Chọn “UCI thật · Kết quả GitHub” ở thanh bên để demo số liệu đã kiểm thử.

**Giao diện đầy đủ:** [Ảnh minh chứng và hướng dẫn demo](docs/DASHBOARD.md) · [GitHub Actions](https://github.com/toanhuynh040805-crypto/BigData/actions).
