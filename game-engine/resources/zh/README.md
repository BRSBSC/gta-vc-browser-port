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
