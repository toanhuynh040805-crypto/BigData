"""Create a Word report draft + PowerPoint slides FROM saved real pipeline outputs.

Important: output contains a visible SYNTHETIC warning if generated from the
offline sample. The report is a reviewed draft: fill in actual team contribution
and instructor information before academic submission.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt as DPt
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
NAVY = RGBColor(20, 42, 69)
TEAL = RGBColor(0, 131, 141)


def read_inputs(directory: Path):
    required = ("quality.json", "metrics.json", "daily.csv", "monthly.csv")
    missing = [p for p in required if not (directory / p).is_file()]
    if missing:
        raise FileNotFoundError("Chạy pipeline trước. Thiếu: " + ", ".join(missing))
    quality = json.loads((directory / "quality.json").read_text(encoding="utf-8"))
    metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
    daily = pd.read_csv(directory / "daily.csv", parse_dates=["date"])
    monthly = pd.read_csv(directory / "monthly.csv")
    return quality, metrics, daily, monthly


def chart_assets(directory: Path, daily: pd.DataFrame, monthly: pd.DataFrame) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"
    images = {}
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(daily["date"], daily["energy_kwh"], linewidth=0.9)
    ax.set(xlabel="Ngày", ylabel="Điện năng (kWh)", title="Tiêu thụ điện theo ngày")
    fig.autofmt_xdate()
    fig.tight_layout()
    images["daily"] = directory / "daily.png"
    fig.savefig(images["daily"], dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(monthly["month"], monthly["energy_kwh"])
    if len(monthly) > 12:
        step = max(1, len(monthly) // 12)
        for i, label in enumerate(ax.get_xticklabels()):
            if i % step:
                label.set_visible(False)
    ax.tick_params(axis="x", labelrotation=45)
    ax.set(xlabel="Tháng", ylabel="Điện năng (kWh)", title="Tổng điện năng theo tháng")
    fig.tight_layout()
    images["monthly"] = directory / "monthly.png"
    fig.savefig(images["monthly"], dpi=150)
    plt.close(fig)
    return images


def add_table(doc: Document, headings: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1, cols=len(headings))
    table.style = "Table Grid"
    for i, heading in enumerate(headings):
        table.rows[0].cells[i].text = heading
    for values in rows:
        cells = table.add_row().cells
        for i, value in enumerate(values):
            cells[i].text = str(value)


def build_word(
    output: Path, quality: dict, metrics: dict,
    daily: pd.DataFrame, monthly: pd.DataFrame, images: dict,
) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.3)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = DPt(12)
    normal.paragraph_format.space_after = DPt(7)
    for style in ("Title", "Heading 1", "Heading 2"):
        doc.styles[style].font.name = "Times New Roman"
        doc.styles[style].font.color.rgb = None

    cover = doc.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cover.add_run("BÁO CÁO ĐỒ ÁN CUỐI KỲ\nMÔN NHẬP MÔN BIG DATA\n")
    run.bold = True
    run.font.size = DPt(18)
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("\nĐỀ TÀI 9\nPHÂN TÍCH DỮ LIỆU TIÊU THỤ ĐIỆN NĂNG")
    run.bold = True
    run.font.size = DPt(20)
    doc.add_paragraph("\nGiảng viên hướng dẫn: [Điền tên giảng viên]")
    doc.add_paragraph("Nhóm thực hiện (2 sinh viên): [Điền tên và mã sinh viên]")
    doc.add_paragraph("Năm học: 2026–2027")
    provenance = metrics.get("data_provenance", quality.get("data_provenance", "other"))
    if provenance != "uci":
        doc.add_paragraph(
            "CẢNH BÁO: DỮ LIỆU CHƯA XÁC NHẬN LÀ UCI THẬT. "
            "Không sử dụng các con số này làm kết quả nghiên cứu để nộp."
        )
    doc.add_page_break()

    doc.add_heading("LỊCH VÀ PHÂN CÔNG CÔNG VIỆC NHÓM", 1)
    doc.add_paragraph(
        "Bảng dưới đây là khung kế hoạch tham khảo. Nhóm cần ghi lại công việc và "
        "mức đóng góp thực tế của từng thành viên trước khi nộp."
    )
    add_table(doc, ["Tuần", "Nội dung dự kiến", "Người phụ trách"], [
        ["1–3", "Chọn đề tài, phân công, lập kế hoạch", "[Điền]"],
        ["4–5", "Tìm hiểu Spark, công nghệ, baseline", "[Điền]"],
        ["6–7", "Khảo sát, tiền xử lý, báo cáo tiến độ", "[Điền]"],
        ["8–9", "Mô hình, đánh giá, dashboard, tài liệu", "[Điền]"],
        ["10", "Kiểm thử, hoàn thiện, thuyết trình", "[Điền]"],
    ])
    doc.add_heading("1. GIỚI THIỆU ĐỀ TÀI", 1)
    doc.add_paragraph(
        "Quản lý tiêu thụ điện năng đòi hỏi khả năng phát hiện chu kỳ sử dụng, "
        "nhận diện các giai đoạn tiêu thụ cao và dự báo nhu cầu ngắn hạn. "
        "Đề tài áp dụng Apache Spark để xử lý tập dữ liệu có độ phân giải một phút, "
        "kết hợp các thống kê mô tả, hồi quy và dashboard hỗ trợ phân tích."
    )
    doc.add_paragraph(
        "Mục tiêu gồm: (i) làm sạch dữ liệu và đánh giá chất lượng; "
        "(ii) tổng hợp điện năng theo giờ/ngày/tháng và theo nhánh thiết bị; "
        "(iii) xây dựng baseline và Random Forest dự báo một ngày tiếp theo; "
        "(iv) đánh giá sai số bằng dữ liệu kiểm tra theo thời gian."
    )
    doc.add_paragraph(
        "Phạm vi: một hộ gia đình tại Sceaux (Pháp), giai đoạn 12/2006–11/2010. "
        "Kết quả không đại diện cho một quận, tỉnh hoặc toàn quốc."
    )
    doc.add_heading("2. CƠ SỞ LÝ THUYẾT", 1)
    doc.add_paragraph(
        "Apache Spark là hệ thống xử lý phân tán; Spark DataFrame hỗ trợ "
        "biến đổi dữ liệu, tổng hợp và tối ưu truy vấn. Parquet là định dạng "
        "lưu trữ dạng cột giúp quản lý dữ liệu sạch và hỗ trợ truy vấn phân tích."
    )
    doc.add_paragraph(
        "Random Forest Regression tổng hợp dự đoán của nhiều cây quyết định. "
        "Với dữ liệu chuỗi thời gian, bài toán cần tránh rò rỉ tương lai: "
        "đặc trưng lag-1, lag-7 và trung bình bảy ngày trước được tạo từ lịch sử, "
        "không chứa lượng điện của chính ngày đích."
    )
    doc.add_paragraph(
        "MAE = trung bình |giá trị thật − dự đoán|; RMSE = căn bậc hai trung bình "
        "bình phương sai số; R² thể hiện mức độ giải thích biến thiên mục tiêu. "
        "Baseline là phương pháp dự báo ngày hiện tại bằng giá trị ngày trước đó."
    )
    doc.add_heading("3. XÂY DỰNG HỆ THỐNG VÀ DỮ LIỆU", 1)
    doc.add_paragraph(
        "Nguồn: UCI Individual Household Electric Power Consumption, "
        "2.075.259 quan sát theo phút. File văn bản phân tách dấu chấm phẩy; "
        "Date và Time đứng trước các thông số điện năng/công suất. "
        "Các bản ghi thiếu dữ liệu thể hiện bằng giá trị trống hoặc '?'."
    )
    doc.add_paragraph(
        "Luồng dữ liệu: UCI TXT → PySpark parse/clean → Parquet phân vùng năm-tháng "
        "→ tổng hợp → tạo đặc trưng → Random Forest → dashboard Streamlit."
    )
    doc.add_paragraph(
        "Quy đổi: tổng điện năng toàn hộ (kWh) ≈ tổng Global_active_power (kW) / 60 "
        "với mẫu cách đều một phút. Ba Sub_metering đo năng lượng Wh theo phút, "
        "được cộng rồi chia 1000. Chúng là nhánh thiết bị trong nhà, không phải khu vực địa lý."
    )
    doc.add_paragraph(
        "Mốc thời gian nguồn không chứa timezone hoặc UTC offset. "
        "Hệ thống xử lý theo giờ hiển thị gốc; ngày có thiếu mẫu được gắn tỷ lệ "
        "bao phủ, không nội suy điện năng bằng 0. Bản ghi trùng thời điểm được "
        "ưu tiên theo mức đầy đủ trường và loại trùng để tránh đếm đôi."
    )
    doc.add_heading("4. KẾT QUẢ THỰC NGHIỆM", 1)
    add_table(doc, ["Chỉ tiêu", "Giá trị từ pipeline"], [
        ["Bản ghi gốc", f"{quality.get('raw_rows', 0):,}"],
        ["Bản ghi sạch duy nhất", f"{quality.get('clean_unique_rows', 0):,}"],
        ["Bản ghi bị loại", f"{quality.get('invalid_rows', 0):,}"],
        ["Bản ghi trùng", f"{quality.get('duplicates_removed', 0):,}"],
        ["Số ngày có dữ liệu", str(len(daily))],
        ["Tổng điện năng quan sát được", f"{daily['energy_kwh'].sum():,.2f} kWh"],
    ])
    doc.add_paragraph("Hình 4.1. Điện năng tiêu thụ theo ngày (nguồn: kết quả pipeline Spark).")
    doc.add_picture(str(images["daily"]), width=Cm(15.5))
    doc.add_paragraph("Hình 4.2. Điện năng tiêu thụ theo tháng (nguồn: kết quả pipeline Spark).")
    doc.add_picture(str(images["monthly"]), width=Cm(15.5))
    doc.add_heading("5. DỰ BÁO VÀ ĐÁNH GIÁ", 1)
    if metrics.get("status") == "trained":
        rf = metrics["random_forest"]
        baseline = metrics["baseline_previous_day"]
        doc.add_paragraph(
            f"Tập train: {metrics['train_rows']} ngày; tập test: {metrics['test_rows']} ngày, "
            f"từ {metrics['test_start']} đến {metrics['test_end']}. "
            "Phân chia tuần tự theo thời gian (80/20), dự báo một bước."
        )
        add_table(doc, ["Mô hình", "MAE (kWh/ngày)", "RMSE (kWh/ngày)", "R²"], [
            ["Random Forest", f"{rf['mae']:.4f}", f"{rf['rmse']:.4f}", f"{rf['r2']:.4f}" if rf["r2"] is not None else "N/A"],
            ["Ngày hôm trước", f"{baseline['mae']:.4f}", f"{baseline['rmse']:.4f}", f"{baseline['r2']:.4f}" if baseline["r2"] is not None else "N/A"],
        ])
        result = (
            "Random Forest có MAE thấp hơn baseline trên tập kiểm tra."
            if rf["mae"] < baseline["mae"]
            else "Random Forest không cải thiện MAE so với baseline trong thực nghiệm này."
        )
        doc.add_paragraph(result + " Cần đối chiếu các đặc trưng và chất lượng dữ liệu trước khi kết luận.")
    else:
        doc.add_paragraph(
            "Chưa đủ dữ liệu để huấn luyện/đánh giá mô hình theo yêu cầu bao phủ dữ liệu."
        )
    doc.add_heading("6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", 1)
    doc.add_paragraph(
        "Đồ án xây dựng luồng xử lý Spark, chuẩn hóa dữ liệu điện năng theo phút, "
        "lưu Parquet, thống kê tiêu thụ và thử nghiệm dự báo bằng Spark MLlib. "
        "Giá trị thực tiễn chính là hỗ trợ nhận diện xu hướng tiêu thụ trong lịch sử."
    )
    doc.add_paragraph(
        "Hạn chế: một hộ; dữ liệu đã cũ; mẫu theo phút có thể thiếu; thiếu múi giờ gốc, "
        "giá điện và thông tin thời tiết; chưa thử nhiều mô hình. "
        "Hướng phát triển: bổ sung nhiều hộ, phân tích streaming, dự báo nhiều bước, "
        "kết hợp biến thời tiết và triển khai hệ thống thực tế."
    )
    doc.add_heading("TÀI LIỆU THAM KHẢO", 1)
    doc.add_paragraph(
        "[1] G. Hebrail và A. Berard, Individual Household Electric Power Consumption, "
        "UCI Machine Learning Repository, DOI: 10.24432/C58K54, CC BY 4.0."
    )
    doc.add_paragraph("[2] Apache Spark Documentation, https://spark.apache.org/docs/latest/.")
    doc.add_paragraph("[3] Streamlit Documentation, https://docs.streamlit.io/.")
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)


def slide_text(slide, title: str, lines: list[str]) -> None:
    box = slide.shapes.add_textbox(Inches(0.75), Inches(0.55), Inches(11.8), Inches(0.8))
    p = box.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(29)
    p.font.bold = True
    p.font.color.rgb = NAVY
    body = slide.shapes.add_textbox(Inches(0.95), Inches(1.55), Inches(11.3), Inches(5.3))
    body.text_frame.word_wrap = True
    for index, line in enumerate(lines):
        p = body.text_frame.paragraphs[0] if index == 0 else body.text_frame.add_paragraph()
        p.text = "• " + line
        p.level = 0
        p.font.size = Pt(20)
        p.font.color.rgb = NAVY
        p.space_after = Pt(18)


def build_slides(
    output: Path, quality: dict, metrics: dict,
    daily: pd.DataFrame, images: dict,
) -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    layout = prs.slide_layouts[6]
    def new(title: str, lines: list[str], picture: Path | None = None):
        slide = prs.slides.add_slide(layout)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(250, 252, 253)
        slide_text(slide, title, lines)
        if picture:
            # Replace body space with a large chart to avoid text overlap.
            for shape in list(slide.shapes):
                if shape.has_text_frame and shape.top >= Inches(1.5):
                    shape._element.getparent().remove(shape._element)
            slide.shapes.add_picture(str(picture), Inches(1.0), Inches(1.58), width=Inches(11.2))
        return slide

    new("BIG DATA | PHÂN TÍCH ĐIỆN NĂNG", [
        "Đề tài 9 – Nhập môn Big Data · Apache Spark / PySpark",
        "Dữ liệu: UCI Household Electric Power Consumption",
        "Nhóm thực hiện: [Bổ sung 2 sinh viên và giảng viên]",
    ])
    provenance = metrics.get("data_provenance", quality.get("data_provenance"))
    if provenance != "uci":
        new("LƯU Ý VỀ NGUỒN DỮ LIỆU", [
            "Dữ liệu hiện tại chưa được xác minh là bản UCI gốc.",
            "Nếu đang chạy synthetic, các kết quả chỉ để demo hệ thống.",
            "Chạy download_data.py và pipeline --data-provenance uci để lấy số liệu báo cáo.",
        ])
    new("1. BÀI TOÁN VÀ MỤC TIÊU", [
        "Phân tích thói quen tiêu thụ điện, giờ cao điểm và xu hướng theo thời gian.",
        "Xử lý dữ liệu đo theo phút bằng Apache Spark.",
        "Dự báo mức tiêu thụ điện ngày kế tiếp bằng Random Forest.",
        "Trực quan hóa và đánh giá sai số so với baseline.",
    ])
    new("2. BỘ DỮ LIỆU UCI", [
        "Một hộ gia đình tại Sceaux, Pháp (12/2006–11/2010).",
        "2.075.259 quan sát theo phút; Date, Time và bảy biến đo điện.",
        "Global_active_power (kW); ba sub-metering đo Wh theo phút.",
        "Ba nhánh là nhóm thiết bị, không phải ba địa bàn địa lý.",
    ])
    new("3. KIẾN TRÚC XỬ LÝ SPARK", [
        "UCI TXT / HDFS (tùy chọn) → Spark DataFrame.",
        "Chuẩn hóa ngày giờ, lọc thiếu/trùng và đo chất lượng.",
        "Parquet phân vùng theo năm-tháng → nhóm ngày/tháng/giờ.",
        "Spark MLlib → CSV/JSON → Streamlit Dashboard.",
    ])
    new("4. TIỀN XỬ LÝ DỮ LIỆU", [
        f"Dòng nguồn: {quality.get('raw_rows', 0):,}.",
        f"Dòng sạch duy nhất: {quality.get('clean_unique_rows', 0):,}.",
        f"Dòng bị loại: {quality.get('invalid_rows', 0):,}; dòng trùng: {quality.get('duplicates_removed', 0):,}.",
        "Giữ giờ nguồn; kiểm tra coverage thay vì tự nội suy ngày thiếu dữ liệu.",
    ])
    new("5. ĐIỆN NĂNG THEO NGÀY", [], images["daily"])
    new("6. ĐIỆN NĂNG THEO THÁNG", [], images["monthly"])
    new("7. DỰ BÁO BẰNG RANDOM FOREST", [
        "Đặc trưng: lag-1, lag-7, trung bình 7 ngày trước và ngày/tháng.",
        "Loại ngày có tỷ lệ bao phủ thấp; tạo lịch liên tục trước khi lag.",
        "Chia train/test theo thứ tự thời gian 80%/20%.",
        "So sánh baseline dự báo bằng lượng điện hôm trước.",
    ])
    if metrics.get("status") == "trained":
        rf = metrics["random_forest"]
        base = metrics["baseline_previous_day"]
        lines = [
            f"Train: {metrics['train_rows']} ngày · Test: {metrics['test_rows']} ngày.",
            f"Random Forest — MAE {rf['mae']:.3f}; RMSE {rf['rmse']:.3f} kWh/ngày.",
            f"Baseline — MAE {base['mae']:.3f}; RMSE {base['rmse']:.3f} kWh/ngày.",
            "Kết quả là của tập dữ liệu đã chạy, không phải dự báo cho năm hiện tại.",
        ]
    else:
        lines = ["Dữ liệu chưa đủ điều kiện để huấn luyện và báo cáo độ đo."]
    new("8. ĐÁNH GIÁ KẾT QUẢ", lines)
    new("9. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", [
        "Đã xây dựng pipeline Spark, phân tích tiêu thụ và mô hình dự báo ngày tiếp theo.",
        "Giới hạn: một hộ, dữ liệu cũ, thiếu mẫu, thiếu offset giờ và biến thời tiết.",
        "Phát triển: nhiều hộ, dữ liệu thời gian thực, mô hình chuỗi thời gian nâng cao.",
        "Nguồn: Hebrail & Berard, UCI, DOI 10.24432/C58K54.",
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/outputs"))
    parser.add_argument("--output", type=Path, default=Path("deliverables"))
    args = parser.parse_args()
    quality, metrics, daily, monthly = read_inputs(args.input)
    chart_dir = args.output / "charts"
    images = chart_assets(chart_dir, daily, monthly)
    word = args.output / "Bao_cao_BigData_Dien_nang.docx"
    slide = args.output / "Slide_BigData_Dien_nang.pptx"
    build_word(word, quality, metrics, daily, monthly, images)
    build_slides(slide, quality, metrics, daily, images)
    print(f"Word report: {word}")
    print(f"PowerPoint: {slide}")
    if metrics.get("data_provenance") != "uci":
        print("WARNING: Data is not tagged as UCI; do not submit synthetic results.")


if __name__ == "__main__":
    main()
