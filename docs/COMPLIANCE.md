# Ma trận yêu cầu của đề tài 9 (phần hệ thống và kỹ thuật)

Tài liệu đối chiếu bản kế hoạch đồ án Nhập môn Big Data do giảng viên cung cấp. Tập trung các phần kỹ thuật được yêu cầu tiếp tục hoàn thiện; báo cáo Word, PPT, đóng góp hai thành viên và xác minh demo Windows không nằm trong phạm vi cập nhật này.

| Yêu cầu | Minh chứng nguồn và mã thực thi | Trạng thái |
|---|---|---|
| Bài toán thực tế, mục tiêu và phạm vi | README.md, docs/ARCHITECTURE.md | Hoàn thiện nội dung kỹ thuật |
| Công nghệ Big Data phù hợp | Apache Spark DataFrame và Spark MLlib; src/energy_bigdata | Đã chạy UCI thật trên GitHub Actions |
| Dữ liệu nguồn đủ thông tin | UCI có DOI; OPSD có DOI, năm và quy tắc đơn vị | Đã công bố cả 2 nguồn |
| Khảo sát dữ liệu và xử lý lỗi | pipeline.py, metrics.json, quality.json, tests/test_pipeline.py | Đã kiểm thử |
| Dữ liệu lớn, kiến trúc và luồng | Spark → Parquet → aggregations → model; docs/ARCHITECTURE.md | Đã thực hiện |
| Lưu trữ phân tán HDFS | infra/hdfs, scripts/hdfs_demo.sh, hdfs-integration.yml | Cần kiểm tra run HDFS trên Actions; không tự nhận đạt |
| Phân tích theo giờ/ngày | results/uci/hourly_profile.csv, daily.csv | Đã có |
| Phân tích theo khu vực | src/energy_bigdata/regions.py, results/regions/ và 7th dashboard page | Đã chạy Spark thật trên OPSD năm 2019 |
| Hồi quy/dự báo điện năng | Spark MLlib RandomForestRegressor + baseline ngày hôm trước | Đã huấn luyện/đánh giá UCI thật |
| Độ đo và so sánh mô hình | MAE, RMSE, R², 80/20 holdout tuần tự; results/uci/metrics.json | Đã kiểm chứng |
| Trực quan hóa/ứng dụng | Dashboard Streamlit + Plotly 7 màn hình, tests/test_dashboard_app.py | Đã kiểm thử bằng GitHub Actions |
| Độ tin cậy/tính tái lập | GitHub Actions CI, tests/test_published_data.py, docs/SETUP.md | Đã kiểm thử |

## Lưu ý quan trọng về phạm vi

1. **Một hộ và năm quốc gia là hai nguồn độc lập.** UCI (2006–2010) dùng kWh hộ gia đình; OPSD (2019) dùng MW/GWh cấp quốc gia. Không nối cùng một mô hình, không coi các Sub_metering là khu vực.
2. **Dữ liệu theo giờ của UCI và OPSD có ngữ nghĩa thời gian khác nhau.** UCI giữ giờ hiển thị gốc, không có UTC offset; OPSD sử dụng dấu giờ UTC có khai báo.
3. **Dữ liệu thiếu không được ngầm tính bằng 0.** Dashboard thể hiện độ bao phủ, mục tiêu mô hình yêu cầu coverage ≥90%.
4. **Kết quả CI không chứng minh phần cứng Windows của sinh viên đã chạy thành công.** Kiểm thử riêng phần phần mềm trên GitHub.
5. **Word/PPT và bài nộp Classroom không nằm trong thay đổi này**, theo yêu cầu người thực hiện.

## Các phép kiểm thử và nguồn xác thực

- Kết quả UCI: [results/uci](../results/uci), xử lý full-data và mô hình qua workflow .github/workflows/real-uci.yml.
- Kết quả OPSD: [results/regions](../results/regions), workflow .github/workflows/regions.yml; nguồn https://doi.org/10.25832/time_series/2020-10-06.
- HDFS: workflow .github/workflows/hdfs-integration.yml; phải xem trực tiếp trạng thái thành công/thất bại.
- Dashboard 7 trang: .github/workflows/dashboard-ui.yml.
- Bộ unit/integrity tests: .github/workflows/ci.yml.
