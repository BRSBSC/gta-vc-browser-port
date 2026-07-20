# GTA VC 简体中文资源准备实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把用户提供的 Koishi 汉化补丁净化为可校验、可提交的 GXT/TXD/DAT 资源归档，并明确阻止在完整 vc-sky 构建源缺失时接入无效的 `lang=zh`。

**Architecture:** 使用一个仅依赖 Python 标准库的命令行脚本校验原始 ZIP 和三个资源的 SHA-256，验证 GXT 表结构，然后生成只含 GXT/TXD/DAT、成员顺序与时间戳固定的 ZIP。一个 `unittest` 集成检查锁定归档文件列表、哈希、79 个 GXT 表和中文字符；本阶段不修改启动器、不生成 WASM。

**Tech Stack:** Python 3.11 标准库（`argparse`、`hashlib`、`struct`、`zipfile`、`unittest`）、Git。

## Global Constraints

- 仅处理 `wm_vcchs.gxt`、`wm_vcchs.txd`、`wm_vcchs.dat`；不得执行或提交 DLL/ASI。
- 原始 ZIP 的 SHA-256 必须为 `0A8F32C2D6ADFB11D32A14F84E42F77C6C1ED1D368F5FF468B1DCCF213F46783`。
- 当前工作区未检测到原始 ZIP；执行生成步骤前必须由用户把同名文件重新放回仓库根目录，不得用名称或哈希不同的补丁替代。
- 三项资源的 SHA-256 必须与设计规格完全一致。
- 生成归档必须只包含三个平铺文件名，不保留 Windows 可执行文件或原目录结构。
- 不新增 Python 依赖，不修改 `game-engine/requirements.txt`。
- 不修改 `game-engine/dist/game.js`、`index.js`、`index.html` 或任何语言入口。
- 完整 vc-sky 游戏源码、Emscripten 构建链和许可未取得前，不创建假的中文 WASM、`packages/zh.js` 或 `asm_consts/zh.js`。
- 只提交到本地 Git；未收到明确请求前不推送。

---

## 文件结构

| 文件 | 责任 |
|---|---|
| `.gitignore` | 忽略根目录中的原始 Koishi ZIP，防止把 DLL/ASI 一起提交。 |
| `game-engine/utils/prepare_zh_assets.py` | 校验原始补丁、验证 GXT、生成并复查净化归档。 |
| `game-engine/utils/test_prepare_zh_assets.py` | 对提交后的净化归档执行一个可重复的集成检查。 |
| `game-engine/resources/zh/koishi-assets.zip` | 仅保存 GXT/TXD/DAT 的压缩资源。 |
| `game-engine/resources/zh/README.md` | 记录来源、哈希、生成命令、私人使用边界和 vc-sky 源码门槛。 |

本阶段不创建其他文件。完整中文 WASM 集成必须在取得真实构建源后另写第二份实施计划。

### Task 1: 生成并锁定净化后的中文资源归档

**Files:**
- Modify: `.gitignore`
- Create: `game-engine/utils/prepare_zh_assets.py`
- Create: `game-engine/utils/test_prepare_zh_assets.py`
- Create: `game-engine/resources/zh/koishi-assets.zip`
- Create: `game-engine/resources/zh/README.md`

**Interfaces:**
- Consumes: 根目录 `【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip`，SHA-256 固定为 `0A8F32C2D6ADFB11D32A14F84E42F77C6C1ED1D368F5FF468B1DCCF213F46783`。
- Produces: `prepare_archive(source: pathlib.Path, output: pathlib.Path) -> dict[str, int]`。
- Produces: `validate_archive(path: pathlib.Path) -> dict[str, int]`，返回 `table_count`、`cjk_count` 与 `main_cjk_count`。
- Produces: `game-engine/resources/zh/koishi-assets.zip`，成员顺序与名称精确为 `wm_vcchs.gxt`、`wm_vcchs.txd`、`wm_vcchs.dat`。

- [ ] **Step 1: 先写会失败的归档契约测试**

创建 `game-engine/utils/test_prepare_zh_assets.py`：

