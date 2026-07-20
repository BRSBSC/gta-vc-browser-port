from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import sys
import zipfile


SOURCE_SHA256 = "0a8f32c2d6adfb11d32a14f84e42f77c6c1ed1d368f5ff468b1dccf213f46783"
SOURCE_ENTRIES = {
    "plugins/wm_vcchs/wm_vcchs.gxt": ("wm_vcchs.gxt", "f1325caf616c3290c3ffd87c1f06c88902c7b59d65cba745c504f14c09d6d8f2"),
    "plugins/wm_vcchs/wm_vcchs.txd": ("wm_vcchs.txd", "6e7c3aaa72852ac5481c968ef9508ede88c9ce725909dc5b2107afd669a10690"),
    "plugins/wm_vcchs/wm_vcchs.dat": ("wm_vcchs.dat", "7ffa7c843678610e42c4e3fd2b2647e8ff573136463f4054443d129d2a054c3d"),
}
EXPECTED_FILES = {destination: digest for destination, digest in SOURCE_ENTRIES.values()}
OPTIONAL_FILES = {"README.md"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_gxt(data: bytes) -> dict[str, int]:
    if len(data) < 8 or data[:4] != b"TABL":
        raise ValueError("wm_vcchs.gxt 缺少 TABL 头")
    table_bytes = struct.unpack_from("<I", data, 4)[0]
    if table_bytes % 12 != 0 or 8 + table_bytes > len(data):
        raise ValueError("wm_vcchs.gxt 的 TABL 长度无效")

    records = []
    for offset in range(8, 8 + table_bytes, 12):
        name = data[offset : offset + 8].split(b"\0", 1)[0].decode("ascii")
        records.append((name, struct.unpack_from("<I", data, offset + 8)[0]))
    names = [name for name, _ in records]
    if len(records) != 79 or "MAIN" not in names or len(set(names)) != len(names):
        raise ValueError("wm_vcchs.gxt 必须包含 79 个唯一表和 MAIN 表")

    cjk_count = main_cjk_count = 0
    for name, table_offset in records:
        tkey_offset = next((candidate for candidate in (table_offset, table_offset + 8)
                            if 0 <= candidate <= len(data) - 8 and data[candidate : candidate + 4] == b"TKEY"), None)
        if tkey_offset is None:
            raise ValueError(f"{name} 表缺少 TKEY 块")
        tkey_size = struct.unpack_from("<I", data, tkey_offset + 4)[0]
        if tkey_size % 12 != 0:
            raise ValueError(f"{name} 表的 TKEY 长度无效")
        tdat_offset = tkey_offset + 8 + tkey_size
        if not 0 <= tdat_offset <= len(data) - 8 or data[tdat_offset : tdat_offset + 4] != b"TDAT":
            raise ValueError(f"{name} 表缺少 TDAT 块")
        tdat_size = struct.unpack_from("<I", data, tdat_offset + 4)[0]
        payload_start, payload_end = tdat_offset + 8, tdat_offset + 8 + tdat_size
        payload = data[payload_start:payload_end]
        if payload_end > len(data) or len(payload) % 2 != 0:
            raise ValueError(f"{name} 表的 TDAT 长度无效")
        table_cjk_count = sum(0x3400 <= codepoint <= 0x9FFF for (codepoint,) in struct.iter_unpack("<H", payload))
        cjk_count += table_cjk_count
        if name == "MAIN":
            main_cjk_count = table_cjk_count
    if cjk_count <= 100:
        raise ValueError("wm_vcchs.gxt 未检测到足够的中文字符")
    if main_cjk_count == 0:
        raise ValueError("wm_vcchs.gxt 的 MAIN 表未检测到中文字符")
    return {"table_count": len(records), "cjk_count": cjk_count, "main_cjk_count": main_cjk_count}


def validate_assets(directory: Path) -> dict[str, int]:
    entry_names = {path.name for path in directory.iterdir()}
    unexpected_names = sorted(entry_names - set(EXPECTED_FILES) - OPTIONAL_FILES)
    if unexpected_names:
        raise ValueError(f"中文资源目录包含意外项目: {unexpected_names}")
    resource_names = sorted(entry_names & set(EXPECTED_FILES))
    if resource_names != sorted(EXPECTED_FILES):
        raise ValueError(f"中文资源文件集合不匹配: {resource_names}")
    payloads = {}
    for name, expected_hash in EXPECTED_FILES.items():
        payload = (directory / name).read_bytes()
        if sha256_bytes(payload) != expected_hash:
            raise ValueError(f"{name} 的 SHA-256 不匹配")
        payloads[name] = payload
    return inspect_gxt(payloads["wm_vcchs.gxt"])


def prepare_assets(source: Path, output_dir: Path) -> dict[str, int]:
    if sha256_file(source) != SOURCE_SHA256:
        raise ValueError("原始 Koishi ZIP 的 SHA-256 不匹配")
    with zipfile.ZipFile(source) as archive:
        payloads = {}
        for source_name, (destination, expected_hash) in SOURCE_ENTRIES.items():
            payload = archive.read(source_name)
            if sha256_bytes(payload) != expected_hash:
                raise ValueError(f"{source_name} 的 SHA-256 不匹配")
            payloads[destination] = payload
    inspect_gxt(payloads["wm_vcchs.gxt"])
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary_files = []
    try:
        for name, payload in payloads.items():
            temporary = output_dir / f".{name}.tmp"
            temporary_files.append(temporary)
            temporary.write_bytes(payload)
            if sha256_file(temporary) != EXPECTED_FILES[name]:
                raise ValueError(f"{name} 的临时文件 SHA-256 不匹配")
        for name, temporary in zip(payloads, temporary_files):
            temporary.replace(output_dir / name)
    finally:
        for temporary in temporary_files:
            if temporary.exists():
                temporary.unlink()
    return validate_assets(output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="准备或校验 Koishi 中文资源散文件")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="从原始补丁提取三个散文件")
    prepare.add_argument("source", type=Path)
    prepare.add_argument("output_dir", type=Path)
    verify = commands.add_parser("verify", help="校验三个散文件")
    verify.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            target, summary = args.output_dir, prepare_assets(args.source, args.output_dir)
        else:
            target, summary = args.directory, validate_assets(args.directory)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"OK: {target}，GXT 表={summary['table_count']}，中文字符={summary['cjk_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
