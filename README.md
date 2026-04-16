# Charlie Skill

这是一个面向销售线索收集与邮件外联的本地工具包。  
你可以把它理解成 4 个 skill 组合在一起使用。

## 当前包含的 4 个 Skills

### 1. `company-filter-refresh`

作用：从公开网页搜索公司、抓取官网高管、补充联系方式、生成邮箱、查看数据状态。

适合什么时候用：

- 你刚开始建名单
- 你想更新公司和高管数据
- 你需要先把基础数据准备好

当前可直接运行的常用功能：

- 搜索公司
- 抓取高管
- 生成邮箱
- 补充联系方式
- 查看数据状态

### 2. `company-filter`

作用：从本地已有数据中，按条件筛选目标公司和高管名单。

适合什么时候用：

- 你已经有一批公司数据
- 你想从中筛出某个行业、地区或目标岗位的人

说明：

- 这个 skill 的定位是“筛选本地数据”
- 它依赖 `company-filter-refresh` 先把数据准备出来

### 3. `email-templates`

作用：提供常用的销售邮件模板。

适合什么时候用：

- 你已经有联系人名单
- 你准备发开发信、跟进信、会议邀请

说明：

- 它本身不是发送工具
- 它负责提供邮件内容模板

### 4. `gmail-manager`

作用：连接 Gmail 做发信、查询历史邮件、追踪跟进状态。

适合什么时候用：

- 你已经筛好了公司和联系人
- 你想正式发邮件并记录结果

说明：

- 这个 skill 依赖 Gmail MCP 配置
- 如果没有 Gmail MCP，它不能单独直接使用

## 建议使用顺序

如果你是第一次接手这个项目，建议按下面顺序使用：

1. 先用 `company-filter-refresh` 建立或更新数据
2. 再用 `company-filter` 从数据里筛选目标名单
3. 再用 `email-templates` 选合适的邮件模板
4. 最后用 `gmail-manager` 发信和跟进

## 一键运行

项目根目录已经提供了一个 Mac 用的一键启动文件：

- `run.command`

使用方法：

1. 在 Finder 中打开项目目录
2. 双击 `run.command`
3. 按提示输入数字
4. 根据提示继续输入关键词或公司名

它会提供这些菜单：

- 搜索公司
- 抓取高管
- 生成邮箱
- 补充联系方式
- 查看数据状态

如果是第一次在这台设备上运行，`run.command` 会自动：

- 优先使用项目里的 `.venv`
- 如果没有 `.venv`，尝试自动创建
- 自动安装 `requests` 和 `beautifulsoup4`

## 最常用的操作

如果你不想双击，也可以在终端里直接运行。

### 搜索公司

```bash
python3 skills/company-filter-refresh/refresh.py search --query "Trimble reseller dealer USA" --limit 20
```

### 抓取高管

```bash
python3 skills/company-filter-refresh/refresh.py discover --company "AllTerra Central"
```

### 生成邮箱

```bash
python3 skills/company-filter-refresh/refresh.py email --company "AllTerra Central"
```

### 补充联系方式

```bash
python3 skills/company-filter-refresh/refresh.py enrich --company "AllTerra Central"
```

### 查看状态

```bash
python3 skills/company-filter-refresh/refresh.py status
```

## 结果文件在哪里

主要结果保存在这里：

- `skills/company-filter/data/companies.csv`
- `skills/company-filter/data/executives.csv`

可以直接用 Excel、Numbers 或任意表格软件打开。

## 交付方式

把项目交付到另一台设备时，建议只考虑下面两种方式。

### 方式 A：Mac 项目目录交付

适用场景：

- 目标设备是 macOS
- 对方可以接受双击 `run.command`
- 允许设备上存在 `python3`

交付内容：

- 整个项目目录
- `.venv`
- `run.command`
- `README.md`

使用方式：

1. 把整个项目文件夹复制到另一台 Mac
2. 双击 `run.command`
3. 按菜单提示操作

优点：

- 交付最快
- 不需要额外做打包
- 适合同一团队内部临时使用

限制：

- 仍然依赖系统能运行 `python3`
- 如果目标设备环境不同，`.venv` 不一定完全可复用
- 对非技术用户仍然不够稳妥

### 方式 B：打包成独立可执行版本

这是推荐的交付方式。

适用场景：

- 交付给不懂技术的人
- 希望对方不安装 Python
- 希望对方双击就能运行

交付原则：

- 不直接交付源码作为主要入口
- 交付单独打包后的可执行程序
- 按操作系统分别交付

#### macOS 交付版本

推荐产物：

- `.app` 应用，或者
- 独立可执行文件

推荐交付内容：

- `Charlie Skill.app` 或等价可执行程序
- 数据目录
- 这份 `README.md`

用户操作方式：

1. 双击应用
2. 按界面或菜单提示操作

#### Windows 交付版本

推荐产物：

- `.exe` 可执行文件

推荐交付内容：

- `Charlie Skill.exe` 或等价程序
- 数据目录
- 说明文档

用户操作方式：

1. 双击 `.exe`
2. 按界面或菜单提示操作

优点：

- 对方不需要安装 Python
- 对非技术用户最友好
- 可控性更高，交付更标准

限制：

- 需要你提前完成打包
- macOS 和 Windows 必须分别产出对应版本
- 每次功能更新后通常都要重新打包

## 推荐交付方式

推荐使用：`方式 B：打包成独立可执行版本`

推荐原因：

- 这是最适合非技术用户的方案
- 不要求对方安装 Python
- 不要求对方理解项目目录结构
- 交付后更接近真正的软件使用方式

建议最终同时准备两套可执行文件：

- macOS 版本
- Windows 版本

如果只是内部临时测试，才建议使用 `方式 A：Mac 项目目录交付`。

## 常见问题

### 双击 `run.command` 没反应

先确认是在 Mac 上使用。  
如果系统提示安全限制，请右键 `run.command` 后选择“打开”。

### 提示安装依赖失败

通常是网络问题，稍后再试。  
如果长期失败，说明这台设备可能没有可用的 `python3`。

### 搜不到公司

可以换关键词，或者在关键词里增加地区，如 `USA`、`Texas`、`California`。

### 没抓到高管

通常是因为目标公司官网没有公开的 `about`、`team`、`leadership` 页面，或者网页结构变化导致识别失败。

### `gmail-manager` 不能直接用

这是正常情况。  
`gmail-manager` 需要额外配置 Gmail MCP，不是拿到项目后立刻就能发信。