```python
from pathlib import Path
import sys
import unittest
import zipfile


UTILS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(UTILS_DIR))

from prepare_zh_assets import EXPECTED_FILES, FIXED_TIMESTAMP, validate_archive


ARCHIVE = UTILS_DIR.parent / "resources" / "zh" / "koishi-assets.zip"


class ZhAssetsTest(unittest.TestCase):
    def test_sanitized_archive_contract(self) -> None:
        summary = validate_archive(ARCHIVE)

        with zipfile.ZipFile(ARCHIVE) as archive:
            infos = archive.infolist()
            self.assertEqual(
                [info.filename for info in infos],
                list(EXPECTED_FILES),
            )
            for info in infos:
                self.assertEqual(info.date_time, FIXED_TIMESTAMP)
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.external_attr >> 16, 0o100644)

        self.assertEqual(summary["table_count"], 79)
        self.assertGreater(summary["cjk_count"], 100)
        self.assertGreater(summary["main_cjk_count"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认它因实现尚不存在而失败**

Run:

```powershell
python -m unittest discover -s game-engine/utils -p "test_prepare_zh_assets.py" -v
```

Expected: FAIL，包含 `ModuleNotFoundError: No module named 'prepare_zh_assets'`。

- [ ] **Step 3: 实现最小资源准备与校验脚本**

创建 `game-engine/utils/prepare_zh_assets.py`：

```python
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import sys
import zipfile


SOURCE_SHA256 = "0a8f32c2d6adfb11d32a14f84e42f77c6c1ed1d368f5ff468b1dccf213f46783"

SOURCE_ENTRIES = {
    "plugins/wm_vcchs/wm_vcchs.gxt": (
        "wm_vcchs.gxt",
        "f1325caf616c3290c3ffd87c1f06c88902c7b59d65cba745c504f14c09d6d8f2",
    ),
    "plugins/wm_vcchs/wm_vcchs.txd": (
        "wm_vcchs.txd",
        "6e7c3aaa72852ac5481c968ef9508ede88c9ce725909dc5b2107afd669a10690",
    ),
    "plugins/wm_vcchs/wm_vcchs.dat": (
        "wm_vcchs.dat",
        "7ffa7c843678610e42c4e3fd2b2647e8ff573136463f4054443d129d2a054c3d",
    ),
}

EXPECTED_FILES = {
    destination: digest
    for destination, digest in SOURCE_ENTRIES.values()
}

FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


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

    records: list[tuple[str, int]] = []
    for offset in range(8, 8 + table_bytes, 12):
        name = data[offset : offset + 8].split(b"\0", 1)[0].decode("ascii")
        table_offset = struct.unpack_from("<I", data, offset + 8)[0]
        records.append((name, table_offset))

    table_names = [name for name, _ in records]
    if len(records) != 79 or "MAIN" not in table_names:
        raise ValueError("wm_vcchs.gxt 必须包含 79 个表和 MAIN 表")
    if len(set(table_names)) != len(table_names):
        raise ValueError("wm_vcchs.gxt 包含重复表名")

    cjk_count = 0
    main_cjk_count = 0
    for name, table_offset in records:
        candidates = (table_offset, table_offset + 8)
        tkey_offset = next(
            (
                candidate
                for candidate in candidates
                if 0 <= candidate <= len(data) - 8
                and data[candidate : candidate + 4] == b"TKEY"
            ),
            None,
        )
        if tkey_offset is None:
            raise ValueError(f"{name} 表缺少 TKEY 块")

        tkey_size = struct.unpack_from("<I", data, tkey_offset + 4)[0]
        if tkey_size % 8 != 0:
            raise ValueError(f"{name} 表的 TKEY 长度无效")
        tdat_offset = tkey_offset + 8 + tkey_size
        if (
            not 0 <= tdat_offset <= len(data) - 8
            or data[tdat_offset : tdat_offset + 4] != b"TDAT"
        ):
            raise ValueError(f"{name} 表缺少 TDAT 块")

        tdat_size = struct.unpack_from("<I", data, tdat_offset + 4)[0]
        payload_start = tdat_offset + 8
        payload_end = payload_start + tdat_size
        payload = data[payload_start:payload_end]
        if payload_end > len(data) or len(payload) % 2 != 0:
            raise ValueError(f"{name} 表的 TDAT 长度无效")

        table_cjk_count = sum(
            0x3400 <= codepoint <= 0x9FFF
            for (codepoint,) in struct.iter_unpack("<H", payload)
        )
        cjk_count += table_cjk_count
        if name == "MAIN":
            main_cjk_count = table_cjk_count

    if cjk_count <= 100:
        raise ValueError("wm_vcchs.gxt 未检测到足够的中文字符")
    if main_cjk_count == 0:
        raise ValueError("wm_vcchs.gxt 的 MAIN 表未检测到中文字符")

    return {
        "table_count": len(records),
        "cjk_count": cjk_count,
        "main_cjk_count": main_cjk_count,
    }


