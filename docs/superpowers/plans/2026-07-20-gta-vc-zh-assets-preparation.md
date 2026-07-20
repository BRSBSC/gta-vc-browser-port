# GTA VC 简体中文散文件资源准备实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从用户提供的 Koishi 原始补丁 ZIP 中只提取并提交 GXT/TXD/DAT 三个散文件，不生成或保留二次 ZIP，也不提前接入无效的 `lang=zh`。

**Architecture:** 使用一个仅依赖 Python 标准库的命令行脚本锁定原始 ZIP 与三项资源的 SHA-256，验证 GXT 的 TABL/TKEY/TDAT 结构，再通过临时文件把三个资源写入 `game-engine/resources/zh/`。一个 `unittest` 契约检查锁定散文件集合、哈希、79 个 GXT 表和 `MAIN` 中文字符；README 可以同目录保留，本阶段不修改启动器或生成 WASM。

**Tech Stack:** Python 3.11 标准库（`argparse`、`hashlib`、`pathlib`、`struct`、`zipfile`、`unittest`）、Git。

## Global Constraints

- 只提取和提交 `wm_vcchs.gxt`、`wm_vcchs.txd`、`wm_vcchs.dat`；不得提取、执行或提交 DLL/ASI。
- 原始 ZIP 的 SHA-256 必须为 `0A8F32C2D6ADFB11D32A14F84E42F77C6C1ED1D368F5FF468B1DCCF213F46783`。
- 三项资源的 SHA-256 必须与设计规格完全一致。
- `game-engine/resources/zh/` 中的游戏资源必须恰为上述三个散文件；可保留 README，但不得包含 ZIP、DLL 或 ASI。
- GXT 必须包含 79 个唯一表和 `MAIN` 表；TKEY 记录宽度按真实 VC GXT 格式固定为 12 字节。
- 不新增 Python 依赖，不修改 `game-engine/requirements.txt`。
- 不修改 `game-engine/dist/game.js`、`index.js`、`index.html` 或任何语言入口。
- 完整 vc-sky 游戏源码、Emscripten 构建链和许可未取得前，不创建中文 WASM、`packages/zh.js` 或 `asm_consts/zh.js`。
- 原始用户 ZIP 保留在仓库根目录但由 `.gitignore` 忽略；不得把它加入 Git。
- 用户已选择重写未推送的本地实现历史，使 `koishi-assets.zip` 不出现在最终可达 Git 历史中。
- 只提交到本地 Git；未收到明确请求前不推送。

---

## 文件结构

| 文件 | 责任 |
|---|---|
| `.gitignore` | 忽略根目录原始 Koishi ZIP，并说明 Git 跟踪三个散文件。 |
| `game-engine/utils/prepare_zh_assets.py` | 校验原始补丁、验证 GXT、提取并复查三个散文件。 |
| `game-engine/utils/test_prepare_zh_assets.py` | 检查已提交散文件集合、哈希和 GXT 结构。 |
| `game-engine/resources/zh/wm_vcchs.gxt` | 简体中文菜单、剧情和任务文本。 |
| `game-engine/resources/zh/wm_vcchs.txd` | 中文字形纹理。 |
| `game-engine/resources/zh/wm_vcchs.dat` | 中文字形映射。 |
| `game-engine/resources/zh/README.md` | 记录来源、哈希、复现命令、私人使用边界和 WASM 源码门槛。 |

删除 `game-engine/resources/zh/koishi-assets.zip`。本阶段不创建其他产品文件；完整中文 WASM 集成必须在取得真实构建源后另写计划。

### Task 1: 改为生成并校验三个中文资源散文件

**Files:**
- Modify: `.gitignore`
- Modify: `game-engine/utils/prepare_zh_assets.py`
- Modify: `game-engine/utils/test_prepare_zh_assets.py`
- Modify: `game-engine/resources/zh/README.md`
- Delete: `game-engine/resources/zh/koishi-assets.zip`
- Create: `game-engine/resources/zh/wm_vcchs.gxt`
- Create: `game-engine/resources/zh/wm_vcchs.txd`
- Create: `game-engine/resources/zh/wm_vcchs.dat`

**Interfaces:**
- Consumes: 根目录 `【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip`。
- Produces: `prepare_assets(source: pathlib.Path, output_dir: pathlib.Path) -> dict[str, int]`。
- Produces: `validate_assets(directory: pathlib.Path) -> dict[str, int]`，返回 `table_count`、`cjk_count` 与 `main_cjk_count`。
- Produces: `game-engine/resources/zh/` 中三个固定名称、固定哈希的游戏资源散文件。

- [ ] **Step 1: 先把归档测试改成散文件契约测试**

用以下完整内容替换 `game-engine/utils/test_prepare_zh_assets.py`：

