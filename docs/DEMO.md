# Kịch bản demo cuối kỳ (5–8 phút)

1. **Dữ liệu đầu vào**: giới thiệu dataset UCI, 2.075.259 quan sát theo phút, các cột Date/Time/công suất và ba sub-metering.
2. **Big Data**: trình bày luồng Spark DataFrame, thống kê bản ghi hỏng/trùng, Parquet theo năm-tháng. Có thể minh họa đọc bằng HDFS nếu lớp có cluster.
3. **Phân tích**: xem dashboard xu hướng ngày/tháng, công suất theo giờ và tỷ trọng ba nhánh thiết bị.
4. **Dự báo**: giải thích lag-1, lag-7, trung bình 7 ngày trước; phân chia train/test theo ngày. So sánh MAE/RMSE Random Forest và baseline một ngày trước.
5. **Giá trị/giới hạn**: minh họa giờ cao điểm, lượng điện kỳ gần nhất và giới hạn một hộ gia đình.

## Lệnh demo

~~~powershell
python scripts/download_data.py
python scripts/run_pipeline.py --data-provenance uci
streamlit run dashboard/app.py
~~~

Nếu Internet không ổn: chuẩn bị trước dữ liệu bằng \`download_data.py\` và chạy hoàn tất pipeline trước buổi báo cáo. Không công bố số liệu tổng hợp nhân tạo như kết quả trên dữ liệu thực.

## Ảnh và số liệu đưa vào slide

Chụp màn hình các tab của dashboard sau khi chạy thật; lấy bảng \`data/outputs/metrics.json\` để ghi giá trị mô hình. Số liệu thực nghiệm từ một lần chạy trước (RF MAE 4,0937 và RMSE 5,5422) **không** được chèn như kết quả tái lập được trừ khi pipeline hiện tại tạo lại kết quả tương ứng.
