from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


PROJECT_ROOT = Path("/root/it-bidding-copilot")


@dataclass
class AssetCheck:
    label: str
    path: Path
    required: bool = True
    kind: str = "file"

    def exists(self) -> bool:
        if self.kind == "dir":
            return self.path.is_dir()
        return self.path.is_file()

    def size_bytes(self) -> int:
        if not self.exists():
            return 0
        if self.kind == "dir":
            return sum(item.stat().st_size for item in self.path.rglob("*") if item.is_file())
        return self.path.stat().st_size


def format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size_bytes}B"


def main() -> int:
    checks = [
        AssetCheck("runtime models directory", PROJECT_ROOT / "models", required=False, kind="dir"),
        AssetCheck("magic-pdf configuration", PROJECT_ROOT / "models" / "magic-pdf" / "configuration.json", required=False),
        AssetCheck(
            "business doc sample",
            PROJECT_ROOT / "docs" / "商务技术文件.docx",
            required=False,
        ),
        AssetCheck(
            "rfp sample",
            PROJECT_ROOT / "docs" / "定稿-招标文件-浙江省财务开发有限责任公司私有云项目.docx",
            required=False,
        ),
        AssetCheck("bidding template", PROJECT_ROOT / "templates" / "bidding_template.docx"),
        AssetCheck(".env file", PROJECT_ROOT / ".env", required=False),
    ]

    print("Runtime asset check")
    print(f"project_root: {PROJECT_ROOT}")
    print("")

    missing_required = []
    missing_optional = []

    for check in checks:
        exists = check.exists()
        status = "OK" if exists else ("MISSING" if check.required else "OPTIONAL_MISSING")
        size_text = format_size(check.size_bytes()) if exists else "-"
        print(f"[{status}] {check.label}: {check.path} size={size_text}")
        if not exists and check.required:
            missing_required.append(check.label)
        elif not exists:
            missing_optional.append(check.label)

    print("")

    if missing_required:
        print("Required assets missing:")
        for item in missing_required:
            print(f"- {item}")
        return 1

    if missing_optional:
        print("Optional runtime assets missing:")
        for item in missing_optional:
            print(f"- {item}")
        print("")
        print("The codebase can still be cloned and developed, but some local parsing or demo workflows may not fully reproduce this server.")
        return 0

    print("All checked runtime assets are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