```python
from pathlib import Path
import sys
import unittest


UTILS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(UTILS_DIR))

try:
    from prepare_zh_assets import EXPECTED_FILES, validate_assets
except ImportError as error:
    MISSING_IMPLEMENTATION = error
else:
    MISSING_IMPLEMENTATION = None


ASSET_DIR = UTILS_DIR.parent / "resources" / "zh"


class ZhAssetsTest(unittest.TestCase):
    def test_extracted_assets_contract(self) -> None:
        if MISSING_IMPLEMENTATION is not None:
            self.fail(
                f"{MISSING_IMPLEMENTATION.__class__.__name__}: "
                f"{MISSING_IMPLEMENTATION}"
            )

        summary = validate_assets(ASSET_DIR)
        file_names = sorted(
            path.name
            for path in ASSET_DIR.iterdir()
            if path.is_file()
        )

        self.assertEqual(file_names, sorted([*EXPECTED_FILES, "README.md"]))
        self.assertEqual(summary["table_count"], 79)
        self.assertGreater(summary["cjk_count"], 100)
        self.assertGreater(summary["main_cjk_count"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认新接口尚不存在**

Run:

```powershell
python -m unittest discover -s game-engine/utils -p "test_prepare_zh_assets.py" -v
```

Expected: FAIL，包含 `ImportError` 和 `cannot import name 'validate_assets'`；这是接口尚未实现导致的断言失败，而不是语法或测试发现错误。

- [ ] **Step 3: 实现最小散文件准备与校验脚本**

用以下完整内容替换 `game-engine/utils/prepare_zh_assets.py`：

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
        tkey_offset = next(
            (
                candidate
                for candidate in (table_offset, table_offset + 8)
                if 0 <= candidate <= len(data) - 8
                and data[candidate : candidate + 4] == b"TKEY"
            ),
            None,
        )
        if tkey_offset is None:
            raise ValueError(f"{name} 表缺少 TKEY 块")

        tkey_size = struct.unpack_from("<I", data, tkey_offset + 4)[0]
        if tkey_size % 12 != 0:
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


def validate_assets(directory: Path) -> dict[str, int]:
    entry_names = {path.name for path in directory.iterdir()}
    unexpected_names = sorted(
        entry_names - set(EXPECTED_FILES) - OPTIONAL_FILES
    )
    if unexpected_names:
        raise ValueError(f"中文资源目录包含意外项目: {unexpected_names}")

    resource_names = sorted(
        entry_names & set(EXPECTED_FILES)
    )
    if resource_names != sorted(EXPECTED_FILES):
        raise ValueError(f"中文资源文件集合不匹配: {resource_names}")

    payloads: dict[str, bytes] = {}
    for name, expected_hash in EXPECTED_FILES.items():
        payload = (directory / name).read_bytes()
        if sha256_bytes(payload) != expected_hash:
            raise ValueError(f"{name} 的 SHA-256 不匹配")
        payloads[name] = payload

    return inspect_gxt(payloads["wm_vcchs.gxt"])


def prepare_assets(source: Path, output_dir: Path) -> dict[str, int]:
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
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary_files: list[Path] = []

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
            target = args.output_dir
            summary = prepare_assets(args.source, target)
        else:
            target = args.directory
            summary = validate_assets(target)
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

- [ ] **Step 4: 删除二次 ZIP 并提取三个散文件**

先确认原始输入仍存在且哈希正确：

```powershell
Test-Path -LiteralPath "【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip"
(Get-FileHash -LiteralPath "【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip" -Algorithm SHA256).Hash
```

Expected: `True`，哈希为 `0A8F32C2D6ADFB11D32A14F84E42F77C6C1ED1D368F5FF468B1DCCF213F46783`。

删除已跟踪的二次 ZIP，再生成散文件：

```powershell
git rm -- game-engine/resources/zh/koishi-assets.zip
python game-engine/utils/prepare_zh_assets.py prepare "【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip" game-engine/resources/zh
```

Expected: 退出码为 0，输出包含 `GXT 表=79` 和 `中文字符=43292`。

- [ ] **Step 5: 更新说明与忽略注释**

用以下完整内容替换 `game-engine/resources/zh/README.md`：

```markdown
# Koishi 简体中文资源

本目录用于私人构建 GTA Vice City 浏览器版简体中文支持。

以下三个散文件由仓库根目录的
`【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip`
校验后提取：

| 文件 | SHA-256 |
|---|---|
| `wm_vcchs.gxt` | `f1325caf616c3290c3ffd87c1f06c88902c7b59d65cba745c504f14c09d6d8f2` |
| `wm_vcchs.txd` | `6e7c3aaa72852ac5481c968ef9508ede88c9ce725909dc5b2107afd669a10690` |
| `wm_vcchs.dat` | `7ffa7c843678610e42c4e3fd2b2647e8ff573136463f4054443d129d2a054c3d` |

原始 ZIP 的 SHA-256：

`0A8F32C2D6ADFB11D32A14F84E42F77C6C1ED1D368F5FF468B1DCCF213F46783`

提取：

```powershell
python game-engine/utils/prepare_zh_assets.py prepare "【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip" game-engine/resources/zh
```

校验：

```powershell
python game-engine/utils/prepare_zh_assets.py verify game-engine/resources/zh
python -m unittest discover -s game-engine/utils -p "test_prepare_zh_assets.py" -v
```

