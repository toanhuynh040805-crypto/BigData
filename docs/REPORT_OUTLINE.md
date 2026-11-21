# Dàn ý báo cáo cuối kỳ theo yêu cầu giảng viên

> Đây là bản nội dung nền cần cập nhật số liệu, ảnh màn hình và nhận xét thực nghiệm sau khi chạy đủ bộ dữ liệu thật. Không dùng số liệu demo nhân tạo làm kết quả nghiên cứu.

## Trang bìa
Trường, khoa, học phần Nhập môn Big Data, đề tài 9 – Phân tích dữ liệu tiêu thụ điện năng, giảng viên, 2 sinh viên, năm học.

## Lịch làm việc nhóm và công việc từng thành viên
Lập bảng theo từng tuần: lập kế hoạch; tìm hiểu Spark; khảo sát dữ liệu; xây dựng ETL; mô hình và đánh giá; dashboard; demo và báo cáo. Ghi rõ người thực hiện/đóng góp thực tế.

## Mục lục

## 1. Giới thiệu đề tài
Bối cảnh quản lý điện năng, mục tiêu phân tích theo ngày/tháng/giờ, dự báo ngày tiếp theo, phạm vi một hộ gia đình từ 2006–2010, ý nghĩa tiết kiệm năng lượng.

## 2. Cơ sở lý thuyết
- Big Data và 5V, xử lý phân tán và Apache Spark.
- Spark DataFrame, Spark SQL, Parquet; HDFS như tùy chọn lưu trữ phân tán.
- Phân tích chuỗi thời gian, lag features, Random Forest Regression.
- Chia train/test tuần tự và các độ đo MAE, RMSE, R².
- Nguyên tắc bảo đảm chất lượng dữ liệu và tránh rò rỉ thông tin tương lai.

## 3. Xây dựng hệ thống và trực quan hóa
- Mô tả nguồn dữ liệu UCI, schema 9 trường và đơn vị đo, nguồn trích dẫn.
- Luồng xử lý: đọc TXT -> parse -> lọc thiếu/trùng -> Parquet -> tổng hợp -> đặc trưng -> dự báo -> dashboard.
- Công thức kWh = tổng công suất kW theo phút / 60; Sub_metering Wh / 1000.
- Kết quả thống kê chất lượng trích từ quality.json.
- Các biểu đồ ngày/tháng/giờ và ba nhánh thiết bị; ảnh dashboard thật.
- Tham số mô hình, phân tách tập train/test, bảng so sánh baseline và Random Forest từ metrics.json.
- Nhận xét điểm cao điểm/tiêu thụ theo chu kỳ và hạn chế của cách tính khi thiếu mẫu.

## 4. Kết luận và hướng phát triển
Tổng kết những gì đã cài đặt và kiểm thử, hạn chế một hộ, thiếu dữ liệu, thiếu timezone/offset và biến ngoại sinh. Hướng phát triển: dữ liệu đa hộ, thời tiết, so sánh nhiều mô hình, giám sát theo thời gian thực.

## 5. Tài liệu tham khảo
- Hebrail, G. & Berard, A. (2006). Individual Household Electric Power Consumption, UCI. DOI: 10.24432/C58K54.
- Apache Spark Documentation (Spark SQL, DataFrame, MLlib).
- Streamlit Documentation.

## 6. Phụ lục
Lệnh cài đặt, cấu hình Java/Python, mô tả file, lệnh demo, test cases và minh chứng chạy thật.

## Hồ sơ nộp
Source code repository + Word báo cáo chính thức + PPT + demo, đúng yêu cầu giảng viên. Tài liệu Markdown này **chưa phải file Word/PPT hoàn chỉnh**.
