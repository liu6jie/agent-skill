# -*- coding: utf-8 -*-
"""
基于 ReAct(Think→Act→Observe→Reflect) 的简易「控制台小游戏生成 Agent」

要求特性：
- Think：根据用户需求规划游戏类型/规则/结构
- Act：调用 DeepSeek（OpenAI 兼容 SDK，model=deepseek-chat）生成 Python 控制台小游戏代码
- Observe：执行生成代码，捕获 stdout/stderr/报错
- Reflect：根据错误信息自动修复，最多 3 轮

运行前准备（二选一）：
1) 设置环境变量：DEEPSEEK_API_KEY=你的key
2) 或运行时按提示输入 Key
可选：
  - DEEPSEEK_BASE_URL（默认 https://api.deepseek.com）
"""

import json
import os
import re
import shutil
import sys
import tempfile
import textwrap
import subprocess
from dataclasses import dataclass
from typing import Dict, Tuple


# ----------------------------
# Windows 控制台中文显示优化
# ----------------------------
def _setup_console_utf8() -> None:
    """
    尽量让 Windows 终端正确显示中文。
    说明：不同终端/字体/代码页差异较大，这里做“尽力而为”的兼容处理。
    """
    if os.name != "nt":
        return
    try:
        # Python 3.7+：尽量把标准输出/错误切到 UTF-8
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ----------------------------
# DeepSeek Key 进程内缓存
# ----------------------------
_CACHED_DEEPSEEK_API_KEY: str = ""


# ----------------------------
# 基础工具：路径/模式判断
# ----------------------------
def _project_root() -> str:
    """
    项目根目录（README.md/requirements.txt 所在目录）。
    """
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, ".."))


def _is_web_game_need(user_need: str) -> bool:
    s = (user_need or "").lower()
    keywords = ["html", "css", "javascript", "js", "网页", "浏览器", "canvas", ".js", ".css", ".html"]
    return any(k in s for k in keywords)


# ----------------------------
# 1) LLM 调用封装（DeepSeek）
# ----------------------------
def llm(
    messages,
    model: str = "deepseek-chat",
    temperature: float = 0.2,
    max_tokens: int = 2500,
    response_format: Dict = None,
) -> str:
    """
    统一封装 LLM 调用（OpenAI 兼容 SDK -> DeepSeek）
    依赖：pip install openai
    """
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError(
            "未检测到 openai SDK。请先安装：pip install openai\n"
            f"原始错误：{e}"
        )

    global _CACHED_DEEPSEEK_API_KEY

    # 优先使用进程内缓存，其次环境变量
    api_key = (_CACHED_DEEPSEEK_API_KEY or os.getenv("DEEPSEEK_API_KEY", "")).strip()
    if not api_key:
        api_key = input("请输入 DEEPSEEK_API_KEY：").strip()
        if not api_key:
            raise RuntimeError("未提供 DEEPSEEK_API_KEY，无法调用 DeepSeek。")
        # 写入缓存 + 写入当前进程环境变量，避免后续多次提示
        _CACHED_DEEPSEEK_API_KEY = api_key
        os.environ["DEEPSEEK_API_KEY"] = api_key
    else:
        # 同步回缓存（如果来自环境变量）
        _CACHED_DEEPSEEK_API_KEY = api_key

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
    client = OpenAI(api_key=api_key, base_url=base_url)

    # DeepSeek 侧 max_tokens 通常有上限（你当前报错显示是 8192）
    try:
        max_tokens = int(max_tokens)
    except Exception:
        max_tokens = 2500
    max_tokens = max(1, min(max_tokens, 8192))

    kwargs = {}
    if response_format is not None:
        # OpenAI 兼容的 JSON 输出模式（DeepSeek 通常也支持）
        kwargs["response_format"] = response_format

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
    return resp.choices[0].message.content or ""


# ---------------------------------
# 2) 安全执行代码并捕获输出/错误
# ---------------------------------
@dataclass
class RunResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool


