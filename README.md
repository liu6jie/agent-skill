# 🚀 Agent Skills：从入门到精通实战手册 (Claude Code & Cursor)

过去，我们用 AI 就像是在用一个“打字机”或“百科全书”，你得一遍遍告诉它需求。

现在，有了 Agent Skills，AI 变成了你们广告公司的**“全能实习生”**。
你不需要每次都重复交代规矩，而是可以给它塞一个“技能包（SOP）”。
只有当老板（你）下发特定任务时（比如“给包子铺做个设计”），AI 才会去翻看对应的技能包，按部就班地干活，不仅省时，还绝对不会搞错品牌调性。

---

## 📁 第一部分：标准文件结构设计

为了让主流的 AI 助手（Claude Code, Cursor 等）都能看懂，我们需要把项目的技能包存放在特定的文件夹里。
通常是在你的项目根目录建一个 `.agents/skills/` 文件夹。

### 示例：王大妈包子铺全案设计
.agents/
└── skills/
└── baozi-campaign/ # 技能唯一标识名（项目代号）
├── SKILL.md # 【核心大脑】项目 SOP：触发条件 + 执行步骤
├── scripts/ # 【动作工具】AI 可调用脚本
│ ├── resize_board.py
│ └── color_palette.sh
├── references/ # 【知识库】品牌资料、规范
│ └── brand_guidelines.md
└── assets/ # 【资源素材】模板、配置、参考图
├── config.yaml
└── poster-template.svg
plaintext

---

## 📂 核心目录与文件类型详解

### 1. 大脑发号施令：SKILL.md
- 类型：Markdown
- 作用：总指挥部，定义触发条件、执行步骤、工作流

### 2. 工具外包：scripts/
- 格式：`.py`、`.sh`、`.js` 等可执行脚本
- 作用：让 AI 调用脚本完成实际操作（改尺寸、调色、运行命令）

### 3. 资料按需查阅：references/
- 格式：`.md`、`.txt`、`.csv`
- 作用：品牌规范、历史资料、禁忌要求，AI 只在任务时读取

### 4. 物料与配置仓库：assets/
- 配置：`.json`、`.yaml`
- 模板：`.svg`、`.html`
- 图片：`.png`、`.jpg`
- 作用：AI 执行任务所需的静态资源与参数

---

## 🤖 第二部分：在 Claude Code 中创建与使用 Skills

### 1. 编写核心大脑：SKILL.md
顶部 YAML 是“任务雷达”，AI 靠它识别是否触发技能。

```yaml
---
name: baozi-campaign
description: "处理包子铺的广告物料设计。当用户要求写文案、设计招牌、生成海报时自动触发。"
disable-model-invocation: true
---
2. 工作流（Workflow）示例
查阅品牌调性
静默读取 references/brand_guidelines.md
读取全局配置
加载 assets/config.yaml 获取品牌色、主推产品
执行招牌 / 海报设计
运行脚本 scripts/color_palette.sh
尺寸适配与输出
运行 scripts/resize_board.py <宽度> <高度>
3. 使用方式
自动触发：说 “帮我写包子铺文案” 自动激活
手动触发：输入 /baozi-campaign + 指令
⚡ 第三部分：在 Cursor 中创建与使用 Skills / MDC
Cursor 采用双轨制规则系统：
1. 静态习惯约束：.mdc Rules（日常员工手册）
示例：.cursor/rules/copywriting.mdc
yaml
---
description: 广告文案创作规范
globs: copy/**/*.txt
alwaysApply: false
---
规则：
永远使用「动词 + 名词」结构
食品文案禁用降低食欲的形容词
2. 动态工作流：Agent Skills（专项任务小组）
自动扫描项目中的 .agents/skills/
自动进入工作流模式
可自动打开终端、运行脚本、读取配置、修改模板
🌐 第四部分：如何使用 GitHub 上别人的 Skills
方案 A：使用 skills-cli（推荐）
bash
运行
npm install -g skills-cli

# 下载文案大师技能
npx skills add creative-agency/agent-skills --skill copywriting-master

# 下载餐饮全案广告包
npx skills add Awesome-Agent/food-ad-skills
方案 B：Claude Code 内置市场
bash
运行
/plugin marketplace add ad-master/claude-skills
/plugin install layout-checker@claude-skills
🏆 第五部分：高阶最佳实践
1. 写给 AI 的注释要用「指令语气」
不要写：“这个脚本用来切图”
要写：“如果用户需要朋友圈海报，必须运行 resize_board.py，并设置 9:16 比例”
2. 单一职责原则
不要做全能技能包，应拆分为：
/write-slogan 写广告语
/design-poster 设计海报
/calculate-budget 计算预算
3. 用脚本桥接一切工具
不要指望 AI 手动操作 Photoshop
正确方式：
写 Python 脚本 → 让 AI 调用 → AI 变相拥有操作软件的能力
