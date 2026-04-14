# ReAct 简易游戏生成 Agent（DeepSeek）

这是一个基于 ReAct 范式（Think → Act → Observe → Reflect）的控制台小游戏生成 Agent：
- **Think**：根据你的需求规划游戏类型、规则和结构
- **Act**：调用 DeepSeek（OpenAI 兼容 SDK，`model=deepseek-chat`）生成游戏代码
- **Observe**：执行生成代码，捕获 stdout / stderr / 异常
- **Reflect**：根据错误自动修复，最多 3 轮

## 环境要求

- Windows / macOS / Linux 均可
- Python 3.9+（推荐）

## 安装依赖

在本项目根目录执行：

```bash
pip install -r requirements.txt
```

## 配置 DeepSeek Key

二选一：

- **方式 1：环境变量（推荐）**

PowerShell：

```powershell
setx DEEPSEEK_API_KEY "你的key"
```

- **方式 2：运行时输入**
程序启动后会提示你输入 `DEEPSEEK_API_KEY`。

可选环境变量：
- `DEEPSEEK_BASE_URL`：默认 `https://api.deepseek.com`

## 运行

两种方式任选其一：

```bash
python -m react_game_agent
```

或：

```bash
python react_game_agent/main.py
```

运行后输入你想要的小游戏需求，程序会输出最终可运行的 **`game.py` 单文件代码**，复制保存即可运行。

