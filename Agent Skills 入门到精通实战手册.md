# **🚀 Agent Skills：从入门到精通实战手册 (Claude Code & Cursor)**

过去，我们用 AI 就像是在用一个“打字机”或“百科全书”，你得一遍遍告诉它需求。

现在，有了 **Agent Skills**，AI 变成了你们广告公司的\*\*“全能实习生”\*\*。你不需要每次都重复交代规矩，而是可以给它塞一个“技能包（SOP）”。只有当老板（你）下发特定任务时（比如“给包子铺做个设计”），AI 才会去翻看对应的技能包，按部就班地干活，不仅省时，还绝对不会搞错品牌调性。

## **📁 第一部分：标准文件结构设计**

为了让主流的 AI 助手（Claude Code, Cursor 等）都能看懂，我们需要把项目的技能包存放在特定的文件夹里。通常是在你的项目根目录建一个 .agents/skills/ 文件夹。

假设我们现在接了一个大单：**为“王大妈包子铺”设计全套视觉（招牌、海报、传单）**。我们给 AI 定制的技能包目录结构如下：

.agents/  
└── skills/  
    └── baozi-campaign/             \# 技能的唯一标识名 (项目代号：包子铺全案)  
        ├── SKILL.md                \# 【核心大脑】项目SOP：包含触发条件和执行步骤  
        ├── scripts/                \# 【动作工具】给 AI 用的工具箱  
        │   ├── resize\_board.py     \# 自动调整招牌尺寸的脚本  
        │   └── color\_palette.sh    \# 提取品牌主色调的脚本  
        ├── references/             \# 【知识库】按需翻阅的长篇资料  
        │   └── brand\_guidelines.md \# 王大妈包子铺的品牌禁忌（如：不准用冷色调）  
        └── assets/                 \# 【资源素材】模板文件  
            ├── config.yaml         \# 预设的全局参数配置  
            └── poster-template.svg \# 预设好的海报排版模板

### **📂 核心目录与支持的文件类型详解**

1. **大脑发号施令 (SKILL.md)**  
   * **类型**：Markdown 文件。  
   * **作用**：这是总指挥部，顶部用 YAML 写明触发条件，正文告诉 AI“第一步想文案，第二步做海报”。  
2. **工具外包 (scripts/)**  
   * **常见格式**：.py (Python), .sh (Bash), .js (Node.js) 等可执行脚本。  
   * **作用**：AI 本身不会使用 Photoshop 或 Illustrator？没关系，写个小脚本让它调用，它只需在终端传入参数（如尺寸 800x600），脏活累活脚本干。  
3. **资料按需查阅 (references/)**  
   * **常见格式**：.md (Markdown文档), .txt (纯文本), .csv (数据表格) 等。  
   * **作用**：不要把王大妈长达 10 页的品牌历史和碎碎念都塞进平时对话里。把品牌禁忌、过往竞品数据放在这里，AI 只有在做这个项目时才会去“翻书”，极大节省日常沟通成本。  
4. **物料与配置仓库 (assets/)**  
   * **常见格式**：  
     * **配置类**：.json, .yaml（例如存储王大妈品牌的标准色号代码、字体与字号的映射表）。  
     * **模板类**：.svg（海报矢量排版骨架）, .html（网页落地页结构）。  
     * **参考图**：.png, .jpg（供视觉脚本提取色彩，或作为设计构图参考的底图）。  
   * **作用**：这里存放 AI 执行任务时需要读取的静态模板或参考数据，是不可或缺的“后勤仓库”。

## **🤖 第二部分：在 Claude Code 中创建与使用 Skills**

Claude Code 原生支持这种基于 SKILL.md 的生态。

### **1\. 编写核心大脑 SKILL.md**

这个文件最顶部的区域（两根虚线之间的部分）极其关键，相当于实习生的“任务雷达”，探测到特定词汇就会激活技能。

\---  
name: baozi-campaign  
description: "处理包子铺的广告物料设计。当用户要求写包子铺文案、设计招牌或生成海报时触发此技能。"  
disable-model-invocation: true  
\---

\# 包子铺广告全案执行 SOP

\#\# 工作流 (Workflow)  
当老板让你为包子铺制作物料时，严格按以下步骤执行：

