# GTA Vice City 浏览器版简体中文设计

## 状态

- 日期：2026-07-20
- 状态：设计方向和书面规格已于 2026-07-20 经用户复核批准
- 目标：增加简体中文菜单和剧情字幕，保留英文语音
- 分发方式：先提交到本地 Git 仓库，不自动推送

## 背景

当前游戏启动层只支持英语和俄语：

- `game-engine/dist/game.js` 只识别 `lang=en` 与 `lang=ru`，并为两种语言选择独立的 `.data.br` 和 `.wasm.br`。
- `game-engine/dist/index.js` 为两种语言选择各自的资源清单和 `ASM_CONSTS`。
- `game-engine/dist/index.html` 的语言下拉框只有英语和俄语。
- 英语资源清单包含 `american.gxt`、`fonts.txd` 等游戏文本和字库；俄语版还使用独立 WASM 和更大的字体资源。
- 新配置默认 `Subtitles=0`，因此即使加入中文文本，也需要为新的中文配置开启字幕。

公开源码审查还确认了一个硬前提：当前仓库及其直接上游只包含启动器、服务端和预编译 WASM，没有完整 `vc-sky` 游戏源码与可复现的 Emscripten 构建链。

- `caiiiycuk/sky` 的 `vc` 分支包含 revcDOS 使用的 Emscripten 适配，但根目标只是 `sky` 静态库，不包含 reVC 游戏入口。
- `Carter54git/revcdos` 提供数据转换器和预编译 release，没有生成 `index.wasm` 的完整 C++ 工程。
- 传统 reVC 镜像没有 revcDOS 的 `BUILD_DZ`、`Module.getAsyncUrl` 和当前产物拆分链，不能作为无成本替换。

用户提供的补丁：

`【汉化补丁】罪恶都市无名汉化组汉化补丁 v1.0(Koishi).zip`

原始 ZIP 的 SHA-256：

`0A8F32C2D6ADFB11D32A14F84E42F77C6C1ED1D368F5FF468B1DCCF213F46783`

补丁包含 Windows x86 的 DLL/ASI 加载链，以及以下三项可迁移资源：

| 资源 | 用途 | SHA-256 |
|---|---|---|
| `wm_vcchs.gxt` | UTF-16 游戏菜单、任务和剧情文本 | `f1325caf616c3290c3ffd87c1f06c88902c7b59d65cba745c504f14c09d6d8f2` |
| `wm_vcchs.txd` | 中文字形纹理 | `6e7c3aaa72852ac5481c968ef9508ede88c9ce725909dc5b2107afd669a10690` |
| `wm_vcchs.dat` | 65536 个 UTF-16 字符到 64×64 字形图集的映射 | `7ffa7c843678610e42c4e3fd2b2647e8ff573136463f4054443d129d2a054c3d` |

静态检查确认 GXT 使用标准 `TABL/TKEY/TDAT` 结构，共 79 个文本表，包含 `MAIN`、`ASSIN`、`CUBAN`、`FINALE` 等任务文本。

无名汉化组已公开 `WMHHZ/VC.SA.Plugin` 源码并使用 MIT 许可证。可复用的是其中的 Unicode 字符映射、字体纹理加载、字符宽度、自动换行和渲染逻辑；Windows 地址注入、DLL/ASI 加载和 GInput 依赖不能带入浏览器版。

## 方案比较

### 方案 A：取得完整 vc-sky 构建源后原生移植（采用）

把无名汉化组的必要渲染逻辑直接接入 reVC 的 `CFont` 和文本加载链，生成中文 WASM 与中文数据包。

优点：菜单、剧情字幕、任务提示和自动换行都使用游戏原生状态，行为最稳定。

前提：必须先取得完整 vc-sky 游戏源码、构建说明、Emscripten 版本和允许私人修改构建的授权。公开仓库目前不足以完成这一步。

代价：在前提满足前，只能准备和校验汉化资源，不能生成可运行的中文 WASM。

