"""验证薪资变体工具只修改第一页的期望月薪。"""

import importlib.util
import hashlib
import tempfile
import unittest
import warnings
from pathlib import Path

import pymupdf
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "create_salary_variants.py"


class SalaryVariantScriptTests(unittest.TestCase):
    def test_exposes_expected_salary_options(self):
        """支持会话中约定的八种期望月薪选项。"""
        spec = importlib.util.spec_from_file_location("salary_variants", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            module.DEFAULT_SALARIES,
            ("8k", "8-9k", "9k", "9-10k", "10k", "10-11k", "11k", "12k"),
        )

    def test_rejects_missing_source_pdf(self):
        """源简历不存在时应明确报错，避免生成空白或错误文件。"""
        spec = importlib.util.spec_from_file_location("salary_variants", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(FileNotFoundError):
            module.create_variants(Path("missing-source.pdf"), Path("output"), ("8k",))

    def test_changes_target_salary_and_preserves_second_page(self):
        """生成的变体应为两页，且第 2 页渲染不变。"""
        spec = importlib.util.spec_from_file_location("salary_variants", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        root = Path(tempfile.mkdtemp(prefix="resume-variant-test-"))
        source_path = root / "base.pdf"
        font_path = Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf")
        pdfmetrics.registerFont(TTFont("TestNotoSC", str(font_path)))
        pdf = canvas.Canvas(str(source_path), pagesize=(615.12, 870.0))
        pdf.setFillColor(colors.HexColor("#364352"))
        pdf.rect(0, 0, 202.5, 870.0, stroke=0, fill=1)
        pdf.setFillColor(colors.white)
        pdf.setFont("TestNotoSC", 9.4)
        pdf.drawString(20, 335, "期望月薪：11-12k")
        pdf.showPage()
        pdf.setFont("TestNotoSC", 12)
        pdf.drawString(40, 800, "第二页保持不变")
        pdf.save()

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            paths = module.create_variants(
                source_path,
                root / "variants",
                ("8k",),
                font_path=font_path,
            )
        variant = pymupdf.open(paths[0])
        original = pymupdf.open(source_path)
        self.assertEqual(variant.page_count, 2)
        self.assertIn("期望月薪：8k", variant[0].get_text())
        self.assertEqual(
            hashlib.sha256(variant[1].get_pixmap().tobytes()).digest(),
            hashlib.sha256(original[1].get_pixmap().tobytes()).digest(),
        )


if __name__ == "__main__":
    unittest.main()
