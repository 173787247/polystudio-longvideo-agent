## 1. 当前长视频 Agent 的基础能力分析

本项目当前实现了一套“Agent 驱动”的长视频生成最小闭环，核心流程为：**分镜（StoryBoard）→ 每镜头生图 → 图生视频 → 拼接成片**。对应关键代码：

- `backend/app/services/agent_service.py`：长视频主流程编排（按镜头循环、时长归一化、角色参考图策略）
- `backend/app/tools/volcano_image_generation.py`：`generate_volcano_image_tool` / `edit_volcano_image_tool`
- `backend/app/tools/volcano_video_generation.py`：`generate_volcano_video_tool`
- `backend/app/tools/video_concatenation.py`：`concatenate_videos_tool`

### 1.1 现有工作流与数据如何在步骤间传递

输入是 `LongVideoRequest`，包含：

- **分镜**：`storyboard.shots[]`（每个镜头：`description`、`duration_s`、`character_ids`）
- **角色表**：`characters{character_id -> Character}`（可带 `reference_image_path`）
- **统一风格**：`style_prompt` / `negative_prompt`

输出是 `LongVideoResult`，包含成片路径、每段 clip 路径、每镜头的图片路径，以及时长校准前后信息。

数据流（简化）：

```mermaid
flowchart TD
  A[用户输入: storyboard + characters + style] --> B{是否指定 target_total_duration?}
  B -- 否 --> C[使用原分镜时长]
  B -- 是 --> D[normalize_durations 按比例缩放每镜头时长]
  C --> E[逐镜头循环]
  D --> E

  E --> F[构造 shot_prompt = style + 镜头描述 + 角色信息 + 一致性规则]
  F --> G{镜头是否包含角色?}
  G -- 否 --> H[generate_volcano_image_tool(prompt)]
  G -- 是 --> I[确保角色 reference 图存在]
  I --> J[对主角色 reference 做 edit_volcano_image_tool(prompt, reference)]
  H --> K[generate_volcano_video_tool(image, duration)]
  J --> K
  K --> L[收集 clip_paths]
  L --> M[concatenate_videos_tool(clip_paths)]
  M --> N[输出 final_video + 过程产物路径]
```

### 1.2 现有角色一致性：如何保证“同一角色跨镜头一致”

当前的一致性策略基于 **“参考图 + edit”**：

- **依赖输入**：`Character.reference_image_path`（该角色的统一参考图）
- **工具选择规则**：
  - 若镜头包含角色且该角色已有 `reference_image_path`：优先走 `edit_volcano_image_tool`（把镜头 prompt 叠加到参考图上）
  - 若镜头包含角色但该角色没有参考图：先用 `generate_volcano_image_tool` 生成“角色 reference（角色卡）”，回填到角色表，再对镜头走 `edit`
  - 不含角色镜头：直接 `generate`
- **Prompt 规则（在 shot_prompt 中约束）**：
  - 强调 “keep identities consistent / do not mix characters / maintain same face-hair-outfit”
  - `negative_prompt` 中包含 “mixed identity / face swap”等抑制串脸关键词

当前实现为了最小可运行做了简化：**当镜头有多个角色时只对“主角色（第一个 id）”做 edit**，这会导致“多角色同镜”场景下，其它角色的一致性约束较弱——这是第 2 部分需要扩展的重点。

### 1.3 现有时长处理：镜头时长、校验与调整

镜头时长体现在 `ShotSpec.duration_s`：

- **单段 clip 时长由谁决定**：由分镜的 `duration_s` 决定，传入 `generate_volcano_video_tool(image_path, duration_s, fps)`
- **是否支持总时长目标**：支持 `target_total_duration_s`（可选）
  - 若提供：`_normalize_durations()` 按比例缩放各镜头 `duration_s`，并设定每镜头最小时长 0.5s（避免 0 帧/不可见镜头）
  - 若不提供：使用原始分镜时长
- **拼接后校验/调整**：
  - 当前实现把“最终时长”视为 **分镜时长总和**（因为 mock 图生视频严格按 `duration_s * fps` 写帧）
  - 若未来接入真实视频生成，可能出现“返回时长与请求不一致”，建议在拼接前做：读取每段 clip 实际时长 → 与目标差异比较 → 通过补帧/裁剪/变速对齐（第 2 部分可进一步完善）