### 方案 B：从传统 reVC 重新制作浏览器端口（本次不采用）

从传统 reVC 镜像开始补 Emscripten、WebGL/音频、异步资源、虚拟文件系统和当前 JS 产物拆分。

问题：这相当于新建浏览器游戏端口，不是当前仓库的汉化改动；源码许可也不明确。除非确认无法取得 vc-sky 完整源码且用户另行批准扩大范围，否则不进入这条路线。

### 方案 C：浏览器 HTML 字幕覆盖层（不采用）

在 Canvas 上方显示 DOM 字幕。

问题：仍需从 WASM 内存识别当前字幕，无法可靠覆盖菜单、任务提示和颜色标记；维护成本高于原生移植。

### 方案 D：直接加载原补丁 DLL/ASI（不可行）

原补丁是 Windows x86 PE 文件。浏览器 WebAssembly 无法执行 `Mss32.dll` 或 `wm_vcchs.asi`，当前项目也没有 `LoadLibrary`、ASI 或 CLEO 加载链。

### 已排除的复用候选

`PolyMath-XK/TExtender` 虽然支持 UTF-8 和 TTF，但明确依赖 Windows D3D9/D3DX，不能用于当前浏览器 RenderWare/WebGL 路径。

## 总体架构

实现有一个前置门槛和四个边界清晰的部分：

0. **源码门槛**：取得并验证完整 vc-sky 游戏源码、构建方式和许可；未通过时不声明中文功能可运行。
1. **可复现的 vc-sky WebAssembly 构建**：从固定提交构建能进入现有英文菜单的基础 WASM。
2. **中文文本与字体渲染**：在 vc-sky/reVC 源码中直接集成最小中文渲染逻辑，不运行任何 DLL/ASI。
3. **中文数据包**：以现有英文资源包为基线，替换 GXT 并加入中文 TXD/DAT，生成匹配的资源清单。
4. **现有启动器接入**：沿用英语/俄语语言选择模式增加 `zh`，不重构启动器。

中文运行时必须成对使用：

```text
lang=zh
  -> vc-sky-zh-v6.wasm.br
  -> vc-sky-zh-v6.data.br
  -> modules/packages/zh.js
  -> modules/asm_consts/zh.js
```

任何一项缺失或版本不匹配都不得静默回退或混用英语文件。

## 组件设计

### 1. 源码门槛与 WebAssembly 构建基线

接受的构建源必须同时包含：

- 完整的 vc-sky/reVC 游戏目标，而不只是 `sky` 静态库；
- revcDOS 使用的 Emscripten、`BUILD_DZ`、异步资源和虚拟文件系统适配；
- 生成 WASM、运行时 JS、`ASM_CONSTS` 和资源清单的步骤；
- 明确的源码提交号、Emscripten 版本和私人修改/构建许可。

最短路径是向 Carter54git、DOS.Zone 或 caiiiycuk 获取上述构建源或由其提供中文构建服务。未满足这些条件时：

- 可以把净化后的 GXT/TXD/DAT 和静态校验加入本地 Git；
- 不增加 `lang=zh`，避免入口指向不存在的 WASM；
- 不尝试修改现有二进制 WASM；
- 不自动扩大为“重做 reVC 浏览器端口”。

取得完整构建源后，它只作为私人构建输入，不整仓复制进本项目。实现以固定版本的 Emscripten 容器和最小补丁集完成构建，最终在仓库中保留：

- 固定的源码提交号；
- 固定的编译器容器版本或摘要；
- 本项目自己的 Emscripten 适配与中文补丁；
- 可重复执行的单一构建入口。

源码门槛通过后的第一项验收是用当前英语数据包启动到主菜单。基础构建未通过前，不接入中文资源，也不修改正式语言选择逻辑。这样可以把“构建复现问题”和“中文渲染问题”分开定位。

### 2. 中文渲染

