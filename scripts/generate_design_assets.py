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
    "bg": "#eef3f8",
    "surface": "#ffffff",
    "panel": "#f9fbfe",
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
            '<feDropShadow dx="0" dy="16" stdDeviation="18" flood-color="#15345b" flood-opacity="0.10"/>',
            "</filter>",
            "</defs>",
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{COLORS["bg"]}"/>',
        ]

    def rounded(
        self,
        xy: tuple[int, int, int, int],
        radius: int,
        fill: str,
        outline: str | None = None,
        width: int = 1,
        shadow: bool = False,
    ) -> None:
        if shadow:
            shadow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            x1, y1, x2, y2 = xy
            shadow_draw.rounded_rectangle((x1, y1 + 14, x2, y2 + 14), radius=radius, fill=(22, 52, 91, 24))
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

    def text(
        self,
        xy: tuple[int, int],
        value: str,
        size: int = 24,
        fill: str = COLORS["text"],
        anchor: str = "la",
        max_width: int | None = None,
    ) -> None:
        if max_width is not None:
            value = fit_text(self.draw, value, size, max_width)
        self.draw.text(xy, value, font=font(size), fill=fill, anchor=anchor)
        svg_anchor = "middle" if "m" in anchor else "start"
        dominant = "middle" if anchor.endswith("m") else "auto"
        self.svg.append(
            f'<text x="{xy[0]}" y="{xy[1]}" fill="{fill}" font-size="{size}" '
            'font-family="WenQuanYi Micro Hei, Noto Sans CJK SC, Microsoft YaHei, Arial, sans-serif" '
            f'text-anchor="{svg_anchor}" dominant-baseline="{dominant}">{escape(value)}</text>'
        )

    def multiline(self, x: int, y: int, lines: Iterable[str], size: int = 22, fill: str = COLORS["muted"], gap: int = 34) -> None:
        for idx, line in enumerate(lines):
            self.text((x, y + idx * gap), line, size, fill)

    def save(self) -> None:
        DESIGNS_DIR.mkdir(exist_ok=True)
        IMAGES_DIR.mkdir(exist_ok=True)
        self.svg.append("</svg>")
        (DESIGNS_DIR / f"{self.name}.svg").write_text("\n".join(self.svg) + "\n", encoding="utf-8")
        self.image.convert("RGB").save(IMAGES_DIR / f"{self.name}.png", quality=96)


def header(c: Canvas, mode: str) -> None:
    c.rounded((70, 36, 1910, 116), 24, COLORS["surface"], COLORS["line"], shadow=True)
    c.circle(124, 76, 24, COLORS["blue"])
    c.text((124, 76), "审", 21, COLORS["white"], "mm")
    c.text((166, 76), "部门预算执行审计智能体", 30, COLORS["text"], "lm")
    c.circle(538, 76, 7, COLORS["green_text"])
    c.text((556, 76), "在线", 18, COLORS["green_text"], "lm")
    c.rounded((806, 56, 1070, 96), 20, COLORS["blue_soft"], "#b9d8ff")
    c.text((938, 76), mode, 18, COLORS["blue_dark"], "mm")
    c.rounded((1550, 56, 1700, 96), 20, "#f4f7fb", COLORS["line"])
    c.text((1625, 76), "历史会话", 18, COLORS["muted"], "mm")
    c.rounded((1722, 56, 1874, 96), 20, COLORS["blue"])
    c.text((1798, 76), "新建对话", 18, COLORS["white"], "mm")


