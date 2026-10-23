# ProjectSeal CLI

<!-- 项目 Logo 占位：尚未选定正式图标。 -->

**为软件发行文件签名，并验证明确指定的发布者身份。**

[English](README.md) · [入门指南](docs/getting-started.md) ·
[命令参考](docs/cli-reference.md) · [安全模型](docs/security-model.md)

ProjectSeal 是本地优先的 Python 命令行工具，提供项目 UUID、SHA-256 指纹、
Sigstore Cosign 签名及带信任约束的验证。无需 ProjectSeal 账号、数据库或云服务。
**0.1.0 当前作为首版候选交付**，正式发布前请检查[实际验证状态](docs/validation.md)。

## 主要功能

- 初始化带 schema_version 的项目身份文件，显示名称明确属于用户声明。
- 以 1 MiB 分块读取任意普通二进制文件，支持大文件。
- 默认使用 Cosign 无密钥签名，输出现代 Sigstore Bundle。
- 验证必须指定精确签名者身份和 OIDC issuer、明确可信的策略文件，或受信任公钥。
- 可选生成规范化 Manifest，并对 Manifest **单独签名**。
- 展示 Git 分支、Commit 和未提交修改；非 Git 项目也可正常使用。
- 支持 JSON、CI 非交互模式、覆盖保护和明确的失败退出码，无遥测。

## 安全能力边界

签名验证文件内容和预期签名者/公钥的关系。普通哈希不能证明作者身份。
项目名称、开发者名称、UUID 和 Git 信息不会自动成为权属证明；即使 Manifest
已签名，也只证明受信任签名者作出了该声明。

工具不能防复制、防逆向、自动认定著作权、判断原创性，或保证签名软件没有
漏洞/恶意行为。Git 提交时间不是法律意义上的可信时间戳。

**本地优先不等于无密钥签名离线运行。** Cosign 使用 OIDC、Fulcio、Rekor
及可信根服务。公开透明日志可能披露签名者身份、文件摘要和签名元数据。
ProjectSeal 不上传源码、不收集遥测。详见[安全模型](docs/security-model.md)。

## 安装

需要 Python **3.11+**。在项目目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
projectseal --help
projectseal --version
```

macOS/Linux 激活命令为 `. .venv/bin/activate`。也可安装本地构建产物：
`python -m pip install dist/projectseal-0.1.0-py3-none-any.whl`。
当前不假设已经在 PyPI 发布。

### 安装 Cosign

当前仅接受 **Cosign 3.1.4**，运行前检测版本及必要参数。从
[官方发行页](https://github.com/sigstore/cosign/releases/tag/v3.1.4)
选择 Windows amd64、macOS amd64/arm64 或 Linux amd64/arm64 对应文件，按
[官方安装指南](https://docs.sigstore.dev/cosign/system_config/installation/)
验证下载来源后，以 `cosign`（Windows 为 `cosign.exe`）放入 PATH。
不会静默使用未测试的新版本。测试范围见[签名指南](docs/signing-guide.md)。

## 快速开始

```powershell
projectseal init
projectseal status
projectseal identity --json
projectseal hash dist/app.zip --json
projectseal sign dist/app.zip
projectseal verify dist/app.zip --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com
```

签名会启动 Cosign 身份认证流程。分发原文件及 `dist/app.zip.sigstore.json`。
通过独立可信渠道取得发布者的精确身份及签发者，替换示例身份/issuer 后再验证。
缺少信任约束返回 `UNTRUSTED`；缺少 Bundle 返回 `MISSING_BUNDLE`，均非零退出。

同时认证项目名称、版本等声明：

```powershell
projectseal sign dist/app.zip --release-version 0.1.0
projectseal verify dist/app.zip --manifest dist/app.zip.manifest.json --certificate-identity dev@example.com --certificate-oidc-issuer https://accounts.google.com
```

会生成原文件的 Bundle、规范化 Manifest，以及 Manifest 自己的 Bundle。
只验证原文件时，不会顺便认证旁边的 Manifest。

## 常见问题

**开发者名称经过认证吗？** 没有，它只是自填显示字段。

**为何错误身份、签发者或篡改有时统一显示 `VERIFICATION_FAILED`？**
Cosign 没有稳定的结构化错误分类，不能根据文字猜测。只有认证后的 Manifest
摘要比较，或检测到文件在操作期间变化时，才能可靠返回 `FILE_MODIFIED`。

**支持 CI 和自有密钥吗？** 支持。`init --non-interactive` 使用默认值；
`sign --non-interactive` 同意透明日志条款，并依赖可用的环境 OIDC 凭证或密钥。
签名的 `--json` 隐含非交互模式。私钥应存放仓库外，密码通过 Cosign 自己的
机制提供。详见[签名指南](docs/signing-guide.md)。

**验证必须初始化项目吗？** 不需要，只有生成 Manifest 需要初始化。
信任策略必须显式使用 `--policy` 传入，不会从项目文件自动信任作者。

## 开发、测试与构建

```powershell
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src
pytest --cov=projectseal --cov-report=term-missing
python -m build
python -m twine check dist/*.whl dist/*.tar.gz
```

普通测试使用 Stub/Mock，不能代替真实认证。可选真实测试要求与当前结果见
[验证记录](docs/validation.md)。Python 3.11、3.12、3.13 × Ubuntu、Windows、
macOS 的九组 GitHub CI 已通过，真实 GitHub Actions OIDC 无密钥签名验收也已通过；
具体提交、运行记录和发版前待办均已记录。

## 路线图、贡献与许可证

v0.2.0 计划提供 Codex Skill、可复用发行集成和更多经过测试的 Cosign 版本；
v0.3.0 计划加入开发证据及可选许可证 SDK。后续可通过适配器扩展 Cloud、License、
Shield；当前不包含服务器、账号、数据库、Redis、支付或商业授权实现。

参阅[贡献指南](CONTRIBUTING.md)、[行为准则](CODE_OF_CONDUCT.md)、
[安全政策](SECURITY.md)。采用 [MIT](LICENSE)。未声称通过第三方安全审计，
不提供绝对安全、绝对防破解或版权确权承诺。
