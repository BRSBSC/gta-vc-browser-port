# 调研发现与决定

## 用户需求
- 审查当前项目，找出真正值得处理的优化项。
- 扩展 GitHub 容器镜像构建，支持 ARM 架构。
- 始终使用简体中文回应。
- 优先选择可工作的最小改动，不增加推测性抽象或依赖。
- 计划文档使用中文。
- ARM 目标机器是甲骨文云 ARM 实例，对应 `linux/arm64`。

## 调研发现
- 本地记忆索引没有本项目条目，结论全部来自当前工作区。
- 开始任务前仓库干净；当前 `git status --short` 只显示本次会话创建的 `.planning/`。
- 仓库包含两个主要组件：Python `game-engine/` 和 Astro/TypeScript `web-launcher/`。
- 近期提交集中在启动器体验、SEO 和运行端口调整。
- 仓库内没有 `AGENTS.md`，遵循用户消息中给出的“始终使用简体中文”。
- `.github/workflows/build-engine.yml` 已使用 Buildx，但未声明 `platforms`，因此当前托管的 `ubuntu-latest` 任务只发布运行器原生架构。
- 实时检查 GHCR 后确认：`ghcr.io/developeranku/gta-vc-browser-port-engine:latest` 只有 `linux/amd64`；另一个 `unknown/unknown` 是证明清单，不是可运行平台。
- `python:3.11-slim` 当前同时提供 `linux/amd64` 和 `linux/arm64/v8`，Dockerfile 的基础镜像不阻塞 ARM64。
- Docker 官方当前用法是先配置 QEMU，再配置 Buildx，并由 `build-push-action` 的 `platforms` 生成一个多架构清单。
- 对这个解释型 Python 镜像，现有任务中使用 QEMU 是改动最少的方案；双原生运行器会增加任务和清单合并复杂度。
- 当前 Git 远端是 `BRSBSC/gta-vc-browser-port`，工作流使用 `github.repository_owner`，因此会推送 `ghcr.io/brsbsc/...`；README 和 Compose 却固定拉取 `ghcr.io/developeranku/...`，构建与部署来源不一致。
- `requirements.txt` 的六个运行依赖均未锁定版本，相同提交的重建结果可能漂移；但当前依赖链没有明显 ARM64 硬编码。
- `game-engine/.dockerignore` 已正确排除版本控制信息、notebook、Compose、归档、缓存、存档和解包数据，无需修改。
- `game-engine/additions/saves.py:24-27,36-37` 只清理 `fileName`，却把未清理的 `token` 拼进文件路径；包含父目录片段的 token 可逃逸 `saves/`。
- `game-engine/additions/saves.py:28-30` 会把没有大小限制的上传文件一次性读入内存。
- `game-engine/additions/packed.py:67-84` 直接写最终归档文件，而 `:115-118` 把任何非空文件视为可复用；下载中断会留下之后反复加载的损坏文件。
- `server.py:299-347` 会把 `/vcsky/*` 和 `/vcbr/*` 请求代理到外部 CDN；`cache.py:98` 没有排除 `Authorization`，开启 Basic Auth 后可能把凭据转发给第三方。
- `server.py:308-320,334-346` 把不可信路由 `path` 直接拼到本地目录和缓存目录，缺少统一的安全路径约束。
- 项目没有可见的自动测试、lint/type-check CI 或依赖更新配置；当前唯一工作流会直接构建并推送镜像。
- `game-engine/docker-compose.yml` 没有 `environment` 或 `build`，但后端 README 声称环境变量和 `docker compose up --build` 可用；这些说明与实现不一致。
- Compose 没有持久化卷，删除或重建容器会丢失容器内下载的归档；启用自定义存档时也会丢失存档。
- `game-engine/dist/` 是必要的浏览器运行时载荷；其中最大文件是约 8 MB 的片头视频，不属于明显可删除的镜像膨胀。
- 启动器代码较小，并复用了浏览器原生 API；未发现值得为本次任务重构的逻辑。
- `web-launcher/public/manifest.webmanifest:16-26` 把 `.ico` 声明为 `image/png`，PWA 安装图标可能被浏览器忽略。
- `game-engine/utils/packer_brotli.py` 约 1,687 行且包含同步/异步两套实现，但没有测试时重构风险较高，本次不建议顺手处理。

## 技术决定
| 决定 | 理由 |
|------|------|
| 直接修改现有镜像工作流 | 工作流历史中没有需要保留的复杂架构 |
| 推荐 `linux/amd64,linux/arm64` 单清单 | 兼容现有拉取方式，满足主流 64 位 ARM 设备 |
| Dockerfile 和 Compose 不因 ARM64 而修改 | 基础镜像和 Python 依赖链未发现架构阻塞 |
| 不在 ARM 改动中重构大型打包器 | 缺少测试且与目标无关，风险大于收益 |
| 不增加 `linux/arm/v7` | 目标是甲骨文云 aarch64 实例，32 位 ARM 不在需求内 |
| 优化项暂不实施 | 用户要求先完成 GitHub 自动构建，后续再单独处理项目优化 |

## 遇到的问题
| 问题 | 处理结果 |
|------|----------|
| 一次批量读取没有返回有效错误上下文 | 改为每条命令独立捕获结果 |
| Docker 清单检查被沙箱阻止创建 Buildx 锁 | 经批准后完成只读检查 |
| 初次文件枚举未包含隐藏文件，误判缺少 `.dockerignore` | 用包含隐藏文件的枚举复核并纠正结论 |

## 参考资料
- 当前仓库：`J:\abu_workspace\github\gta-vc-browser-port`
- Docker GitHub Actions：`https://docs.docker.com/build/ci/github-actions/`
- Docker 多架构构建：`https://docs.docker.com/build/building/multi-platform/`
- `docker/build-push-action`：`https://github.com/docker/build-push-action`

## 图像或浏览器调研
- 无。
