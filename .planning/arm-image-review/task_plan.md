# 任务计划：项目审查与 ARM 镜像支持

## 目标
审查项目中有证据支撑的优化点，并在确认目标架构后，以最小改动扩展 GitHub 镜像构建。

## 当前阶段
已完成

## 阶段安排

### 阶段 1：需求与现状调研
- [x] 记录用户需求
- [x] 检查仓库结构、文档、近期提交和现有工作流
- [x] 确认 ARM 目标和验收标准
- [x] 记录有证据支撑的审查发现
- **状态：** 已完成

### 阶段 2：方案确认
- [x] 对比最小实现方案
- [x] 提交推荐方案并取得用户确认
- [x] 编写并自检已确认的设计说明
- **状态：** 已完成

### 阶段 3：实施计划
- [x] 根据已确认的设计编写精确实施计划
- **状态：** 已完成

### 阶段 4：实施
- [x] 按确认方案完成最小工作流或代码改动
- [x] 添加最小且有效的自动检查
- **状态：** 已完成

### 阶段 5：验证与交付
- [x] 运行仓库检查和工作流专项验证
- [x] 复核最终差异并按优先级记录优化项
- **状态：** 已完成

## 关键问题
1. “ARM 架构”是只支持 Linux ARM64，还是同时支持 ARM64 和 ARM/v7？已确认：用于甲骨文云 ARM 实例，只需 `linux/arm64`。
2. 当前 Dockerfile 和依赖链是否已经兼容目标平台？
3. 哪些优化项有可验证的收益或正确性影响，而不是推测性重构？
4. 工作流应发布到当前仓库所有者的 GHCR，还是继续以 `developeranku` 镜像为部署来源？

## 已作决定
| 决定 | 理由 |
|------|------|
| 保持实现最小并复用现有工作流 | 用户只要求增加一个架构，不做无关 CI 重构 |
| 发布一个多架构镜像清单，而不是架构后缀标签 | 保持现有拉取命令不变，由 Docker 自动选择 amd64 或 ARM64 变体 |
| ARM 目标使用 `linux/arm64` | 甲骨文云 ARM（Ampere/aarch64）实例对应 64 位 ARM，不需要 32 位 ARM/v7 |
| 只修改现有 GitHub Actions 工作流 | 用户明确要求先完成自动构建，项目优化留到后续处理 |
| 在当前工作区直接修改，不创建 worktree、不提交 | 仅有一个 YAML 文件的低风险改动，用户已明确要求执行，且没有既有产品文件改动 |

## 已确认的设计

- 现有 `ubuntu-latest` 任务继续负责构建和推送。
- 在 Buildx 之前增加 `docker/setup-qemu-action@v3`。
- 在现有 Build and push 步骤中声明 `linux/amd64,linux/arm64`。
- 继续生成 `latest` 和短 SHA 标签，并保留 GHCR 登录、权限和 GHA 缓存设置。
- 镜像发布到当前仓库所有者对应的 `ghcr.io/brsbsc/gta-vc-browser-port-engine`。
- 本次不修改 Dockerfile、Compose、README 或任何项目优化项。

## 中文实施计划

### 目标
让现有 GitHub Actions 自动发布同时支持 amd64 与甲骨文云 ARM64 的单一镜像清单。

### 架构
复用现有 Buildx 构建任务，通过 QEMU 在 GitHub x64 托管运行器中执行 ARM64 构建步骤。`docker/build-push-action@v6` 一次推送两个平台及统一 manifest，不增加矩阵任务或架构后缀标签。

### 技术栈
GitHub Actions、Docker Buildx、QEMU、GHCR。

### 全局约束
- 只修改 `.github/workflows/build-engine.yml`。
- 平台必须精确为 `linux/amd64,linux/arm64`。
- QEMU 设置步骤必须位于 Buildx 设置步骤之前。
- 保留现有触发条件、权限、标签、登录方式和缓存配置。
- 不修改 Dockerfile、Compose、README 和项目源码。

### 任务 1：增加 ARM64 多架构构建

**文件：**
- 修改：`.github/workflows/build-engine.yml`

**输入：** 现有单平台 Buildx 构建工作流。

**输出：** 自动推送包含 `linux/amd64` 与 `linux/arm64` 的 GHCR 镜像清单。

- [x] 步骤 1：运行结构检查，确认当前工作流因缺少 QEMU 和平台声明而失败。
- [x] 步骤 2：在 Buildx 前增加以下配置：

```yaml
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3
```

- [x] 步骤 3：在 Build and push 的 `with` 中增加：

```yaml
          platforms: linux/amd64,linux/arm64
```

- [x] 步骤 4：重新运行结构检查，确认 QEMU 顺序和平台值正确。
- [x] 步骤 5：运行双架构 Buildx 构建且不推送：

```powershell
docker buildx build --platform linux/amd64,linux/arm64 --progress=plain --output=type=cacheonly -f game-engine/docker/Dockerfile game-engine
```

预期结果：命令退出码为 0，两个平台均完成依赖安装和镜像构建。

- [x] 步骤 6：检查最终 Git 差异，确认只有工作流产品文件发生改动，`.planning/` 仅为本次中文记录。

## 最终结果

- 产品改动仅为 `.github/workflows/build-engine.yml` 的 4 行新增。
- amd64 与 ARM64 的实际 Buildx 构建均成功。
- 独立审查结论：符合规格、代码质量批准，Critical/Important/Minor 问题均为零。
- 本次改动已按用户要求提交到本地 `main`；尚未推送，推送到 `BRSBSC/gta-vc-browser-port` 后才会触发 GHCR 自动发布。

## 遇到的错误
| 错误 | 尝试 | 处理结果 |
|------|------|----------|
| 并行读取技能和上下文时仅返回通用退出码 1 | 1 | 改为逐命令捕获错误，随后完整读取所需技能文件 |
| 本地记忆索引搜索返回退出码 1 | 1 | 确认没有本项目专属记忆，改用当前仓库实时证据 |
| 只读检查批次因 `rg` 无匹配而整体退出 | 1 | 对允许无匹配的搜索改用逐命令结算 |
| Docker Buildx 无权创建用户目录锁文件 | 1 | 经批准后以沙箱外只读方式重新检查镜像清单 |
| 双架构构建无法连接 `dockerDesktopLinuxEngine` | 1 | 确认 Docker Desktop 完全停止；经用户授权后台启动，等待引擎就绪后原命令构建成功 |

## 备注
- 重大架构或实现决定前重新阅读本计划。
- 用户确认设计前不修改产品代码。