原补丁中的 `Mss32.dll`、`OriginalMss32.dll` 和 `wm_vcchs.asi`
是 Windows x86 可执行文件，不会提取、执行或提交。

汉化程序源码来自无名汉化组：
<https://github.com/WMHHZ/VC.SA.Plugin>，源码采用 MIT 许可证。
该源码许可证不能自动外推到 GXT/TXD/DAT；这里按用户要求仅作私人使用。

## WASM 源码门槛

当前公开仓库没有完整 vc-sky 游戏源码与可复现的 Emscripten 构建链。
在取得完整游戏目标、构建步骤、Emscripten 版本和许可前，不增加
`lang=zh`，也不创建中文 WASM、`packages/zh.js` 或
`asm_consts/zh.js`。
```

把根 `.gitignore` 末尾的注释改为：

```gitignore
# Private source archive; only the extracted GXT/TXD/DAT files are tracked.
/【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip
```

- [ ] **Step 6: 运行散文件集成测试并确认通过**

Run:

```powershell
python -m unittest discover -s game-engine/utils -p "test_prepare_zh_assets.py" -v
python game-engine/utils/prepare_zh_assets.py verify game-engine/resources/zh
```

Expected:

```text
test_extracted_assets_contract ... ok
Ran 1 test in ...
OK
OK: game-engine\resources\zh，GXT 表=79，中文字符=43292
```

- [ ] **Step 7: 验证文件、Git 和语言入口边界**

Run:

```powershell
git diff --check
Get-ChildItem -LiteralPath game-engine/resources/zh -File | Select-Object -ExpandProperty Name
git ls-files | rg -i "\.(zip|dll|asi)$"
rg -n "lang=zh|vc-sky-zh|packages/zh|asm_consts/zh" game-engine/dist game-engine/README.md
git status --short
```

Expected:

- 资源目录只列出 `README.md`、`wm_vcchs.gxt`、`wm_vcchs.txd`、`wm_vcchs.dat`。
- `git ls-files | rg -i "\.(zip|dll|asi)$"` 无输出；`rg` 返回 1。
- 中文入口扫描无输出；`rg` 返回 1。
- 原始 ZIP 不出现在 `git status`，但 `Test-Path` 仍为 `True`。
- 工作区只包含本任务列出的产品文件变更。

- [ ] **Step 8: 提交散文件实现**

```powershell
git add -- .gitignore game-engine/utils/prepare_zh_assets.py game-engine/utils/test_prepare_zh_assets.py game-engine/resources/zh/README.md game-engine/resources/zh/wm_vcchs.gxt game-engine/resources/zh/wm_vcchs.txd game-engine/resources/zh/wm_vcchs.dat
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: store Chinese localization assets unpacked"
```

Expected: 暂存区不含原始 ZIP、二次 ZIP、DLL、ASI、依赖、启动器或 WASM 改动。

- [ ] **Step 9: 重写未推送实现历史，彻底移除二次 ZIP**

本步骤只在前述测试、任务审查通过且工作区干净后执行。用户已明确选择方案一，允许重写尚未推送的本地提交。固定重写基点为：

`5699ac7c0e34edd19660ce4281806cd754a6b1e6`

Run:

```powershell
$rewriteBase = "5699ac7c0e34edd19660ce4281806cd754a6b1e6"
git status --short
git diff --name-status "$rewriteBase..HEAD"
git reset --soft $rewriteBase
git diff --cached --check
git diff --cached --name-only
git commit -m "feat: prepare extracted Chinese localization assets"
git rev-list --objects HEAD | rg "game-engine/resources/zh/koishi-assets.zip"
```

Expected:

- 重写前 `git status --short` 无输出。
- 重写后的单一新提交包含已批准的规格/计划修订、脚本、测试、README 和三个散文件。
- `git diff --cached --name-only` 不包含原始 ZIP 或 `koishi-assets.zip`。
- 最后一条 `rg` 无输出并返回 1，证明最终可达 Git 历史没有二次 ZIP 对象。
- 不执行 `git push`。

## 后续计划入口

本计划完成后，仓库只具备经过固定哈希验证的三个中文资源散文件，不具备可运行的中文游戏。

只有拿到以下全部输入后，才编写第二份“中文 WASM 原生移植实施计划”：

1. 完整 vc-sky/reVC 游戏源码仓库地址和固定提交号；
2. 包含 `BUILD_DZ`、异步资源和虚拟文件系统适配的游戏构建目标；
3. 固定 Emscripten 版本及生成 WASM、运行时 JS、`ASM_CONSTS` 的准确命令；
4. 使用当前英语数据包进入主菜单的基线验证方法；
5. 允许私人修改和构建的明确授权；
6. 使用 `char16_t`/`uint16_t` 和 `static_assert(sizeof(CharType) == 2)` 固定中文字符为 16 位，并显式转换 reVC 字符缓冲区。

任一输入缺失时，停止在本计划的资源准备成果，不转向二进制补丁、HTML 字幕覆盖或重新制作传统 reVC 浏览器端口。
