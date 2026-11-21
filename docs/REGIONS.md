# Khu vực địa lý: nguồn OPSD riêng biệt

Dữ liệu UCI là một hộ gia đình ở Pháp (2006–2010): không có mã khu vực địa lý. Ba nhánh Sub_metering là nhóm thiết bị, không phải quốc gia.

Phần phân tích khu vực sử dụng dữ liệu *độc lập* từ Open Power System Data, Time Series, phiên bản 2020-10-06, nguồn ENTSO-E Transparency.
Nguồn: https://doi.org/10.25832/time_series/2020-10-06
CSV gốc: https://data.open-power-system-data.org/time_series/2020-10-06/time_series_60min_singleindex.csv

Năm so sánh thống nhất: 2019. Năm quốc gia: Đức, Pháp, Ý, Tây Ban Nha, Great Britain.
Đơn vị OPSD là MW (công suất trung bình mỗi giờ) và GWh (điện năng toàn quốc trong khoảng thời gian): tổng MW * 1h / 1000. Đây KHÔNG phải kWh hộ gia đình. So sánh quy mô lưới điện các nước, không đánh giá hiệu suất bình quân đầu người. Thiếu số đo được báo bằng tỷ lệ bao phủ, không nội suy.

Chạy Spark sau khi cài PySpark:
- python scripts/download_regions.py
- python scripts/run_regions.py --year 2019

Workflow Actions sẽ chạy nguồn OPSD gốc để xuất bảng tổng hợp nhỏ trong results/regions. Người dùng Windows có thể xem các bảng đã công bố qua Dashboard, không cần tải tệp gốc 124 MB.

Không dùng kết quả OPSD để huấn luyện hoặc đánh giá Random Forest của UCI.
