# Chạy thực nghiệm trên toàn bộ dữ liệu UCI

Đã cấu hình workflow [Real UCI analysis and deliverables](../.github/workflows/real-uci.yml).

Khi workflow chạy, GitHub Actions:
1. Tải UCI gốc (2.075.259 bản ghi).
2. Tiền xử lý bằng PySpark và xuất Parquet, bảng tổng hợp, mô hình Random Forest, baseline.
3. Xác minh số bản ghi gốc và trạng thái huấn luyện.
4. Xuất Word/PPT từ kết quả chạy **thật**.
5. Lưu tệp kết quả trong GitHub Actions artifact và đưa bản tổng hợp nhỏ vào \`results/uci/\`, báo cáo vào \`reports/\`.

Workflow cũng có thể chạy lại từ GitHub > Actions > Real UCI analysis and deliverables > Run workflow.

Không commit bộ TXT nguồn (~127 MB) lên Git. Word/PPT được xuất dạng **bản nháp**: cần bổ sung thông tin nhóm và người hướng dẫn trước khi nộp. Trường hợp job thất bại, không coi dữ liệu hay báo cáo là đã xác nhận; xem log Actions để sửa nguyên nhân.