从 `WMHHZ/VC.SA.Plugin` 只迁移以下能力：

- 读取 131072 字节的 UTF-16 字形映射表；
- 从 TXD 加载普通与倾斜字形纹理；
- 中文字符宽度计算；
- 按中文字符边界换行；
- 从 64×64 图集中计算 UV 并绘制字符；
- 在字体缓冲区渲染中文字符。

Emscripten 端的文本、映射表和字体索引必须显式使用 `char16_t` 或
`uint16_t`，并用 `static_assert(sizeof(CharType) == 2)` 锁定 16 位布局；
不得直接沿用上游 Windows 构建中的 `wchar_t`，因为 Emscripten 下它通常
为 32 位。与 reVC 原有字符缓冲区之间使用显式转换，避免破坏 GXT/DAT
偏移和 131072 字节映射表布局。

以下内容不迁移：

- Windows 固定内存地址和 `injector::MakeJMP/MakeCALL`；
- `GetModuleHandle`、DLL/ASI 生命周期；
- GInput 的函数地址和按钮图标依赖；
- 与中文显示无关的字体 API 抽象。

颜色标记、控制器标记和英语字符继续使用 reVC 现有解析与渲染路径。中文字符只在 `codepoint >= 0x80` 时进入中文图集路径。

### 3. 中文资源

Git 中保存一个净化后的资源归档：

`game-engine/resources/zh/koishi-assets.zip`

归档只包含 GXT、TXD、DAT，不包含 `Mss32.dll`、`OriginalMss32.dll` 或 `wm_vcchs.asi`。构建前必须校验三项资源的 SHA-256。

中文数据包使用以下虚拟路径：

```text
/vc-assets/local/text/american.gxt
/vc-assets/local/models/wm_vcchs.txd
/vc-assets/local/data/wm_vcchs.dat
```

使用 `american.gxt` 槽位可以保持 `Language=0`，避免修改存档和菜单语言枚举。其余游戏、音频和地图资源沿用英语包，因而语音保持英文。

资源打包器读取现有英语清单，替换 `american.gxt`、加入两个中文字库文件，并重新计算所有偏移和 `remote_package_size`。`packages/zh.js` 必须由打包结果生成，不能手工复制英语偏移。

### 4. 启动器接入

保持现有文件和调用关系，只做必要扩展：

- `game-engine/dist/game.js`：增加启动页中文文案、浏览器中文识别、`lang=zh` 和中文 WASM/data 映射。
- `game-engine/dist/index.html`：增加“简体中文”选项。
- `game-engine/dist/index.js`：选择 `packages/zh.js` 和 `asm_consts/zh.js`。
- `game-engine/README.md`：记录 `lang=zh`。

首次创建中文配置时使用 `Subtitles=1`。已有本地配置继续尊重用户设置，不强制覆盖。

中文 WASM 的内存布局未验证前，中文模式不加载作弊模块；英语和俄语作弊行为保持原样。只有验证中文构建对应地址后才恢复该功能。

## 数据流

```text
Koishi 原始 ZIP
  -> 静态提取并校验 GXT/TXD/DAT
  -> 净化资源归档进入 Git

取得的固定 vc-sky 源码 + Emscripten 适配 + 中文渲染补丁
  -> vc-sky-zh-v6.wasm
  -> Brotli 压缩

英语 data 包 + 中文 GXT/TXD/DAT
  -> 重建连续 data 文件和 zh.js 偏移清单
  -> vc-sky-zh-v6.data.br

浏览器 ?lang=zh
  -> 同时加载 zh WASM、data、packages 和 ASM_CONSTS
  -> 英文音频 + 中文菜单/字幕
```

## 错误处理与安全边界

