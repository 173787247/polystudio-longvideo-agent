# polystudio-longvideo-agent

本仓库用于提交 **PolyStudio 长视频 Agent **

参考项目：[`hirogoing/PolyStudio`](https://github.com/hirogoing/PolyStudio)（主要参考其长视频工作流的目录约定与模块拆分方式）。

## 目录结构

- `docs/`：作业分析与方案说明（可放流程图/数据流图/截图）
- `src/`：可运行 demo
- `backend/`：后端代码（tools + service）
- `assets/`：图片等静态资源（可选）

## 作业内容索引

- 1）分析当前长视频 Agent 的基础能力：`docs/01-current-agent-analysis.md`
- 2）增加多角色一致性能力：`docs/02-multi-role-consistency.md`

## 本地运行（Mock 可跑通）

环境：Python 3.9+（建议 3.10/3.11）。

安装依赖：

```bash
cd backend
pip install -r requirements.txt
```

运行 demo（会生成镜头图片、clip 视频、最终拼接视频）：

```bash
cd ..
python src/demo.py
```

产物目录：

- `outputs/images/`：镜头生图与多角色合成图
- `outputs/videos/`：每镜头 clip 与 `final_*.mp4`

