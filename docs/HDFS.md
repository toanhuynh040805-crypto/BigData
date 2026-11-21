# Apache Hadoop HDFS: phân tán hai DataNodes

Đã bổ sung hạ tầng tùy chọn dùng Docker Compose: một NameNode, hai DataNodes lưu dữ liệu dạng block, replication=2 và một Spark client cùng mạng Docker. Đây là tính năng triển khai thật để kiểm chứng hệ thống xử lý dữ liệu lớn, không phải giao diện giả. **Chỉ coi HDFS đã kiểm chứng khi GitHub Actions HDFS distributed integration báo thành công.**

## Yêu cầu môi trường

Docker Desktop với Linux Engine/WSL2 hoặc Docker Engine trên Linux, Compose v2, mạng đủ nhanh tải image Docker (lần đầu có thể rất lớn). Không cần cài Docker để chỉ mở Dashboard UCI trên Windows; không cần Apache Hive. Demo chạy trên Windows cá nhân không nằm trong phạm vi thực hiện hiện tại.

## Lệnh triển khai HDFS

Mở PowerShell tại thư mục gốc repository. Trước tiên tạo bộ UCI thực bằng download_data.py (Python 3.11, không cần Java cho riêng bước tải).

1. docker compose -f infra/hdfs/compose.yaml up -d namenode datanode1 datanode2
2. docker compose -f infra/hdfs/compose.yaml exec namenode hdfs dfsadmin -report
3. python scripts/download_data.py
4. docker compose -f infra/hdfs/compose.yaml cp data/raw/household_power_consumption.txt namenode:/tmp/household.txt
5. docker compose -f infra/hdfs/compose.yaml exec namenode hdfs dfs -mkdir -p /bigdata/energy/raw
6. docker compose -f infra/hdfs/compose.yaml exec namenode hdfs dfs -put -f /tmp/household.txt /bigdata/energy/raw/household_power_consumption.txt
7. docker compose -f infra/hdfs/compose.yaml exec namenode hdfs dfs -ls /bigdata/energy/raw
8. docker compose -f infra/hdfs/compose.yaml --profile spark up -d --build spark-client
9. docker compose -f infra/hdfs/compose.yaml --profile spark exec spark-client python scripts/run_pipeline.py --input hdfs://namenode:9000/bigdata/energy/raw/household_power_consumption.txt --output data/outputs/hdfs --master local[2] --data-provenance uci

Web admin NameNode: http://localhost:9870 (chỉ bind trên localhost). Với dữ liệu tổng hợp được tạo bằng generate_sample.py, bắt buộc chọn --data-provenance synthetic, không được gắn nhãn UCI thật.

Bảo vệ dữ liệu: volumes bền vững khi dùng docker compose down, nhưng mất dữ liệu nếu dùng down -v. Cluster phục vụ học tập: không có Kerberos, không có HA/YARN hoặc tính năng sản xuất.

## Kiểm thử tái lập trên GitHub

.github/workflows/hdfs-integration.yml tạo bộ mẫu nhân tạo, chạy NameNode và hai DataNodes, nạp tệp nguồn, dùng fsck kiểm chứng block HDFS khỏe mạnh, rồi xây dựng container Spark đọc từ URI hdfs:// và kiểm tra bản ghi/Parquet. Log ở GitHub Actions phân biệt rõ kết quả thực thi với phần tài liệu hướng dẫn. Kết quả kiểm thử không thay thế việc trình diễn trên Windows thực tế.


## Định tuyến đầu ra Parquet rõ ràng

Khi Spark đọc HDFS, Hadoop có thể đặt fs.defaultFS thành HDFS. Kể cả đường dẫn đầu ra không có hdfs://, Spark có thể tự ghi vào HDFS trong khi Python ghi CSV/JSON vào ổ cục bộ. Pipeline hiện buộc Parquet cục bộ về URI file:// và lưu mô hình MLlib tại file:// cho tính nhất quán. 

Khi muốn lưu song song dữ liệu sạch lên hệ phân tán, truyền thêm tùy chọn --hdfs-parquet-output hdfs://namenode:9000/bigdata/energy/processed/clean_parquet. Workflow CI sẽ kiểm tra file _SUCCESS của Parquet trên HDFS và thư mục clean_parquet trên volume cục bộ, giúp chứng minh hai loại lưu trữ.

## Kết quả tích hợp thực tế đã chạy

Run thành công: [HDFS distributed integration](https://github.com/toanhuynh040805-crypto/BigData/actions/runs/44882806655). Đã kiểm chứng NameNode + 2 DataNodes, fsck HEALTHY, Spark đọc 21.600 quan sát synthetic qua HDFS và ghi Parquet cả cục bộ lẫn HDFS. Kết quả này chỉ thuộc runner GitHub Actions, không phải chứng minh đã chạy trên máy Windows cá nhân.
