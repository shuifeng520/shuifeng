from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DESIGNS_DIR = ROOT / "designs"
IMAGES_DIR = ROOT / "images"

WIDTH = 1980
HEIGHT = 1080
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

COLORS = {
    "bg": "#f3f7fb",
    "card": "#ffffff",
    "line": "#d8e5f4",
    "blue": "#2b7bd8",
    "blue_dark": "#155fb4",
    "blue_soft": "#eef6ff",
    "text": "#10203b",
    "muted": "#5e6f88",
    "subtle": "#7b8aa0",
    "green": "#e9fbf2",
    "green_line": "#9ce3bf",
    "green_text": "#137a4c",
    "orange": "#fff4e8",
    "orange_line": "#ffd0a3",
    "orange_text": "#c15b18",
    "field": "#f1f5f9",
    "white": "#ffffff",
}


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size=size)


def fit_text(draw: ImageDraw.ImageDraw, value: str, size: int, max_width: int) -> str:
    ellipsis = "..."
    if draw.textlength(value, font=font(size)) <= max_width:
        return value
    result = value
    while result and draw.textlength(result + ellipsis, font=font(size)) > max_width:
        result = result[:-1]
    return result + ellipsis


@dataclass
class Canvas:
    name: str

    def __post_init__(self) -> None:
        self.image = Image.new("RGBA", (WIDTH, HEIGHT), COLORS["bg"])
        self.draw = ImageDraw.Draw(self.image)
        self.svg: list[str] = [
            f'<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
            'fill="none" xmlns="http://www.w3.org/2000/svg">',
            "<defs>",
            '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
            '<feDropShadow dx="0" dy="14" stdDeviation="18" flood-color="#15345b" flood-opacity="0.10"/>',
            "</filter>",
            "</defs>",
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{COLORS["bg"]}"/>',
        ]

    def rounded(self, xy: tuple[int, int, int, int], radius: int, fill: str, outline: str | None = None, width: int = 1, shadow: bool = False) -> None:
        if shadow:
            shadow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            sx1, sy1, sx2, sy2 = xy
            shadow_draw.rounded_rectangle((sx1, sy1 + 12, sx2, sy2 + 12), radius=radius, fill=(22, 52, 91, 24))
            self.image.alpha_composite(shadow_layer.filter(ImageFilter.GaussianBlur(18)))
        self.draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        attrs = [
            f'x="{xy[0]}"',
            f'y="{xy[1]}"',
            f'width="{xy[2] - xy[0]}"',
            f'height="{xy[3] - xy[1]}"',
            f'rx="{radius}"',
            f'fill="{fill}"',
        ]
        if outline:
            attrs.extend([f'stroke="{outline}"', f'stroke-width="{width}"'])
        if shadow:
            attrs.append('filter="url(#shadow)"')
        self.svg.append("<rect " + " ".join(attrs) + "/>")

    def rect(self, xy: tuple[int, int, int, int], fill: str, outline: str | None = None, width: int = 1) -> None:
        self.draw.rectangle(xy, fill=fill, outline=outline, width=width)
        attrs = [
            f'x="{xy[0]}"',
            f'y="{xy[1]}"',
            f'width="{xy[2] - xy[0]}"',
            f'height="{xy[3] - xy[1]}"',
            f'fill="{fill}"',
        ]
        if outline:
            attrs.extend([f'stroke="{outline}"', f'stroke-width="{width}"'])
        self.svg.append("<rect " + " ".join(attrs) + "/>")

    def line(self, xy: tuple[int, int, int, int], fill: str, width: int = 1) -> None:
        self.draw.line(xy, fill=fill, width=width)
        self.svg.append(
            f'<line x1="{xy[0]}" y1="{xy[1]}" x2="{xy[2]}" y2="{xy[3]}" '
            f'stroke="{fill}" stroke-width="{width}" stroke-linecap="round"/>'
        )

    def circle(self, cx: int, cy: int, r: int, fill: str, outline: str | None = None, width: int = 1) -> None:
        self.draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline=outline, width=width)
        attrs = [f'cx="{cx}"', f'cy="{cy}"', f'r="{r}"', f'fill="{fill}"']
        if outline:
            attrs.extend([f'stroke="{outline}"', f'stroke-width="{width}"'])
        self.svg.append("<circle " + " ".join(attrs) + "/>")

    def text(self, xy: tuple[int, int], value: str, size: int = 24, fill: str = COLORS["text"], anchor: str = "la", max_width: int | None = None) -> None:
        if max_width is not None:
            value = fit_text(self.draw, value, size, max_width)
        pil_anchor = anchor
        self.draw.text(xy, value, font=font(size), fill=fill, anchor=pil_anchor)
        svg_anchor = "middle" if "m" in anchor else "start"
        dominant = "middle" if anchor.endswith("m") else "auto"
        self.svg.append(
            f'<text x="{xy[0]}" y="{xy[1]}" fill="{fill}" font-size="{size}" '
            'font-family="WenQuanYi Micro Hei, Noto Sans CJK SC, Microsoft YaHei, Arial, sans-serif" '
            f'text-anchor="{svg_anchor}" dominant-baseline="{dominant}">{escape(value)}</text>'
        )

    def multiline(self, x: int, y: int, lines: Iterable[str], size: int = 24, fill: str = COLORS["muted"], gap: int = 34) -> None:
        for i, line in enumerate(lines):
            self.text((x, y + i * gap), line, size, fill)

    def save(self) -> None:
        DESIGNS_DIR.mkdir(exist_ok=True)
        IMAGES_DIR.mkdir(exist_ok=True)
        self.svg.append("</svg>")
        (DESIGNS_DIR / f"{self.name}.svg").write_text("\n".join(self.svg) + "\n", encoding="utf-8")
        self.image.convert("RGB").save(IMAGES_DIR / f"{self.name}.png", quality=96)


