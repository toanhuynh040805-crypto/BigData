# Kiến trúc và định nghĩa dữ liệu

~~~text
UCI TXT (2.075.259 bản ghi theo phút, một hộ gia đình)
   | download_data.py, có thể nạp lên HDFS
   v
PySpark DataFrame (Spark local hoặc Spark cluster)
   | Parse d/M/yyyy + hh:mm:ss; ép kiểu số; lọc null/âm; loại trùng thời điểm
   | Ghi thống kê chất lượng; giữ giờ "wall clock" như bản gốc
   v
Parquet phân vùng theo year/month (data/outputs/clean_parquet/)
   |
   +-- Tổng hợp theo ngày, tháng, giờ trong ngày + 3 sub-metering
   |        |
   |        +--> CSV nhỏ dùng cho dashboard Streamlit
   |
   +-- Bảng ngày liên tục, kiểm tra coverage, đặc trưng lag-1/lag-7/rolling-7
            |
            +--> Chia train/test tuần tự theo ngày (không random split)
            +--> Baseline: lặp lại lượng điện ngày hôm trước
            +--> Spark MLlib RandomForestRegressor
            +--> Đánh giá MAE, RMSE, R² trên tập kiểm tra
            +--> Huấn luyện lại toàn bộ dữ liệu để dự báo NGÀY TIẾP THEO
            +--> CSV/JSON cho dashboard
~~~

## Quy tắc dữ liệu

- \`Global_active_power\`: kW trung bình mỗi phút; \`energy_kwh = sum(kW) / 60\` cho mẫu mỗi phút hợp lệ. Không phải tổng công suất kW.
- \`Sub_metering_1/2/3\`: Wh trong phút; cộng Wh rồi chia 1000 để đổi kWh.
- Dữ liệu một hộ tại Sceaux, Pháp. Ba nhánh thiết bị không phải vùng địa lý (1: bếp; 2: phòng giặt; 3: bình nước nóng & điều hòa).
- \`coverage = unique_valid_minutes / 1440\` đối với ngày 24 giờ theo dấu thời gian gốc, có chặn tối đa 1; đó là chỉ báo, không phải năng lượng đã bù mẫu thiếu.
- Bản gốc không khai báo timezone; dùng UTC làm timezone nội bộ Spark chỉ để giữ nguyên giờ hiển thị, **không** gán cho dữ liệu ý nghĩa UTC và không tự sửa DST. Nếu trùng thời điểm địa phương khi đổi giờ, một mẫu được giữ; chất lượng ghi số bản ghi trùng. Nếu ứng dụng cần giờ thực tuyệt đối thì cần metadata timezone/offset chưa có trong bộ dữ liệu.
- Mô hình không sử dụng năng lượng của ngày đích làm đặc trưng: rolling window chỉ chứa **7 ngày trước**. Các ngày thiếu coverage không đưa vào học; lịch ngày đầy đủ để lag-7 thực sự là 7 ngày trước.
- Chia dữ liệu theo thứ tự thời gian nhằm tránh rò rỉ tương lai. Dự báo ở đây là **một bước: ngày tiếp theo**, không phải dự báo dài hạn.

## Giới hạn

Chỉ có một hộ nên không thể suy luận theo tỉnh/thành/khu vực địa lý. Các ngày thiếu dữ liệu có thể làm méo ước lượng điện năng; không nội suy bừa. Mô hình chưa có biến ngoại sinh như thời tiết, ngày lễ và giá điện. Số liệu dự báo là kết quả mô hình thực nghiệm, không phải hóa đơn điện.
