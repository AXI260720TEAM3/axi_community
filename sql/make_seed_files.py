"""
seed.sql 의 첨부파일 19건에 해당하는 가짜 파일을 media/ 아래에 만듭니다.

DB 에는 경로(stored_path)만 들어 있고 실제 파일은 없어서, 샘플 글의 첨부를
다운로드하면 파일을 찾지 못합니다. media/ 는 .gitignore 에 있으므로 clone 한
사람마다 한 번씩 실행해야 합니다.

    python sql/make_seed_files.py

- 이미 있는 파일은 건드리지 않습니다. 몇 번 실행해도 안전합니다.
- 파일 크기는 DB 의 file_size 와 다릅니다. 화면에는 DB 값이 표시됩니다.
- .hwp 는 형식을 흉내낼 수 없어 텍스트로 채웁니다. 한글에서는 열리지 않습니다.
"""

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = BASE_DIR / "media"
FONT_PATH = Path("C:/Windows/Fonts/malgun.ttf")

# (attachment_id, post_id, origin_name, stored_path) — seed.sql 과 같은 순서
SEED = [
    (1,  12, "알고리즘_스터디_운영안.pdf", "attachments/2026/09/6f2a1c9e.pdf"),
    (2,  12, "1주차_문제목록.xlsx",        "attachments/2026/09/b81d40aa.xlsx"),
    (3,  11, "점심_지도_정리.png",         "attachments/2026/09/1a77c503.png"),
    (4,  8,  "프린터_설정화면.png",        "attachments/2026/09/c4e9b217.png"),
    (5,  8,  "용지함_위치.jpg",            "attachments/2026/09/9d3f8a61.jpg"),
    (6,  15, "ERD_초안.png",               "attachments/2026/09/2b60cf14.png"),
    (7,  15, "중간테이블_예시.sql",        "attachments/2026/09/7ac1e8b3.sql"),
    (8,  19, "외래키_이름_예시.txt",       "attachments/2026/09/e15b9d72.txt"),
    (9,  24, "채용공고_상세.pdf",          "attachments/2026/09/48fd2c06.pdf"),
    (10, 21, "인턴모집_공고.pdf",          "attachments/2026/08/3e70b95f.pdf"),
    (11, 22, "면접_체크리스트.pdf",        "attachments/2026/09/aa02df38.pdf"),
    (12, 22, "자기소개_예시.docx",         "attachments/2026/09/55c8e401.docx"),
    (13, 3,  "훈련장려금_신청서.hwp",      "attachments/2026/08/0c94a7bb.hwp"),
    (14, 3,  "제출_예시.pdf",              "attachments/2026/08/f2318ad0.pdf"),
    (15, 3,  "자주_묻는_질문.pdf",         "attachments/2026/08/6b5c1ee9.pdf"),
    (16, 4,  "출결정정_요청서.hwp",        "attachments/2026/09/d7a4f082.hwp"),
    (17, 4,  "작성_예시.pdf",              "attachments/2026/09/91e6b3c7.pdf"),
    (18, 1,  "2학기_강의실_배정표.xlsx",   "attachments/2026/08/ab13d94e.xlsx"),
    (19, 6,  "연휴_운영안내.pdf",          "attachments/2026/09/7e0a5c39.pdf"),
]


def font(size):
    if FONT_PATH.exists():
        return ImageFont.truetype(str(FONT_PATH), size)
    return ImageFont.load_default(size)


def lines_for(attachment_id, post_id, origin_name, stored_path):
    return [
        origin_name,
        "seed.sql 샘플 첨부파일입니다. (테스트용 가짜 파일)",
        f"attachment_id {attachment_id} · 게시글 {post_id}",
        f"저장 경로 {stored_path}",
    ]


def make_image(path, lines, size, fmt):
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size[0], 12], fill="#2f6fed")
    draw.text((60, 70), lines[0], fill="black", font=font(40))
    y = 150
    for line in lines[1:]:
        draw.text((60, y), line, fill="#444444", font=font(24))
        y += 44
    if fmt == "PDF":
        img.save(path, "PDF", resolution=100)
    else:
        img.save(path, fmt)


def write_zip(path, parts):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, xml in parts.items():
            z.writestr(name, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml)


def make_xlsx(path, lines):
    rows = "".join(
        f'<row r="{i}"><c r="A{i}" t="inlineStr"><is><t>{escape(line)}</t></is></c></row>'
        for i, line in enumerate(lines, start=1)
    )
    write_zip(path, {
        "[Content_Types].xml":
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>',
        "_rels/.rels":
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        "xl/workbook.xml":
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels":
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>',
        "xl/worksheets/sheet1.xml":
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{rows}</sheetData></worksheet>',
    })


def make_docx(path, lines):
    paras = "".join(f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>" for line in lines)
    write_zip(path, {
        "[Content_Types].xml":
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>',
        "_rels/.rels":
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>',
        "word/document.xml":
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{paras}</w:body></w:document>",
    })


def make_text(path, lines, comment=""):
    path.write_text("\n".join(comment + line for line in lines) + "\n", encoding="utf-8")


def main():
    created = skipped = 0
    for attachment_id, post_id, origin_name, stored_path in SEED:
        path = MEDIA_ROOT / stored_path
        if path.exists():
            print(f"skip    {stored_path}")
            skipped += 1
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        lines = lines_for(attachment_id, post_id, origin_name, stored_path)
        ext = path.suffix.lower()

        if ext == ".png":
            make_image(path, lines, (900, 400), "PNG")
        elif ext == ".jpg":
            make_image(path, lines, (900, 400), "JPEG")
        elif ext == ".pdf":
            make_image(path, lines, (1240, 1754), "PDF")
        elif ext == ".xlsx":
            make_xlsx(path, lines)
        elif ext == ".docx":
            make_docx(path, lines)
        elif ext == ".sql":
            make_text(path, lines, comment="-- ")
        else:  # .txt, .hwp
            make_text(path, lines)

        print(f"create  {stored_path}")
        created += 1

    print(f"\n{created} created, {skipped} skipped -> {MEDIA_ROOT}")


if __name__ == "__main__":
    main()