def header(c: Canvas, trail: str) -> None:
    c.rounded((80, 44, 1900, 124), 20, COLORS["blue"])
    c.text((118, 86), "部门预算执行审计智能体", 28, COLORS["white"], "lm")
    c.rounded((1350, 66, 1538, 106), 20, COLORS["blue_dark"])
    c.text((1444, 86), trail, 18, COLORS["white"], "mm")
    c.text((1788, 86), "auditor / 审计员", 20, COLORS["white"], "mm")


def badge(c: Canvas, x: int, y: int, w: int, label: str, fill: str = COLORS["blue_soft"], color: str = COLORS["blue_dark"]) -> None:
    c.rounded((x, y, x + w, y + 42), 21, fill, COLORS["line"])
    c.text((x + w // 2, y + 21), label, 20, color, "mm")


def button(c: Canvas, x: int, y: int, w: int, label: str, primary: bool = True) -> None:
    if primary:
        c.rounded((x, y, x + w, y + 56), 14, COLORS["blue"])
        c.text((x + w // 2, y + 28), label, 22, COLORS["white"], "mm")
    else:
        c.rounded((x, y, x + w, y + 56), 14, COLORS["white"], COLORS["line"])
        c.text((x + w // 2, y + 28), label, 22, COLORS["muted"], "mm")


def stepper(c: Canvas, labels: list[str], active: int) -> None:
    y = 344
    xs = [190, 700, 1210, 1720]
    c.line((xs[0], y, xs[-1], y), COLORS["line"], 8)
    c.line((xs[0], y, xs[active - 1], y), COLORS["blue"], 8)
    for idx, (x, label) in enumerate(zip(xs, labels), start=1):
        if idx <= active:
            c.circle(x, y, 30, COLORS["blue"])
            c.text((x, y), str(idx), 24, COLORS["white"], "mm")
        else:
            c.circle(x, y, 30, COLORS["white"], COLORS["blue"], 4)
            c.text((x, y), str(idx), 24, COLORS["blue_dark"], "mm")
        c.text((x, y + 58), label, 24, COLORS["text"], "mm")


def page_intro(c: Canvas, crumb: str, title: str, desc: str, trail: str) -> None:
    header(c, trail)
    c.text((80, 172), crumb, 18, COLORS["subtle"])
    c.text((80, 216), title, 40, COLORS["text"])
    c.text((80, 268), desc, 24, COLORS["muted"])


def footer(c: Canvas, hint: str, primary: str) -> None:
    c.rounded((80, 970, 1180, 1030), 16, "#eaf4ff")
    c.text((112, 1000), hint, 22, COLORS["blue_dark"], "lm")
    button(c, 1330, 972, 210, "上一步", False)
    button(c, 1570, 972, 330, primary, True)


def entry() -> None:
    c = Canvas("00-guided-entry")
    header(c, "引导式总入口")
    c.text((80, 190), "今天要完成什么审计任务？", 44, COLORS["text"])
    c.text((80, 248), "选择一个任务后，系统会按步骤引导你完成资料输入、数据入库、方法执行和结果归档。", 26, COLORS["muted"])

    c.rounded((80, 304, 1900, 438), 24, COLORS["orange"], COLORS["orange_line"])
    c.text((122, 348), "继续上次任务", 30, COLORS["text"])
    c.text((122, 390), "4-1-1 电梯维护费单价超标审计 · 已生成 SQL，等待执行验证", 24, COLORS["muted"])
    button(c, 1630, 342, 220, "继续处理", True)

    c.text((80, 510), "引导式任务入口", 32, COLORS["text"])
    c.text((80, 552), "去掉左侧菜单后，用户从任务卡片进入流程；每个流程内部完成当前任务，不再依赖菜单树跳转。", 22, COLORS["muted"])

    cards = [
        ("1", "智能识别", ["政策法规、历史经验、自然语言描述", "统一进入识别流程，生成审计思路。"], "生成思路", 80),
        ("2", "数据接入", ["数据库直连与文件导入统一入口", "预览、清洗、字段映射后确认入库。"], "形成审计库", 700),
        ("3", "方法执行", ["选择思路、生成 SQL、运行验证", "导出报告并完成结果归档。"], "归档结果", 1320),
    ]
    for idx, title, lines, tag, x in cards:
        c.rounded((x, 604, x + 580, 850), 26, COLORS["card"], COLORS["line"], shadow=True)
        c.circle(x + 56, 668, 34, COLORS["blue"])
        c.text((x + 56, 668), idx, 26, COLORS["white"], "mm")
        c.text((x + 108, 660), title, 32, COLORS["text"])
        c.multiline(x + 48, 724, lines, 24, COLORS["muted"], 38)
        badge(c, x + 48, 792, 160, tag)

    c.rounded((80, 890, 960, 1030), 22, COLORS["card"], COLORS["line"])
    c.text((120, 936), "最近产出", 26, COLORS["text"])
    c.text((120, 982), "审计思路 26 条 · 临时库 7 张表 · SQL 方法命中 15 个疑点", 24, COLORS["muted"])
    c.rounded((1000, 890, 1900, 1030), 22, COLORS["green"], COLORS["green_line"])
    c.text((1040, 936), "文字溢出规则", 26, COLORS["text"])
    c.text((1040, 982), "标题最多 2 行；列表与表格长字段省略展示，并支持查看完整内容。", 24, COLORS["muted"])
    c.save()


def recognition() -> None:
    c = Canvas("01-smart-recognition")
    page_intro(c, "首页 / 智能识别", "智能识别工作流", "三类材料汇总到一个向导中，右侧持续反馈抽取、补齐和生成结果。", "智能识别")
    stepper(c, ["选择材料", "上传/描述", "抽取补齐", "确认生成"], 2)

    c.rounded((80, 420, 1280, 910), 26, COLORS["card"], COLORS["line"], shadow=True)
    c.text((126, 476), "1 选择已有材料", 32, COLORS["text"])
    c.text((126, 518), "资料入口合并展示，支持单选或组合使用。", 23, COLORS["muted"])
    material_cards = [
        ("P", "政策法规文件", "PDF / DOCX", "抽取审计规则", 126, True),
        ("H", "历史经验资料", "Excel / Word / CSV", "补齐同类案例", 500, False),
        ("Q", "直接描述问题", "自然语言输入", "识别审计方向", 874, False),
    ]
    for icon, title, desc, tag, x, selected in material_cards:
        c.rounded((x, 570, x + 330, 735), 20, COLORS["blue_soft"] if selected else "#f8fafc", "#8fc1ff" if selected else COLORS["line"], 2)
        c.circle(x + 42, 626, 24, COLORS["blue"] if selected else "#dbeafe")
        c.text((x + 42, 626), icon, 22, COLORS["white"] if selected else COLORS["muted"], "mm")
        c.text((x + 86, 610), title, 26, COLORS["text"], max_width=220)
        c.text((x + 86, 650), desc, 20, COLORS["subtle"], max_width=220)
        c.text((x + 86, 690), tag, 20, COLORS["blue_dark"])
    c.line((126, 782, 1234, 782), COLORS["line"], 2)
    c.text((126, 836), "2 上传资料或填写问题", 30, COLORS["text"])
    c.rounded((126, 860, 558, 894), 12, COLORS["field"])
    c.text((148, 877), "拖拽上传文件，支持 PDF / DOCX / CSV", 18, COLORS["subtle"], "lm")
    c.rounded((600, 860, 1234, 894), 12, COLORS["field"])
    c.text((622, 877), "输入审计问题：项目预算执行率偏低且合同支付异常", 18, COLORS["subtle"], "lm", max_width=580)

    c.rounded((1320, 420, 1900, 910), 26, COLORS["card"], COLORS["line"], shadow=True)
    c.text((1366, 476), "3 抽取补齐预览", 32, COLORS["text"])
    c.text((1366, 518), "过程状态固定在右侧，减少跳转。", 23, COLORS["muted"])
    badge(c, 1366, 570, 142, "政策规则")
    badge(c, 1530, 570, 142, "历史经验", "#f8fafc", COLORS["muted"])
    badge(c, 1694, 570, 110, "描述", "#f8fafc", COLORS["muted"])
    c.rounded((1366, 650, 1846, 760), 18, "#f8fbff", COLORS["line"])
    c.text((1400, 690), "识别到 6 条审计关注点", 26, COLORS["text"])
    c.text((1400, 732), "项目预算执行率偏低、采购合规性、合同支付异常...", 20, COLORS["subtle"], max_width=410)
    c.rounded((1366, 790, 1846, 858), 18, COLORS["green"], COLORS["green_line"])
    c.text((1400, 824), "已匹配 12 条历史案例，可直接补齐规则依据。", 21, COLORS["green_text"], "lm")
    footer(c, "私有思路库：确认后进入思路库，可继续编辑或导出。", "开始识别并生成")
    c.save()


def ingestion() -> None:
    c = Canvas("02-data-ingestion")
    page_intro(c, "首页 / 数据接入", "审计数据接入工作流", "数据库直连和文件上传共用一个入口，预览清洗后再设为当前审计库。", "数据接入")
    stepper(c, ["选择方式", "配置/上传", "预览清洗", "设为审计库"], 2)

    c.rounded((80, 420, 1280, 910), 26, COLORS["card"], COLORS["line"], shadow=True)
    c.text((126, 476), "1 选择数据接入方式", 32, COLORS["text"])
    c.text((126, 518), "同页切换接入方式，连接和文件上传最终都进入临时库。", 23, COLORS["muted"])
    c.rounded((126, 570, 620, 720), 20, COLORS["blue_soft"], "#8fc1ff", 2)
    c.circle(178, 626, 26, COLORS["blue"])
    c.text((178, 626), "D", 22, COLORS["white"], "mm")
    c.text((230, 606), "数据库直连", 28, COLORS["text"])
    c.text((230, 648), "MySQL / PostgreSQL / Oracle", 21, COLORS["subtle"])
    c.text((230, 690), "示例：localhost:3306 / dataset01", 20, COLORS["blue_dark"])
    c.rounded((660, 570, 1234, 720), 20, "#f8fafc", COLORS["line"])
    c.circle(712, 626, 26, "#dbeafe")
    c.text((712, 626), "F", 22, COLORS["muted"], "mm")
    c.text((764, 606), "文件导入", 28, COLORS["text"])
    c.text((764, 648), "Excel / CSV 批量上传", 21, COLORS["subtle"])
    c.text((764, 690), "上传后自动识别字段和数据表", 20, COLORS["blue_dark"])
    c.text((126, 792), "2 填写连接信息或上传文件", 30, COLORS["text"])
    fields = [("数据库地址 Host", "localhost", 126, 250), ("端口 Port", "3306", 400, 180), ("用户名", "user1", 604, 210), ("密码", "******", 838, 240)]
    for label, value, x, w in fields:
        c.text((x, 832), label, 18, COLORS["subtle"])
        c.rounded((x, 850, x + w, 895), 12, COLORS["field"])
        c.text((x + 18, 872), value, 20, COLORS["muted"], "lm")

    c.rounded((1320, 420, 1900, 910), 26, COLORS["card"], COLORS["line"], shadow=True)
    c.text((1366, 476), "3 预览清洗并入库", 32, COLORS["text"])
    c.text((1366, 518), "先形成临时库，确认后再进入分析。", 23, COLORS["muted"])
    badge(c, 1366, 570, 130, "已连接", COLORS["green"], COLORS["green_text"])
    badge(c, 1520, 570, 130, "表预览")
    badge(c, 1674, 570, 130, "待入库", "#f8fafc", COLORS["muted"])
    c.rounded((1366, 650, 1846, 760), 18, COLORS["green"], COLORS["green_line"])
    c.text((1400, 690), "临时库：tmp_auditor", 26, COLORS["text"])
    c.text((1400, 732), "识别 7 张表，共 5,830 行数据", 20, COLORS["subtle"])
    c.rounded((1366, 790, 1846, 858), 18, COLORS["orange"], COLORS["orange_line"])
    c.text((1400, 824), "发现 3 个字段需确认映射，入库前可修正。", 21, COLORS["orange_text"], "lm")
    footer(c, "统一结果：数据库直连和文件上传都先进入临时库，再确认入库。", "确认入库并分析")
    c.save()


def method_workflow() -> None:
    c = Canvas("03-method-workflow")
    page_intro(c, "首页 / 方法执行", "审计方法全流程工作流", "思路、SQL、验证和导出保持在一个任务流程内，用户可回到任一步继续编辑。", "方法全流程")
    stepper(c, ["选择思路", "生成 SQL", "执行验证", "导出归档"], 3)

    c.rounded((80, 420, 510, 910), 26, COLORS["card"], COLORS["line"], shadow=True)
    c.text((126, 476), "1 选择审计思路", 32, COLORS["text"])
    c.rounded((126, 530, 260, 574), 12, COLORS["field"])
    c.text((193, 552), "全部", 20, COLORS["muted"], "mm")
    c.rounded((284, 530, 464, 574), 12, COLORS["field"])
    c.text((374, 552), "搜索关键词", 20, COLORS["muted"], "mm")
    c.text((126, 636), "共 26 条", 20, COLORS["subtle"])
    c.rounded((126, 662, 464, 724), 14, COLORS["blue"])
    c.text((148, 693), "4-1-1 电梯维护费超标...", 22, COLORS["white"], "lm")
    c.text((126, 772), "资金支出合规性", 22, COLORS["muted"])
    c.text((126, 812), "标题 1 行省略，悬浮显示完整内容。", 19, COLORS["subtle"], max_width=320)

    c.rounded((550, 420, 1280, 910), 26, COLORS["card"], COLORS["line"], shadow=True)
    c.text((596, 476), "2 查看详情并编辑 SQL", 32, COLORS["text"])
    c.text((596, 526), "4-1-1：电梯维护费单价超标审计", 26, COLORS["text"], max_width=620)
    c.text((596, 566), "规则分类：资金支出合规性", 21, COLORS["muted"])
    c.rounded((596, 606, 1234, 708), 18, COLORS["blue_soft"], "#8fc1ff")
    c.text((626, 642), "分析思路：提取合同与支付明细，计算单价并与标准限额比对。", 21, COLORS["blue_dark"], max_width=580)
    c.text((626, 678), "长描述超过区域时在详情抽屉展示完整内容。", 20, COLORS["blue_dark"])
    c.rounded((596, 742, 1234, 872), 18, "#f8fbff", COLORS["line"])
    sql = [
        "SELECT 项目名称, 支付摘要, 支付金额",
        "FROM 年度支付明细表",
        "WHERE 支付摘要 LIKE '%电梯维护%'",
        "AND 单价 > 8800;",
    ]
    for i, line in enumerate(sql):
        c.text((626, 776 + i * 30), line, 20, "#334155")

    c.rounded((1320, 420, 1900, 910), 26, COLORS["card"], COLORS["line"], shadow=True)
    c.text((1366, 476), "3 执行验证并导出", 32, COLORS["text"])
    c.text((1366, 518), "同页运行 SQL，预览命中结果。", 23, COLORS["muted"])
    button(c, 1366, 570, 320, "运行当前 SQL", True)
    c.rounded((1366, 660, 1846, 760), 18, COLORS["green"], COLORS["green_line"])
    c.text((1400, 696), "执行完成 · 命中 15 条", 26, COLORS["text"])
    c.text((1400, 734), "耗时 1.8s · 数据库 dataset01", 20, COLORS["subtle"])
    c.rounded((1366, 796, 1574, 852), 14, COLORS["white"], COLORS["line"])
    c.text((1470, 824), "导出 Excel", 22, COLORS["blue_dark"], "mm")
    c.rounded((1600, 796, 1808, 852), 14, COLORS["white"], COLORS["line"])
    c.text((1704, 824), "打包报告", 22, COLORS["blue_dark"], "mm")
    footer(c, "统一结果：思路、SQL 方法和执行结果保留关联，可回到任一步编辑。", "保存并归档结果")
    c.save()


def main() -> None:
    entry()
    recognition()
    ingestion()
    method_workflow()


if __name__ == "__main__":
    main()