def run_code(code: str, timeout_sec: int = 6, input_data: str = "") -> RunResult:
    """
    将代码写入临时文件，用子进程运行，捕获 stdout/stderr。
    - timeout_sec: 超时秒数，防止死循环/长期阻塞
    - input_data: 标准输入（用于简单 smoke test）
    """
    temp_dir = tempfile.mkdtemp(prefix="react_game_agent_")
    py_path = os.path.join(temp_dir, "game.py")

    with open(py_path, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        proc = subprocess.run(
            [sys.executable, py_path],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=temp_dir,
        )
        return RunResult(
            ok=(proc.returncode == 0),
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            timed_out=False,
        )
    except subprocess.TimeoutExpired as e:
        return RunResult(
            ok=False,
            returncode=124,
            stdout=(e.stdout or ""),
            stderr=(e.stderr or "") + "\n[Timeout] 运行超时，疑似等待输入过久或死循环。",
            timed_out=True,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------
# 2.1) Web 多文件项目自检与落盘
# ---------------------------------
@dataclass
class WebRunResult:
    ok: bool
    stdout: str
    stderr: str
    used_node_check: bool


def _try_node_check(js_path: str, cwd: str) -> Tuple[bool, str]:
    """
    如果系统安装了 Node.js，则用 `node --check` 做一次 JS 语法检查。
    未安装 Node.js 时返回 (False, '')，并不视为失败。
    """
    try:
        where_cmd = "where node" if os.name == "nt" else "which node"
        p = subprocess.run(where_cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=2)
        if p.returncode != 0:
            return False, ""
    except Exception:
        return False, ""

    try:
        p2 = subprocess.run(
            ["node", "--check", js_path],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        if p2.returncode == 0:
            return True, ""
        return True, (p2.stderr or p2.stdout or "").strip()
    except Exception as e:
        return True, f"Node 语法检查执行失败：{e}"


def run_web_project(files: Dict[str, str]) -> WebRunResult:
    """
    把 index.html/style.css/main.js 写入临时目录并做基本自检：
    - HTML 是否引用了 style.css 与 main.js
    - 三个文件是否非空
    - 可选：如果装了 Node.js，对 main.js 做语法检查
    """
    temp_dir = tempfile.mkdtemp(prefix="react_web_game_")
    try:
        for name, content in files.items():
            path = os.path.join(temp_dir, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content or "")

        required = ["index.html", "style.css", "main.js"]
        for r in required:
            p = os.path.join(temp_dir, r)
            if not os.path.exists(p):
                return WebRunResult(False, "", f"缺少文件：{r}", False)
            if os.path.getsize(p) == 0:
                return WebRunResult(False, "", f"文件为空：{r}", False)

        html = files.get("index.html", "")
        if ("style.css" not in html) or ("main.js" not in html):
            return WebRunResult(False, "", "index.html 未正确引用 style.css 或 main.js", False)

        used_node, node_err = _try_node_check(os.path.join(temp_dir, "main.js"), cwd=temp_dir)
        if used_node and node_err:
            return WebRunResult(False, "", f"main.js 语法检查失败：\n{node_err}", True)

        return WebRunResult(True, "Web 项目基础自检通过。", "", used_node)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def write_web_project(target_dir: str, files: Dict[str, str]) -> None:
    """
    将 Web 项目写入 target_dir（覆盖同名文件）。
    """
    os.makedirs(target_dir, exist_ok=True)
    for name, content in files.items():
        out_path = os.path.join(target_dir, name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content or "")


# ----------------------------
# 3) ReAct 循环主体
# ----------------------------
SYSTEM_PROMPT_PY = """你是一个资深 Python 教学与游戏开发助手。
你要根据用户需求生成【单文件、可直接运行】的 Python 控制台小游戏代码。

强约束：
- 只能输出【代码】（不要解释、不要 Markdown、不要三引号围栏）。
- 代码必须是单文件、可直接运行：python game.py
- 不要依赖第三方库（仅用 Python 标准库）。
- 必须包含清晰的中文注释。
- 必须有 main 入口：if __name__ == "__main__": main()
- 交互友好：提示明确、输入校验、可重复游玩、可退出。
- 代码要健壮：避免 NameError/IndexError/ValueError 等常见错误。
- 尽量在启动时展示规则说明。
"""

SYSTEM_PROMPT_WEB = """你是一个资深前端小游戏开发助手。
你要根据用户需求生成一个【纯前端、可直接打开运行】的 Web 小游戏项目（例如贪吃蛇）。

强约束：
- 只能输出【JSON】（不要解释、不要 Markdown、不要三引号围栏）。
- JSON 顶层必须是对象，且必须包含 3 个键：index.html、style.css、main.js。
- 每个键的值都是对应文件的完整文本内容（字符串）。
- 不允许第三方库/框架/外链 CDN。
- 游戏必须可键盘操作（方向键/WASD），有开始/暂停/重开，显示分数，撞墙/撞自己判定结束。
额外要求（为了避免输出被截断）：
- 请尽量精简 HTML/CSS/JS：样式与逻辑够用即可，不要冗长的 UI 文案/大量无关结构。
"""


def _extract_code(raw: str) -> str:
    """
    兼容模型偶发输出 Markdown 代码块的情况。
    """
    s = (raw or "").strip()

    m = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
    if m:
        s = m.group(1).strip()

    anchors = ["import ", "from ", "def ", "class ", "if __name__"]
    idxs = [s.find(a) for a in anchors if s.find(a) != -1]
    if idxs:
        s = s[min(idxs):].lstrip()

    return s + "\n"


def _extract_web_files(raw: str) -> Dict[str, str]:
    """
    从模型输出中提取 JSON 并得到三文件内容。
    允许模型偶发输出多余文本：尝试截取第一个 { 到最后一个 }。
    """
    s = (raw or "").strip()
    if not s:
        raise ValueError("模型输出为空，无法解析 Web 项目文件。")

    l = s.find("{")
    r = s.rfind("}")
    if l != -1 and r != -1 and r > l:
        s2 = s[l : r + 1]
    else:
        s2 = s

    # 注意：LLM 经常把“文件内容”直接塞进 JSON 字符串导致非法（字符串中出现未转义换行）。
    # 这里不做“猜测性修补”（容易引入更隐蔽的错误），而是把异常上抛，
    # 由上层触发“要求模型重新输出严格合法 JSON（用 \\n 转义换行）”的重试逻辑。
    data = json.loads(s2)
    if not isinstance(data, dict):
        raise ValueError("模型输出 JSON 顶层不是对象。")

    for k in ["index.html", "style.css", "main.js"]:
        if k not in data or not isinstance(data[k], str):
            raise ValueError(f"模型输出 JSON 缺少或非法字段：{k}")

    return {"index.html": data["index.html"], "style.css": data["style.css"], "main.js": data["main.js"]}


def _llm_web_files_with_retry(messages, max_attempts: int = 3) -> Dict[str, str]:
    """
    调用 LLM 生成 Web 三文件；若输出不是合法 JSON，则自动要求模型重输并重试。
    """
    last_err = None
    last_raw = ""
    for attempt in range(1, max_attempts + 1):
        raw = llm(
            messages,
            temperature=0.2,
            # Web 三文件容易很长：提高上限减少截断概率
            max_tokens=8192,
            # 尽量启用 JSON 模式，强约束输出为 JSON 对象
            response_format={"type": "json_object"},
        )
        last_raw = raw
        try:
            return _extract_web_files(raw)
        except Exception as e:
            last_err = e
            # 把模型原始输出与错误原因反馈回去，让它“只重排格式”为严格 JSON
            messages = list(messages) + [
                {"role": "assistant", "content": (raw or "")[:12000]},
                {
                    "role": "user",
                    "content": (
                        "你上一次输出无法被严格 JSON 解析，错误如下：\n"
                        f"{repr(e)}\n\n"
                        "请你重新输出【严格合法 JSON】（只能输出 JSON，不要任何解释）。\n"
                        "关键要求：\n"
                        "1) 顶层是对象，且只包含 3 个键：index.html、style.css、main.js\n"
                        "2) 每个值必须是 JSON 字符串：字符串内部的换行必须写成 \\n（不能出现原始换行）\n"
                        "3) 字符串内部的双引号必须转义为 \\\"\n"
                        "4) 请尽量精简内容，避免输出过长被截断\n"
                    ),
                },
            ]
    raise ValueError(f"连续 {max_attempts} 次未获得可解析的 Web JSON：{last_err!r}\n原始输出截断：\n{(last_raw or '')[:2000]}")


def _think_plan(user_need: str) -> str:
    """
    Think：根据用户需求规划游戏结构。
    """
    plan = f"""
【用户需求】
{user_need}

【游戏规划（Think）】
- 游戏类型：选择适合控制台交互、规则清晰、可快速验证的小游戏（猜数字/井字棋/石头剪刀布/文字冒险等）。
- 交互流程：启动展示规则 -> 回合循环 -> 输入校验 -> 判定输赢/状态更新 -> 询问再来/退出。
- 代码结构：
  - main()：展示说明、启动主循环
  - 可拆分：渲染/校验/判定/回合切换 等函数，保持可读性
- 健壮性：
  - 允许 quit/exit 随时退出
  - 输入非法时给出友好提示并继续
"""
    return textwrap.dedent(plan).strip()


def _act_generate_code(user_need: str, plan_text: str) -> str:
    """
    Act：调用 DeepSeek 生成初版游戏代码。
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PY},
        {"role": "user", "content": f"{plan_text}\n\n请根据以上规划与用户需求，生成完整可运行代码。务必只输出代码。"},
    ]
    raw = llm(messages)
    return _extract_code(raw)


def _act_generate_web_files(user_need: str) -> Dict[str, str]:
    """
    Act：生成 Web 多文件项目（严格 JSON 输出）。
    """
    prompt = f"""
【用户需求】
{user_need}

请生成一个贪吃蛇 Web 项目，文件必须分成 index.html / style.css / main.js。
再次强调：只能输出 JSON，且必须包含这 3 个键。
"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_WEB},
        {"role": "user", "content": textwrap.dedent(prompt).strip()},
    ]
    return _llm_web_files_with_retry(messages, max_attempts=3)


def _reflect_fix_code(user_need: str, plan_text: str, prev_code: str, run_res: RunResult, round_idx: int) -> str:
    """
    Reflect：根据 Observe 的错误信息修复代码。
    """
    obs = {
        "ok": run_res.ok,
        "returncode": run_res.returncode,
        "timed_out": run_res.timed_out,
        "stdout_tail": (run_res.stdout[-2000:] if run_res.stdout else ""),
        "stderr_tail": (run_res.stderr[-2000:] if run_res.stderr else ""),
    }

    reflect_prompt = f"""
你正在进行第 {round_idx} 轮自动修复（Reflect）。
请阅读“运行观察（Observe）”与“旧代码”，定位问题并修复。

要求：
- 只输出修复后的【完整单文件代码】（不要解释、不要 Markdown）。
- 仍然不允许第三方库，仅标准库。
- 确保能启动运行，不要在导入阶段报错。
- 交互仍需友好，有输入校验与退出指令。

【用户需求】
{user_need}

【Think 规划】
{plan_text}

【运行观察（Observe）】
{json.dumps(obs, ensure_ascii=False, indent=2)}

【旧代码】
{prev_code}
"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PY},
        {"role": "user", "content": textwrap.dedent(reflect_prompt).strip()},
    ]
    raw = llm(messages, temperature=0.1, max_tokens=3000)
    return _extract_code(raw)


def _reflect_fix_web_files(user_need: str, prev_files: Dict[str, str], run_res: WebRunResult, round_idx: int) -> Dict[str, str]:
    """
    Reflect：根据 Web 自检错误修复三文件。
    """
    obs = {
        "ok": run_res.ok,
        "used_node_check": run_res.used_node_check,
        "stdout_tail": (run_res.stdout[-2000:] if run_res.stdout else ""),
        "stderr_tail": (run_res.stderr[-2000:] if run_res.stderr else ""),
    }

    reflect_prompt = f"""
你正在进行第 {round_idx} 轮自动修复（Reflect）。
请根据“自检错误信息”修复 Web 项目（index.html/style.css/main.js）。

要求：
- 只能输出 JSON，且必须包含 index.html、style.css、main.js 三个键。
- 不使用任何第三方库/框架/外链 CDN。
- 游戏应可玩：方向键/WASD 控制，显示分数，撞墙/撞自己结束，支持重开/暂停。

【用户需求】
{user_need}

【自检观察（Observe）】
{json.dumps(obs, ensure_ascii=False, indent=2)}

【旧文件内容】
{json.dumps(prev_files, ensure_ascii=False)}
"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_WEB},
        {"role": "user", "content": textwrap.dedent(reflect_prompt).strip()},
    ]
    return _llm_web_files_with_retry(messages, max_attempts=3)


def react_loop(user_need: str, max_reflect_rounds: int = 3) -> Tuple[str, RunResult]:
    """
    ReAct 主循环：
    Think -> Act -> Observe -> (Reflect -> Act -> Observe) * N
    返回：最终游戏代码 与 最后一次运行结果
    """
    plan_text = _think_plan(user_need)

    # Act：初版
    code = _act_generate_code(user_need, plan_text)

    # Observe：轻量启动检查（多数游戏会等待输入，允许 timeout）
    res = run_code(code, timeout_sec=3, input_data="")

    def good_enough(rr: RunResult) -> bool:
        if rr.timed_out:
            return ("Traceback (most recent call last)" not in rr.stderr)
        return rr.ok and ("Traceback (most recent call last)" not in rr.stderr)

    if good_enough(res):
        return code, res

    # Reflect：最多修复 N 轮
    for i in range(1, max_reflect_rounds + 1):
        code = _reflect_fix_code(user_need, plan_text, code, res, round_idx=i)
        res = run_code(code, timeout_sec=3, input_data="")
        if good_enough(res):
            return code, res

    return code, res


def react_loop_web(user_need: str, max_reflect_rounds: int = 3) -> Tuple[Dict[str, str], WebRunResult]:
    """
    ReAct 主循环（Web 多文件）：
    Act -> Observe(自检) -> Reflect(修复) * N
    """
    files = _act_generate_web_files(user_need)
    res = run_web_project(files)
    if res.ok:
        return files, res

    for i in range(1, max_reflect_rounds + 1):
        files = _reflect_fix_web_files(user_need, files, res, round_idx=i)
        res = run_web_project(files)
        if res.ok:
            return files, res

    return files, res


def main():
    _setup_console_utf8()
    print("=== ReAct 简易游戏生成 Agent（DeepSeek）===")
    print("描述一个你想要的控制台小游戏，我会生成可运行代码，并自动尝试修复报错（最多 3 轮）。")
    print("示例：")
    print("- 做一个带难度选择的猜数字游戏")
    print("- 生成一个双人井字棋，支持重开/退出")
    print("- 文字冒险：在森林里找宝藏，包含背包与随机事件")
    print()

    user_need = input("请输入你的游戏需求：").strip()
    if not user_need:
        user_need = "做一个带难度选择的猜数字游戏（简单/普通/困难），有次数限制与再次游玩功能。"

    # Web 需求：生成多文件并落盘到 snake_game/
    if _is_web_game_need(user_need):
        files, res = react_loop_web(user_need, max_reflect_rounds=3)
        out_dir = os.path.join(_project_root(), "snake_game")

        print("\n=== 生成完成（Web 多文件）===")
        if res.ok:
            print("自检结果：通过。")
        else:
            print("自检结果：未通过（已达最大修复轮数），仍会写出当前版本便于你手动调整。")
            if res.stderr.strip():
                print("\n--- 自检错误（截断）---")
                print(res.stderr[-1500:])

        write_web_project(out_dir, files)
        print(f"\n已将文件写入：{out_dir}")
        print("打开方式：直接双击 index.html，或在该目录运行 `python -m http.server 8000` 后访问 http://localhost:8000")
        return

    # 默认：Python 控制台小游戏（单文件）
    code, res = react_loop(user_need, max_reflect_rounds=3)

    print("\n=== 生成完成（Python 单文件）===")
    if res.ok:
        print("自检结果：运行正常退出（returncode=0）。")
    elif res.timed_out:
        print("自检结果：程序已成功启动并等待输入（超时中断属于预期）。")
    else:
        print("自检结果：仍可能存在错误（已达最大修复轮数）。")
        if res.stderr.strip():
            print("\n--- stderr（截断）---")
            print(res.stderr[-1500:])

    print("\n=== 以下为最终可运行游戏代码（请复制保存为 game.py 运行）===\n")
    print(code)


if __name__ == "__main__":
    main()

