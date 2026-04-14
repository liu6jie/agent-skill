# 在线 P 图（本地运行）使用说明

## 目录约定
- `scripts/`：工具脚本与网页
- `assets/`：你要修的照片、以及 `manifest.json`
- `references/`：说明文档（本文件）

## 1) 把照片放进 assets
1. 把图片文件复制到根目录 `assets/`（例如 `assets/a.jpg`、`assets/b.png`）。
2. 编辑 `assets/manifest.json`，把文件名填进 `images` 数组，例如：

```json
{
  "images": ["a.jpg", "b.png"]
}
```

## 2) 启动本地“在线修图”
需要安装 Node.js（建议 18+）。

在项目根目录运行：

```bash
node scripts/serve.mjs
```

看到提示后，用浏览器打开：
- `http://localhost:5177/`
或
- `http://localhost:5177/scripts/`

## 3) 使用方法
- **加载**：点“从本地选择…”或从下拉框选 `assets/` 的图片再点“从 assets 加载”
- **调整**：缩放/旋转/移动，亮度/对比/饱和/色相，锐化/模糊
- **加水印**：填文字，调大小/透明度/颜色/位置
- **导出**：选 PNG/JPG（JPG 可调质量）→ 点“导出”

## 4) 常见问题
- 下拉框没图：检查 `assets/manifest.json` 是否存在、JSON 是否合法、文件名是否写对（大小写也要一致）。
- 直接双击打开 `scripts/index.html` 不行：这是因为浏览器限制 `file://` 读取本地文件，建议用 `node scripts/serve.mjs` 启动本地服务。

