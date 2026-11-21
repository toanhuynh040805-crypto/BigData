# Cài đặt và vận hành

## Điều kiện hệ thống

- Windows 10/11 (PowerShell), hoặc Linux/macOS.
- **Python 3.11** và **JDK 17**, biến môi trường JAVA_HOME đúng thư mục JDK.
- RAM khuyến nghị >= 8 GB, dung lượng trống >= 2 GB (Spark + dữ liệu).
- Git và Internet cho lần tải UCI (không cần Internet khi dùng dữ liệu tổng hợp nhân tạo).

## Chạy trên Windows PowerShell

~~~powershell
git clone https://github.com/toanhuynh040805-crypto/BigData.git
cd BigData
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

java -version
python scripts/download_data.py
python scripts/run_pipeline.py --data-provenance uci --master "local[*]"
streamlit run dashboard/app.py
~~~

Có thể xem kết quả ở thư mục data/outputs/ (Git không commit dữ liệu được sinh ra).

## Demo offline bằng dữ liệu TỔNG HỢP (không phải UCI)

~~~powershell
python scripts/generate_sample.py --days 70
python scripts/run_pipeline.py --input data/sample/household_power_consumption.txt --data-provenance synthetic
streamlit run dashboard/app.py
~~~

Để dùng dữ liệu UCI thật sau khi demo offline: \`python scripts/download_data.py --force\`, chạy lại pipeline.

## Lưu trữ Hadoop HDFS (tùy chọn)

HDFS cần cluster Hadoop đang hoạt động, thư mục HDFS có quyền truy cập và Spark có cấu hình Hadoop tương ứng. Ví dụ:

~~~powershell
hdfs dfs -mkdir -p /bigdata/energy/raw
hdfs dfs -put -f data/raw/household_power_consumption.txt /bigdata/energy/raw/
python scripts/run_pipeline.py --input hdfs:///bigdata/energy/raw/household_power_consumption.txt --master "local[*]"
~~~

Dữ liệu đọc có thể ở HDFS, báo cáo CSV/JSON và Parquet được xuất về data/outputs/ **trên máy chạy Spark**. Thay \`--master\` bằng địa chỉ Spark master phù hợp khi đã cấu hình cluster. Dự án không tự cung cấp Hadoop cluster.

## Kiểm thử

~~~powershell
python -m pytest -q
~~~

## Vấn đề thường gặp

- \`JAVA_GATEWAY_EXITED\`: kiểm tra \`JAVA_HOME\` trỏ đúng **JDK 17**, khởi động terminal lại.
- Lỗi phiên bản Python với Spark 3.5: sử dụng Python 3.11 như hướng dẫn.
- \`FileNotFoundError\`: chạy các lệnh từ thư mục gốc repository.
- Dashboard trống: chạy xong \`run_pipeline.py\` trước.
- Dự báo bị bỏ qua: dữ liệu không có đủ ngày liên tục đạt mức bao phủ tối thiểu (\`--min-coverage\`), hoặc mẫu quá ngắn.
- \`hdfs://...\` không đọc được: kiểm tra HADOOP_CONF_DIR / core-site.xml và kết nối NameNode.
- PowerShell không cho activate: có thể chạy trực tiếp \`.venv\Scripts\python.exe\` thay vì thay đổi chính sách bảo mật toàn máy.

## Thông số quan trọng

\`python scripts/run_pipeline.py --help\` hiển thị: \`--input\`, \`--output\`, \`--master\`, \`--expected-minutes-per-day\`, \`--min-coverage\`, \`--min-train-rows\`.
