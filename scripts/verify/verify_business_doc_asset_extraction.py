import re
import sys
from pathlib import Path

ROOT = Path("/root/it-bidding-copilot")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.docling_wrapper import DoclingWrapper
from utils.business_doc_asset_extractor import BusinessDocAssetExtractor


DOC_PATH = ROOT / "docs/商务技术文件.docx"


def extract_sections(markdown: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = "ROOT"
    current_lines: list[str] = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = line.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))
    return sections


def main() -> None:
    result = DoclingWrapper().convert(str(DOC_PATH))
    markdown = result["markdown"]
    sections = extract_sections(markdown)
    extracted = BusinessDocAssetExtractor().extract(markdown, result["images"])

    section_titles = [title for title, _lines in sections]
    certificate_titles = [title for title in section_titles if re.search(r"证书|营业执照|资质", title)]
    personnel_titles = [title for title in section_titles if re.search(r"简历|社保|项目负责人|团队人员", title)]
    authorization_titles = [title for title in section_titles if re.search(r"授权|法定代表人", title)]

    print(
        {
            "markdown_length": len(markdown),
            "sections_total": len(sections),
            "images_total": len(result["images"]),
            "certificates_total": len(extracted["certificates"]),
            "cases_total": len(extracted["cases"]),
            "personnel_total": len(extracted["personnel"]),
            "authorizations_total": len(extracted["authorizations"]),
            "social_security_total": len(extracted["social_security"]),
            "certificate_titles_preview": certificate_titles[:20],
            "personnel_titles_preview": personnel_titles[:20],
            "authorization_titles_preview": authorization_titles[:20],
        }
    )

    print("\n=== structured previews ===")
    print({"certificates_preview": extracted["certificates"][:8]})
    print({"cases_preview": extracted["cases"][:8]})
    print({"personnel_preview": extracted["personnel"][:8]})
    print({"authorizations_preview": extracted["authorizations"][:4]})
    print({"social_security_preview": extracted["social_security"][:4]})

    target_titles = [
        "5.1营业执照",
        "8.2公司各项资质证书",
        "8.2.1 ISO9001质量管理体系证书",
        "8.2.2 ISO14000环境认证体系证书",
        "9.4.1.1项目负责人证书",
        "9.4.1.3项目负责人社保证明",
    ]
    for title, lines in sections:
        if title in target_titles:
            print(f"\n=== {title} ===")
            print("\n".join(lines[:20]))


if __name__ == "__main__":
    main()
