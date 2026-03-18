## 2. 增加多角色一致性能力（方案 + 关键伪代码/实现）

### 2.1 目标

支持同一部长视频中出现多个不同角色（如 A、B），并满足：

- **同一角色跨镜头保持一致**（脸/发型/服装等身份特征稳定）
- **不同角色之间不混淆**（避免串脸、互换身份）
- **镜头级可控**：每个镜头清晰标注有哪些角色参与，生图阶段能自动选到正确参考图并决定 generate vs edit

### 2.2 数据结构（角色表 + 镜头角色标注）

本项目采用“角色注册表 + 镜头角色列表”：

- **角色表**：`characters: Dict[character_id, Character]`
  - `Character.reference_image_path`：该角色的统一参考图（关键）
- **镜头标注**：`ShotSpec.character_ids: List[str]`

角色 reference 图来源：

- 若用户提供：直接写入 `Character.reference_image_path`
- 若未提供：在角色首次出现时，由 Agent 生成 “CHARACTER SHEET（角色卡）” 并回填到角色表，用作后续镜头的 edit 参考

### 2.3 关键决策：为每个镜头选择 generate 还是 edit

规则（实现位于 `backend/app/services/agent_service.py`）：

- **镜头不含角色**：`generate(prompt)` 直接生图
- **镜头含 1 个角色**：确保该角色 reference 存在后，`edit(prompt, reference)` 生图
- **镜头含多个角色**（本作业扩展点）：
  - 为每个角色分别执行一次 `edit(prompt + FOCUS_CHARACTER, role_reference)`，得到 `per_role_images[]`
  - 将 `per_role_images[]` **合成为最终镜头图**（mock 中用 blend 合成；真实接入可替换为带 mask 的多角色合成/布局控制）

### 2.4 关键伪代码

```text
for shot in storyboard.shots:
  prompt = build_shot_prompt(style, shot.description, shot.character_ids)

  if shot.character_ids is empty:
    image = generate(prompt)
  else:
    # 1) 确保每个角色都有 reference
    for cid in shot.character_ids:
      if characters[cid].reference is None:
        characters[cid].reference = generate("CHARACTER SHEET ...")

    # 2) 多角色：对每个角色分别 edit，避免只约束“主角色”
    images = []
    for cid in shot.character_ids:
      images.append(edit(prompt + "FOCUS_CHARACTER=<name>", characters[cid].reference))

    # 3) 合成一个镜头图（真实场景可用 mask/布局；作业 mock 用 blend）
    image = composite(images)

  clip = image_to_video(image, duration=shot.duration_s)
final = concat(clips)
```

### 2.5 与现有工具/Prompt 的关系（为什么这样能减少串脸）

- **参考图绑定到角色 id**：保证每次 edit 都在“正确角色的 reference”上进行
- **每角色单独 edit**：让“角色身份约束”分别施加，减少多个角色同时出现时的身份漂移
- **Prompt 约束与 negative_prompt**：
  - prompt 强调 “keep identities consistent / do not mix characters”
  - negative_prompt 明确 “mixed identity / face swap”等抑制项

### 2.6 可进一步增强（非本次作业必需）

- **真实多角色同框**：引入 mask/分区布局（左/右/远/近）实现更强控制
- **时长对齐**：读取 clip 实际时长，对不一致的段进行补帧/裁剪/变速

