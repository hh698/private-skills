"""基于已审核的 PDF 简历，仅替换第一页中的指定薪资字段。"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import pymupdf
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


DEFAULT_SALARIES = ("8k", "8-9k", "9k", "9-10k", "10k", "10-11k", "11k", "12k")
DEFAULT_FIELD_LABEL = "期望月薪："
DEFAULT_COVER_COLOR = "#364352"
DEFAULT_FONT_PATH = Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf")


def _register_font(font_path: Path) -> str:
    """注册中文字体，保证叠加层中的中文字段不会变成乱码或省略点。"""
    if not font_path.exists():
        raise FileNotFoundError(f"未找到中文字体：{font_path}")
    font_name = "ResumeVariantNotoSC"
    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    return font_name


def _find_field(document: pymupdf.Document, field_label: str) -> pymupdf.Rect:
    """定位第一页字段的完整文本区域，字段缺失时明确失败。"""
    matches = document[0].search_for(field_label)
    if not matches:
        raise ValueError(f"第一页未找到字段：{field_label}")
    words = document[0].get_text("words")
    same_line = [word for word in words if abs(word[1] - matches[0].y0) < 2]
    if not same_line:
        return matches[0]
    return pymupdf.Rect(
        min(word[0] for word in same_line),
        min(word[1] for word in same_line),
        max(word[2] for word in same_line),
        max(word[3] for word in same_line),
    )


def _make_overlay(
    overlay_path: Path,
    page_rect: pymupdf.Rect,
    field_rect: pymupdf.Rect,
    text: str,
    cover_color: str,
    font_name: str,
) -> None:
    """创建单页叠加层，精确盖住旧字段并沿用原有视觉尺寸。"""
    padding = 1.6
    cover_rect = pymupdf.Rect(
        field_rect.x0 - padding,
        field_rect.y0 - padding,
        field_rect.x1 + 45,
        field_rect.y1 + padding,
    )
    layer = canvas.Canvas(str(overlay_path), pagesize=(page_rect.width, page_rect.height))
    layer.setFillColor(colors.HexColor(cover_color))
    layer.rect(
        cover_rect.x0,
        page_rect.height - cover_rect.y1,
        cover_rect.width,
        cover_rect.height,
        stroke=0,
        fill=1,
    )
    layer.setFillColor(colors.white)
    font_size = max(8.0, min(10.0, field_rect.height))
    layer.setFont(font_name, font_size)
    baseline = page_rect.height - field_rect.y1 + (field_rect.height - font_size) / 2 + 1.0
    layer.drawString(field_rect.x0, baseline, text)
    layer.save()


def create_variants(
    source_pdf: Path,
    output_dir: Path,
    salaries: tuple[str, ...] = DEFAULT_SALARIES,
    field_label: str = DEFAULT_FIELD_LABEL,
    cover_color: str = DEFAULT_COVER_COLOR,
    font_path: Path = DEFAULT_FONT_PATH,
    overwrite: bool = False,
) -> list[Path]:
    """创建多份薪资变体；只替换第一页目标字段，其他页面保留原样。"""
    if not source_pdf.exists():
        raise FileNotFoundError(f"未找到源简历：{source_pdf}")
    if not salaries:
        raise ValueError("至少需要一个薪资选项")

    output_dir.mkdir(parents=True, exist_ok=True)
    font_name = _register_font(font_path)
    probe = pymupdf.open(source_pdf)
    page_rect = probe[0].rect
    field_rect = _find_field(probe, field_label)
    probe.close()

    created: list[Path] = []
    # 叠加层放在系统临时目录，避免在用户的投递目录留下中间文件。
    # 不在脚本中删除任何文件，便于遵循调用方的文件保留策略。
    overlay_dir = Path(tempfile.mkdtemp(prefix="resume-variant-overlays-"))
    for salary in salaries:
        output_path = output_dir / f"{source_pdf.stem}-{field_label.rstrip('：')}{salary}.pdf"
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"目标文件已存在：{output_path}")

        overlay_path = overlay_dir / f"{salary}.pdf"
        _make_overlay(
            overlay_path,
            page_rect,
            field_rect,
            f"{field_label}{salary}",
            cover_color,
            font_name,
        )
        source = PdfReader(str(source_pdf))
        overlay = PdfReader(str(overlay_path))
        writer = PdfWriter(clone_from=source)
        # 先将页面挂载到 writer，再叠加内容，避免 pypdf 未来版本的弃用路径。
        writer.pages[0].merge_page(overlay.pages[0])
        with output_path.open("wb") as stream:
            writer.write(stream)
        created.append(output_path)
    return created


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="基于批准的 PDF 简历生成薪资变体")
    parser.add_argument("--source", required=True, type=Path, help="已审核的基准 PDF 简历")
    parser.add_argument("--output-dir", required=True, type=Path, help="输出目录")
    parser.add_argument("--salaries", nargs="+", default=DEFAULT_SALARIES, help="薪资选项")
    parser.add_argument("--field-label", default=DEFAULT_FIELD_LABEL, help="要替换的字段标签")
    parser.add_argument("--cover-color", default=DEFAULT_COVER_COLOR, help="字段背景色，例如 #364352")
    parser.add_argument("--font-path", type=Path, default=DEFAULT_FONT_PATH, help="中文字体文件路径")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖同名文件")
    return parser.parse_args()


def main() -> None:
    """执行命令行入口。"""
    args = parse_args()
    paths = create_variants(
        args.source,
        args.output_dir,
        tuple(args.salaries),
        args.field_label,
        args.cover_color,
        args.font_path,
        args.overwrite,
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