def chip(c: Canvas, x: int, y: int, label: str, w: int | None = None, active: bool = False) -> int:
    w = w or max(118, len(label) * 24 + 42)
    c.rounded((x, y, x + w, y + 42), 21, COLORS["blue_soft"] if active else COLORS["field"], COLORS["line"])
    c.text((x + w // 2, y + 21), label, 18, COLORS["blue_dark"] if active else COLORS["muted"], "mm")
    return x + w + 14


def action_chip(c: Canvas, x: int, y: int, label: str, icon: str, w: int = 132) -> int:
    c.rounded((x, y, x + w, y + 38), 19, "#f7fbff", "#e1ebf5")
    c.circle(x + 22, y + 19, 12, COLORS["blue_soft"], "#cfe0f2")
    c.text((x + 22, y + 19), icon, 13, COLORS["blue_dark"], "mm")
    c.text((x + 44, y + 19), label, 17, COLORS["muted"], "lm")
    return x + w + 12


def icon_button(c: Canvas, x: int, y: int, label: str) -> None:
    c.rounded((x, y, x + 140, y + 48), 16, COLORS["surface"], COLORS["line"])
    c.text((x + 70, y + 24), label, 18, COLORS["blue_dark"], "mm")


def chat_shell(c: Canvas, title: str, subtitle: str, mode: str, active_tab: str = "审计问答") -> None:
    header(c, mode)
    # Three independent panels keep the chat workspace visually calmer than a nested container.
    c.rounded((70, 148, 390, 1016), 28, COLORS["surface"], "#dce8f5", shadow=True)
    c.rounded((420, 148, 1380, 1016), 28, COLORS["surface"], "#dce8f5", shadow=True)
    c.rounded((1410, 148, 1910, 1016), 28, COLORS["surface"], "#dce8f5", shadow=True)

    # Left conversation list.
    c.text((102, 204), "会话", 28, COLORS["text"])
    c.text((102, 236), "按任务自动归档", 17, COLORS["subtle"])
    c.rounded((102, 266, 358, 314), 16, "#f7fbff", "#e4edf7")
    c.text((128, 290), "搜索审计问题 / 资料", 18, COLORS["subtle"], "lm")
    conversations = [
        ("当前", "电梯维护费超标审计", "刚刚 · 15 条疑点"),
        ("资料", "政策法规抽取", "6 条关注点"),
        ("数据", "dataset01 接入", "7 张表已识别"),
        ("方法", "SQL 方法归档", "已保存 12 条"),
    ]
    y = 352
    for tag, name, meta in conversations:
        selected = tag == "当前"
        c.rounded((100, y, 360, y + 96), 20, COLORS["blue_soft"] if selected else "#fbfdff", "#8fc1ff" if selected else "#e4edf7", 2 if selected else 1)
        c.circle(132, y + 34, 17, COLORS["blue"] if selected else "#dbeafe")
        c.text((132, y + 34), tag[:1], 14, COLORS["white"] if selected else COLORS["muted"], "mm")
        c.text((162, y + 28), name, 19, COLORS["text"], max_width=170)
        c.text((162, y + 62), meta, 16, COLORS["subtle"], max_width=170)
        y += 112

    # Main chat area.
    c.text((462, 206), title, 34, COLORS["text"])
    c.text((462, 250), subtitle, 22, COLORS["muted"], max_width=840)
    x = 462
    for tab in ["审计问答", "资料", "数据", "方法", "结果"]:
        x = chip(c, x, 300, tab, active=tab == active_tab)
    c.line((462, 368, 1340, 368), "#e5edf7", 2)

    # Right context panel.
    c.text((1444, 204), "上下文面板", 28, COLORS["text"])
    c.text((1444, 238), "资料、数据、方法和结果实时沉淀。", 18, COLORS["subtle"], max_width=390)


def assistant_bubble(c: Canvas, y: int, lines: list[str], title: str = "审计智能体", h: int = 120) -> None:
    c.circle(462, y + 36, 24, COLORS["blue"])
    c.text((462, y + 36), "AI", 15, COLORS["white"], "mm")
    c.rounded((506, y, 1256, y + h), 22, COLORS["panel"], "#e2ebf5")
    c.text((540, y + 34), title, 20, COLORS["text"])
    c.multiline(540, y + 70, lines, 20, COLORS["muted"], 30)


def user_bubble(c: Canvas, y: int, lines: list[str], h: int = 92) -> None:
    c.rounded((724, y, 1328, y + h), 22, COLORS["blue_dark"])
    c.multiline(756, y + 32, lines, 20, COLORS["white"], 30)
    c.circle(1354, y + 36, 24, COLORS["field"], COLORS["line"])
    c.text((1354, y + 36), "我", 16, COLORS["muted"], "mm")


def input_box(c: Canvas, placeholder: str = "输入审计问题，或拖拽政策、Excel、CSV 到这里...") -> None:
    c.rounded((462, 834, 1340, 992), 26, COLORS["surface"], "#cfe0f2", shadow=True)
    c.text((498, 878), placeholder, 22, COLORS["subtle"], max_width=690)
    c.circle(1288, 878, 30, COLORS["blue"])
    c.text((1288, 878), "↑", 28, COLORS["white"], "mm")
    c.line((498, 914, 1302, 914), COLORS["line"], 1)
    c.rounded((486, 928, 1232, 974), 18, "#fbfdff", "#edf3f9")
    c.text((510, 951), "快捷操作", 17, COLORS["subtle"], "lm")
    x = 612
    actions = [("上传资料", "文"), ("连接数据", "数"), ("生成 SQL", "S"), ("导出报告", "报")]
    for label, icon in actions:
        x = action_chip(c, x, 932, label, icon)


def side_stat(c: Canvas, y: int, title: str, value: str, desc: str, color: str = COLORS["blue_soft"]) -> None:
    c.rounded((1444, y, 1876, y + 104), 20, color, COLORS["line"])
    c.text((1476, y + 36), title, 22, COLORS["text"])
    c.text((1476, y + 72), value, 20, COLORS["blue_dark"] if color == COLORS["blue_soft"] else COLORS["green_text"])
    c.text((1652, y + 72), desc, 17, COLORS["subtle"], max_width=190)


def entry() -> None:
    c = Canvas("00-guided-entry")
    chat_shell(c, "问答式审计工作台", "一句话开始审计任务，系统自动识别意图并引导上传资料、接入数据、生成方法。", "对话首页")
    assistant_bubble(
        c,
        400,
        ["你可以直接输入审计目标，也可以上传资料或连接数据。", "例如：帮我检查部门预算执行中电梯维护费是否超标。"],
        h=132,
    )
    user_bubble(c, 562, ["帮我做一个部门预算执行审计，先从资料识别开始。"])
    assistant_bubble(
        c,
        688,
        ["好的。我会按“资料识别 -> 数据接入 -> 方法执行 -> 结果归档”推进。", "你可以上传政策文件，也可以直接描述审计关注点。"],
        h=132,
    )
    input_box(c, "直接输入审计目标，例如：检查采购预算执行率偏低的原因...")

    side_stat(c, 316, "当前任务", "部门预算执行审计", "对话中")
    side_stat(c, 448, "资料状态", "待上传", "支持 PDF / DOCX / CSV")
    side_stat(c, 580, "数据状态", "未连接", "可直连数据库")
    side_stat(c, 712, "方法状态", "待生成", "SQL 与报告")
    c.rounded((1444, 858, 1876, 936), 20, COLORS["orange"], COLORS["orange_line"])
    c.text((1476, 892), "快捷建议", 22, COLORS["text"])
    c.text((1476, 922), "上传政策文件后自动抽取规则。", 18, COLORS["orange_text"])
    c.save()


def recognition() -> None:
    c = Canvas("01-smart-recognition")
    chat_shell(c, "智能识别问答", "用户通过对话上传政策、历史经验或直接描述问题，系统实时抽取审计关注点。", "智能识别", "资料")
    user_bubble(c, 400, ["上传了《预算执行审计办法.pdf》，帮我提取可执行的审计规则。"], h=96)
    assistant_bubble(
        c,
        528,
        ["已识别 6 条审计关注点，并匹配 12 条历史案例。", "建议先确认“预算执行率偏低”和“采购金额合规性”两类规则。"],
        h=136,
    )
    c.rounded((506, 696, 1256, 814), 20, COLORS["surface"], COLORS["line"])
    c.text((540, 730), "抽取结果预览", 22, COLORS["text"])
    c.text((540, 764), "1. 项目预算执行率偏低：对比预算金额、支付金额和执行进度。", 19, COLORS["muted"], max_width=670)
    c.text((540, 794), "2. 采购金额合规性：检查采购限额、合同金额与支付明细。", 19, COLORS["muted"], max_width=670)
    input_box(c, "继续追问：把第 1 条规则生成审计思路，并补充历史案例依据...")

    side_stat(c, 316, "资料包", "3 类资料", "政策 / 经验 / 描述")
    side_stat(c, 448, "抽取进度", "6 条关注点", "已完成", COLORS["green"])
    side_stat(c, 580, "历史匹配", "12 条案例", "可引用", COLORS["green"])
    c.rounded((1444, 724, 1876, 874), 20, COLORS["surface"], COLORS["line"])
    c.text((1476, 762), "用户确认后", 22, COLORS["text"])
    c.text((1476, 798), "生成审计思路并写入私有思路库，后续可在对话中继续编辑。", 18, COLORS["muted"], max_width=360)
    c.save()


def ingestion() -> None:
    c = Canvas("02-data-ingestion")
    chat_shell(c, "数据接入问答", "通过对话完成数据库连接、文件上传、表结构预览、字段映射和确认入库。", "数据接入", "数据")
    user_bubble(c, 400, ["连接 localhost:3306 的 dataset01，并预览部门预算相关表。"], h=96)
    assistant_bubble(
        c,
        528,
        ["连接成功，已识别 7 张表，共 5,830 行数据。", "我发现 3 个字段需要确认映射，建议入库前先修正。"],
        h=136,
    )
    c.rounded((506, 696, 1256, 814), 20, COLORS["surface"], COLORS["line"])
    c.text((540, 730), "字段映射建议", 22, COLORS["text"])
    c.text((540, 764), "预算金额 -> budget_amount；支付金额 -> paid_amount；合同编号 -> contract_no", 19, COLORS["muted"], max_width=670)
    c.text((540, 794), "确认后将创建临时库 tmp_auditor，并设为当前审计库。", 19, COLORS["muted"], max_width=670)
    input_box(c, "继续追问：确认字段映射并把 tmp_auditor 设置为当前审计库...")

    side_stat(c, 316, "连接状态", "已连接", "dataset01", COLORS["green"])
    side_stat(c, 448, "临时库", "tmp_auditor", "7 张表")
    side_stat(c, 580, "数据量", "5,830 行", "待清洗")
    c.rounded((1444, 724, 1876, 874), 20, COLORS["orange"], COLORS["orange_line"])
    c.text((1476, 762), "待确认项", 22, COLORS["text"])
    c.text((1476, 798), "发现 3 个字段需确认映射，对话中回复“确认”即可入库。", 18, COLORS["orange_text"], max_width=360)
    c.save()


def method_workflow() -> None:
    c = Canvas("03-method-workflow")
    chat_shell(c, "方法执行问答", "用户用自然语言要求生成 SQL、执行验证和导出报告，系统把过程沉淀为可复用方法。", "方法执行", "方法")
    user_bubble(c, 400, ["基于电梯维护费规则生成 SQL，并运行当前审计库。"], h=96)
    assistant_bubble(
        c,
        528,
        ["已生成 SQL 并执行完成，命中 15 条疑点。", "下方是关键 SQL，可继续要求我解释、优化或导出报告。"],
        h=136,
    )
    c.rounded((506, 690, 1256, 826), 20, "#f8fbff", COLORS["line"])
    c.text((540, 724), "SQL 片段", 22, COLORS["text"])
    sql = [
        "SELECT 项目名称, 支付摘要, 支付金额",
        "FROM 年度支付明细表",
        "WHERE 支付摘要 LIKE '%电梯维护%' AND 单价 > 8800;",
    ]
    for idx, line in enumerate(sql):
        c.text((540, 758 + idx * 28), line, 18, "#334155", max_width=670)
    input_box(c, "继续追问：解释命中原因，导出 Excel，并打包审计报告...")

    side_stat(c, 316, "执行状态", "已完成", "耗时 1.8s", COLORS["green"])
    side_stat(c, 448, "命中结果", "15 条疑点", "可预览")
    side_stat(c, 580, "归档状态", "待确认", "Excel / 报告")
    c.rounded((1444, 724, 1876, 874), 20, COLORS["surface"], COLORS["line"])
    c.text((1476, 762), "可执行动作", 22, COLORS["text"])
    x = 1476
    x = chip(c, x, 798, "导出 Excel", 138, True)
    chip(c, x, 798, "打包报告", 138)
    c.text((1476, 856), "对话确认后保存为可复用审计方法。", 18, COLORS["muted"])
    c.save()


def main() -> None:
    entry()
    recognition()
    ingestion()
    method_workflow()


if __name__ == "__main__":
    main()
