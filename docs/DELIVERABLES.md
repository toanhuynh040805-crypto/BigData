# Tự tạo báo cáo Word và slide PowerPoint từ kết quả Spark

1. Chạy dataset UCI thật: \`python scripts/download_data.py\`
2. Chạy phân tích: \`python scripts/run_pipeline.py --data-provenance uci\`
3. Xuất 2 tài liệu: \`python scripts/build_deliverables.py\`

Kết quả trong thư mục **deliverables/**:
- \`Bao_cao_BigData_Dien_nang.docx\`: Word báo cáo, bảng chất lượng dữ liệu và sai số mô hình, 2 đồ thị từ dữ liệu chạy thật.
- \`Slide_BigData_Dien_nang.pptx\`: 10+ slide thuyết trình gồm mục tiêu, công nghệ, luồng, số liệu, biểu đồ, dự báo và kết luận.
- \`charts/\`: biểu đồ đầu vào để chèn vào báo cáo.

**Bắt buộc chỉnh sửa trước khi nộp:** bìa trường/khoa, giảng viên, hai thành viên, mã số sinh viên; bảng phân công và lịch làm việc **thực tế**; trích dẫn tài liệu cụ thể và ảnh chụp demo. Mã tự tạo tài liệu là tiện ích hỗ trợ, không tự thay thế việc rà soát theo định dạng riêng của giảng viên.

**Cảnh báo:** Nếu chạy với dữ liệu synthetic, Word và PPT sẽ hiện cảnh báo; không sử dụng các số liệu đó làm kết quả thực nghiệm thật. Tập UCI chỉ có **một hộ**, không đại diện khu vực địa lý.