def validate_archive(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != list(EXPECTED_FILES):
            raise ValueError(f"净化归档成员不匹配: {names}")

        payloads: dict[str, bytes] = {}
        for name, expected_hash in EXPECTED_FILES.items():
            if Path(name).suffix.lower() in {".dll", ".asi"}:
                raise ValueError(f"净化归档包含可执行插件: {name}")
            payload = archive.read(name)
            if sha256_bytes(payload) != expected_hash:
                raise ValueError(f"{name} 的 SHA-256 不匹配")
            payloads[name] = payload

    return inspect_gxt(payloads["wm_vcchs.gxt"])


def prepare_archive(source: Path, output: Path) -> dict[str, int]:
    if sha256_file(source) != SOURCE_SHA256:
        raise ValueError("原始 Koishi ZIP 的 SHA-256 不匹配")

    payloads: dict[str, bytes] = {}
    with zipfile.ZipFile(source) as archive:
        for source_name, (destination, expected_hash) in SOURCE_ENTRIES.items():
            payload = archive.read(source_name)
            if sha256_bytes(payload) != expected_hash:
                raise ValueError(f"{source_name} 的 SHA-256 不匹配")
            payloads[destination] = payload

    inspect_gxt(payloads["wm_vcchs.gxt"])
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f"{output.name}.tmp")

    if temporary.exists():
        temporary.unlink()

    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for name in EXPECTED_FILES:
                info = zipfile.ZipInfo(name, FIXED_TIMESTAMP)
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(
                    info,
                    payloads[name],
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        summary = validate_archive(temporary)
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="准备或校验 Koishi 中文资源")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="从原始补丁生成净化归档")
    prepare.add_argument("source", type=Path)
    prepare.add_argument("output", type=Path)

    verify = commands.add_parser("verify", help="校验净化归档")
    verify.add_argument("archive", type=Path)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "prepare":
            summary = prepare_archive(args.source, args.output)
            target = args.output
        else:
            summary = validate_archive(args.archive)
            target = args.archive
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(
        f"OK: {target}，GXT 表={summary['table_count']}，"
        f"中文字符={summary['cjk_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 从用户 ZIP 生成净化归档**

先确认用户已把原始 ZIP 重新放回仓库根目录：

```powershell
Test-Path -LiteralPath "【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip"
```

Expected: `True`。若为 `False`，停止任务并请用户重新提供文件，不执行后续命令。

Run:

```powershell
python game-engine/utils/prepare_zh_assets.py prepare "【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip" game-engine/resources/zh/koishi-assets.zip
```

Expected: 退出码为 0，输出以 `OK:` 开头，`GXT 表=79`，中文字符数大于 100。

随后只列出归档成员：

```powershell
python -c "import zipfile; z=zipfile.ZipFile(r'game-engine/resources/zh/koishi-assets.zip'); print('\n'.join(z.namelist()))"
```

Expected:

```text
wm_vcchs.gxt
wm_vcchs.txd
wm_vcchs.dat
```

- [ ] **Step 5: 记录来源、边界和复现命令**

创建 `game-engine/resources/zh/README.md`：

```markdown
# Koishi 简体中文资源

本目录用于私人构建 GTA Vice City 浏览器版简体中文支持。

`koishi-assets.zip` 由根目录的
`【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip`
净化生成，只包含：

| 文件 | SHA-256 |
|---|---|
| `wm_vcchs.gxt` | `f1325caf616c3290c3ffd87c1f06c88902c7b59d65cba745c504f14c09d6d8f2` |
| `wm_vcchs.txd` | `6e7c3aaa72852ac5481c968ef9508ede88c9ce725909dc5b2107afd669a10690` |
| `wm_vcchs.dat` | `7ffa7c843678610e42c4e3fd2b2647e8ff573136463f4054443d129d2a054c3d` |

原始 ZIP 的 SHA-256：

`0A8F32C2D6ADFB11D32A14F84E42F77C6C1ED1D368F5FF468B1DCCF213F46783`

生成：

```powershell
python game-engine/utils/prepare_zh_assets.py prepare "【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip" game-engine/resources/zh/koishi-assets.zip
```

校验：

```powershell
python game-engine/utils/prepare_zh_assets.py verify game-engine/resources/zh/koishi-assets.zip
python -m unittest discover -s game-engine/utils -p "test_prepare_zh_assets.py" -v
```

原补丁中的 `Mss32.dll`、`OriginalMss32.dll` 和 `wm_vcchs.asi`
是 Windows x86 可执行文件，不会执行或进入净化归档。

汉化程序源码来自无名汉化组：
<https://github.com/WMHHZ/VC.SA.Plugin>，源码采用 MIT 许可证。
该源码许可证不能自动外推到 GXT/TXD/DAT；这里按用户要求仅作私人使用。

## WASM 源码门槛

当前公开仓库没有完整 vc-sky 游戏源码与可复现的 Emscripten 构建链。
在取得完整游戏目标、构建步骤、Emscripten 版本和许可前，不增加
`lang=zh`，也不创建假的中文 WASM、`packages/zh.js` 或
`asm_consts/zh.js`。
```

在根 `.gitignore` 的末尾加入：

```gitignore

# Private source archive; only the sanitized GXT/TXD/DAT archive is tracked.
/【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip
```

- [ ] **Step 6: 运行集成测试并确认通过**

Run:

```powershell
python -m unittest discover -s game-engine/utils -p "test_prepare_zh_assets.py" -v
python game-engine/utils/prepare_zh_assets.py verify game-engine/resources/zh/koishi-assets.zip
```

Expected:

```text
test_sanitized_archive_contract ... ok
Ran 1 test in ...
OK
OK: game-engine\resources\zh\koishi-assets.zip，GXT 表=79，中文字符=...
```

- [ ] **Step 7: 验证 Git 边界和仓库完整性**

Run:

```powershell
git diff --check
git status --short
git ls-files | rg -i "\.(dll|asi)$"
```

Expected:

- `git diff --check` 无输出，退出码为 0。
- `git status --short` 只显示本任务列出的共五个路径；计划文档应已在本计划开始实施前单独提交。
- `git ls-files | rg -i "\.(dll|asi)$"` 无输出；`rg` 因无匹配返回 1 是预期结果。
- 根目录原始 ZIP 不再出现在 `git status`，但文件仍保留在磁盘上。

再确认没有过早接入中文入口：

```powershell
rg -n "lang=zh|vc-sky-zh|packages/zh|asm_consts/zh" game-engine/dist game-engine/README.md
```

Expected: 无输出，`rg` 返回 1。

- [ ] **Step 8: 提交资源准备阶段**

```powershell
git add -- .gitignore game-engine/utils/prepare_zh_assets.py game-engine/utils/test_prepare_zh_assets.py game-engine/resources/zh/README.md game-engine/resources/zh/koishi-assets.zip
git diff --cached --check
git diff --cached --name-only
git commit -m "feat: prepare sanitized Chinese localization assets"
```

Expected: `git diff --cached --check` 无输出，暂存区只包含上述五个路径；提交不包含原始 ZIP、DLL、ASI、计划文档或启动器改动。

## 后续计划入口

本计划完成后，仓库只具备安全、可复现的汉化资源输入，不具备可运行的中文游戏。

只有拿到以下全部输入后，才编写第二份“中文 WASM 原生移植实施计划”：

1. 完整 vc-sky/reVC 游戏源码仓库地址和固定提交号；
2. 包含 `BUILD_DZ`、异步资源和虚拟文件系统适配的游戏构建目标；
3. 固定 Emscripten 版本及生成 WASM、运行时 JS、`ASM_CONSTS` 的准确命令；
4. 使用当前英语数据包进入主菜单的基线验证方法；
5. 允许私人修改和构建的明确授权。
6. 中文字符类型固定为 16 位的方案：使用 `char16_t`/`uint16_t`、
   `static_assert(sizeof(CharType) == 2)`，并显式转换 reVC 字符缓冲区，
   不直接复用 Emscripten 下通常为 32 位的 `wchar_t`。

任一输入缺失时，停止在本计划的资源准备成果，不转向二进制补丁、HTML 字幕覆盖或重新制作传统 reVC 浏览器端口。