1\. \*\*查阅品牌调性 (Brand Check)\*\*  
   \- 在写任何文案或设计之前，必须先静默读取 \`references/brand\_guidelines.md\`。  
   \- 记住：绝对不能出现“低端”、“便宜”等字眼，要主打“匠心”、“老面”。

2\. \*\*读取全局配置 (Config Check)\*\*  
   \- 读取 \`assets/config.yaml\`，确认本次主推的包子口味及对应的主题色。

3\. \*\*招牌设计 (Signboard Task)\*\*  
   \- 如果用户要求做招牌，请运行 \`bash .agents/skills/baozi-campaign/scripts/color\_palette.sh\` 获取品牌标准色。  
   \- 必须使用 \`assets/poster-template.svg\` 中的大字号标题规范。

4\. \*\*海报与尺寸适配 (Poster Task)\*\*  
   \- 写完文案后，如果需要出图，运行 \`python .agents/skills/baozi-campaign/scripts/resize\_board.py \<宽度\> \<高度\>\` 来生成最终排版。

**高阶属性解析：**

* disable-model-invocation: true：安全锁。意思是 AI **不能**私自做主乱发海报，必须由老板（你）明确输入 /baozi-campaign 或明确要求做包子铺任务时才能干活。

### **2\. 如何使用**

* **自动触发**：当你在聊天框说：“把刚才那段话改成王大妈包子铺的招牌文案”，Claude 会探测到需求，自动翻开这个 SOP 开始干活。  
* **手动触发**：在聊天框直接输入斜杠命令：/baozi-campaign，然后跟上具体指令。

## **⚡ 第三部分：在 Cursor 中创建与使用 Skills / MDC**

Cursor 有一套双轨制的规则系统，我们可以理解为：**日常员工手册 (MDC Rules)** 与 **专项行动小组 (Agent Skills)**。

### **1\. 静态习惯约束：.mdc Rules (日常员工手册)**

这用来约束 AI 的日常工作习惯，比如“只要是在写文案，就必须遵守什么风格”。

**示例：.cursor/rules/copywriting.mdc**

\---  
description: 广告文案创作规范  
globs: copy/\*\*/\*.txt  
alwaysApply: false  
\---

\# 文案撰写铁律  
\- 永远优先使用“动词+名词”的结构（如：咬一口爆汁，品百年手艺）。  
\- 任何食品广告，绝不能使用降低食欲的形容词。

当你在 copy/ 文件夹下新建一个文案文件时，AI 会自动遵守这套铁律。

### **2\. 动态工作流：Agent Skills (专项行动小组)**

如果老板说：“去把王大妈的招牌、海报和传单一次性全搞定”，这就需要一整套流程。此时 Cursor 的 Agent 同样会读取 .agents/skills/baozi-campaign/SKILL.md。

在 Cursor Composer (Agent 模式) 中：

1. Agent 会自动在项目里搜寻 .agents/skills/。  
2. 发现 baozi-campaign 后，它会进入“工作流模式”。  
3. 它可以自动打开终端（Terminal），帮你运行调整尺寸的 Python 脚本，甚至直接读取 .yaml 配置去修改模板文件。

## **🌐 第四部分：如何使用 GitHub 上别人的 Skills**

现在开源社区有很多现成的“优秀员工经验包”（如：爆款小红书文案生成器、电商海报自动排版等）。你可以直接把别人的经验包“挖”过来。

### **方案 A：使用通用命令行工具 (推荐)**

社区标准工具 skills 允许你直接从 GitHub 抓取：

\# 全局安装通用技能包管理器  
npm install \-g skills-cli

\# 从 GitHub 仓库下载一个“文案大师”技能到你的项目  
npx skills add creative-agency/agent-skills \--skill copywriting-master

\# 下载别人打包好的“餐饮全案广告包”  
npx skills add Awesome-Agent/food-ad-skills

### **方案 B：在 Claude Code 内置市场安装**

2026 年的 Claude Code 有了内置插件市场：

\# 1\. 添加广告同行的开源技能库源  
/plugin marketplace add ad-master/claude-skills

\# 2\. 安装指定的“排版校对技能包”  
/plugin install layout-checker@claude-skills

## **🏆 第五部分：高阶最佳实践**

1. **写给 AI 的注释要用“指令语气”**  
   不要用备忘录的语气写“这个脚本是用来切图的”。  
   要像给笨笨的实习生下死命令：“**如果你发现用户要求海报适配朋友圈，你必须运行 resize\_board.py 脚本，并将长宽比设置为 9:16。**”  
2. **单一职责原则（不要把全能王逼疯）**  
   不要搞一个巨大无比的 SKILL.md，把写文案、画图、算项目报价全塞进去。  
   应该拆分成多个独立小组：/write-slogan（专门写广告语）、/design-poster（专门套模板）、/calculate-budget（专门算成本）。  
3. **利用脚本（Bash/Python）桥接一切物理工具**  
   不要指望 AI 会自动帮你打开电脑上的 Photoshop 去拖拽图层。  
   正确的做法是：写一个能处理图像的 Python 脚本放在 scripts/ 目录下。告诉 AI：“你需要改尺寸时，就去执行这个脚本”。这样，AI 就变相拥有了操作物理软件的能力！