- 不执行、加载或发布原补丁中的 DLL/ASI。
- 输入资源哈希不匹配时立即停止构建。
- 完整 vc-sky 构建源未取得或基础英文 WASM 无法启动时，停止在资源准备阶段。
- 源码提交、编译器版本、WASM、`ASM_CONSTS` 和数据清单必须作为同一版本产物。
- 中文资源请求失败时显示明确加载错误，不自动混用英语 WASM 或数据包。
- 打包器发现缺失文件、重叠偏移或最终大小不一致时以非零状态退出。
- 英语和俄语路径不经过中文资源处理，降低回归范围。

## Git 与分发约束

- 设计批准授权的是本地 Git 提交；推送是单独操作，未收到明确请求前不推送。
- 原始用户 ZIP 保持未跟踪；产品提交只加入净化后的资源归档及必要源码、脚本和文档。
- 汉化程序移植代码保留无名汉化组 MIT 版权和许可声明。
- 翻译与字库资源缺少明确再分发许可，本设计按用户私人使用决定纳入本地仓库；若以后推送到公开仓库或公共 GHCR，需要再次确认分发风险。

## 验证策略

不新增测试框架，保留一个可直接运行的资源检查和必要的构建/浏览器验收。

### 自动检查

1. 净化资源归档不含 `.dll` 或 `.asi`。
2. 三项资源 SHA-256 与设计记录一致。
3. GXT 包含 79 个表且 `MAIN` 中存在中文字符。
4. 中文数据清单所有区间连续、不重叠，最终偏移等于 `remote_package_size`。
5. 取得完整构建源后，基础英文 WASM 能使用当前数据包进入菜单。
6. 中文 WASM 能完成实例化，且与生成的 `ASM_CONSTS` 配套。
7. `git diff --check` 和项目现有语法检查通过。

### 浏览器验收

1. `?lang=zh` 的启动页和配置下拉显示简体中文。
2. 游戏主菜单、暂停菜单和设置菜单显示中文且没有方框或乱码。
3. 至少验证一个过场剧情字幕和一个任务提示，英文语音正常播放。
4. 长中文文本按字符正确换行，颜色和按键标记不裸露。
5. 新中文配置默认显示字幕，关闭后能保持用户选择。
6. 保存、重新加载存档后仍能显示中文。
7. `lang=en` 和 `lang=ru` 仍能进入游戏。
8. 最终 Docker 镜像同时通过 `linux/amd64` 和 `linux/arm64` 构建；WASM 内容在两种容器架构中一致。

## 完成标准

- 已取得并固定完整 vc-sky 构建源；若未取得，则本任务只能完成资源准备，不能宣称汉化完成。
- 简体中文成为第三个可选语言。
- 中文菜单、剧情字幕和任务提示可读且稳定。
- 游戏语音保持英文。
- 原补丁可执行文件从未运行或进入产品资源。
- 英语、俄语、存档和双架构镜像构建没有回归。
- 所有中文构建输入和产物均可通过固定版本与哈希追踪。

## 明确不做

- 中文配音。
- OCR 或 HTML 字幕覆盖层。
- 通用插件加载器、ASI/CLEO 支持。
- 重写现有语言系统。
- 为中文功能进行无关项目重构。
- 在未验证内存布局前支持中文模式作弊菜单。
- 在本任务中从传统 reVC 重新制作完整浏览器端口。

## 外部来源与致谢

- 无名汉化组中文插件源码：<https://github.com/WMHHZ/VC.SA.Plugin>
- 无名汉化组 MIT 许可证：<https://github.com/WMHHZ/VC.SA.Plugin/blob/master/LICENSE>
- revcDOS 使用的局部 Emscripten 依赖：<https://github.com/caiiiycuk/sky/tree/vc>
- Carter revcDOS 二进制与数据转换器：<https://github.com/Carter54git/revcdos>
- 当前包装层的相关上游：<https://github.com/Lolendor/reVCDOS>
- 传统 reVC 源码候选（仅说明为什么不直接采用）：<https://github.com/mrxenginner/reVC>
- TExtender（仅作为已排除候选）：<https://github.com/PolyMath-XK/TExtender>
