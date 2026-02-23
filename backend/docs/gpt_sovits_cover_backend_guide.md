# GPT-SoVITS 翻唱后端接力文档（精简版）

## 1. 当前结论

- 架构已切到异步：FastAPI + Celery + Redis。
- `cover` 任务链路可跑通：创建任务、执行、查询、取消、下载。
- `scripts/gptsovits_separate.py` 是真实分离实现（直调 GPT-SoVITS UVR 模块）。
- `scripts/gptsovits_infer.py` 已切换为 GPT-SoVITS 官方 `TTS.run` 推理路径（保留原 CLI 协议）。
- 当前重点从“替换脚本”转为“端到端听感回归与参数微调”（ASR 文本质量会直接影响结果）。

## 2. 关键代码入口

- 路由：`app/api/routes/cover.py`
- 任务：`app/tasks/cover_tasks.py`
- 编排：`app/services/cover_pipeline.py`
- 运行器：`app/services/gpt_sovits_runner.py`
- 表结构：`app/db/models/cover_job.py`
- 分离脚本：`scripts/gptsovits_separate.py`
- 推理脚本（已接入运行时）：`scripts/gptsovits_infer.py`

## 3. 最小运行步骤

在 `backend` 目录执行：

```bash
conda activate voice_api
python init_db.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

另一个终端执行（必须）：

```bash
conda activate voice_api
celery -A app.tasks.cover_tasks worker --loglevel=INFO --queues=cover
```

## 4. AutoDL 推荐配置模板

`.env` 最关键条目：

```bash
REDIS_URL=redis://localhost:6379/0
COVER_QUEUE_NAME=cover
GPT_SOVITS_PYTHON=/root/miniconda3/envs/GPTSoVits/bin/python
GPT_SOVITS_PROJECT_ROOT=/root/GPT-SoVITS
COVER_UVR_MODEL=HP2_all_vocals
COVER_SEPARATE_CMD_TEMPLATE="{python_exec} scripts/gptsovits_separate.py --project-root {project_root} --input {song_input} --vocal {vocal_output} --inst {inst_output} --model {uvr_model} --device cuda --is-half true"
COVER_INFER_CMD_TEMPLATE="{python_exec} scripts/gptsovits_infer.py --project-root {project_root} --reference {reference_voice} --input {input_vocal} --output {output_vocal} --model-id {model_id} --pitch {pitch_shift}"
```

## 5. API 快速契约

- `POST /api/v1/cover/jobs`
  - 入参：`reference_voice`、`song`、`model_id?`、`pitch_shift?`
  - 返回：`job_id`、`task_id`
- `GET /api/v1/cover/jobs/{job_id}`
  - 返回：`status`、`stage`、`progress`、`error_message`
- `GET /api/v1/cover/jobs/{job_id}/result`
  - 仅 `succeeded` 可下载
- `POST /api/v1/cover/jobs/{job_id}/cancel`
  - 撤销 Celery 任务并更新状态

## 6. 验收标准（必须同时满足）

1. 创建任务后 5 秒内可查到 `status=queued|running`。
2. 任务阶段顺序可观察到：`preprocess -> separate -> infer -> mix -> finalize`。
3. 成功任务 `status=succeeded` 且可下载 `wav`。
4. 失败任务 `status=failed` 且 `error_message` 非空。
5. 取消任务后状态为 `canceled`。

## 7. 固定下一步任务（按优先级）

1. 在服务器部署并启动 `voice_ll/backend`，完成真实 API 链路回归：`POST /cover/jobs -> GET 状态 -> GET result`。
2. 给 `cover` 任务增加“可选文本输入”（参考文本/目标文本），有文本时跳过 ASR 以显著提速。
3. 将 `infer` 从“每任务拉起脚本”升级为“常驻推理服务调用”，避免每次重复加载大模型权重。
4. 调整推理参数（ASR 模型、切句策略、温度/惩罚系数）提升唱段稳定性。
5. 观察定时清理任务执行日志，确认 `COVER_RESULT_TTL_HOURS` 生效。

## 8. 可复制测试命令

示例文件（先准备）：

- `/tmp/ref.wav` 参考音色
- `/tmp/song.wav` 原曲

创建任务：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/cover/jobs" \
  -H "X-API-Key: your-api-key" \
  -F "reference_voice=@/tmp/ref.wav" \
  -F "song=@/tmp/song.wav" \
  -F "model_id=default" \
  -F "pitch_shift=0"
```

查询状态：

```bash
curl -H "X-API-Key: your-api-key" \
  "http://127.0.0.1:8000/api/v1/cover/jobs/<job_id>"
```

下载结果：

```bash
curl -L -H "X-API-Key: your-api-key" \
  "http://127.0.0.1:8000/api/v1/cover/jobs/<job_id>/result" \
  -o ./cover_result.wav
```

## 9. 可直接给 AI 的接力指令

```text
目标：在不改 FastAPI 路由与 Celery 任务协议的前提下，持续优化 backend/scripts/gptsovits_infer.py 的实际效果与稳定性。
约束：保留现有 CLI 参数（--project-root --reference --input --output --model-id --pitch），输出文件必须写到 --output，失败返回非0退出码并给清晰报错。
验收：按本文件第 6 节执行通过，最终能从 /api/v1/cover/jobs/{job_id}/result 下载可听的转换结果。
```

## 10. 2026-02-17 更新记录（本轮已完成）

### 10.1 代码与文档变更

- `scripts/gptsovits_infer.py` 已替换为真实 GPT-SoVITS 运行时调用：
  - 使用官方 `TTS.run` 推理流程；
  - 支持 `model_id` 动态权重解析（`weight.json` / `trained/<model_id>` / `GPT_weights*` + `SoVITS_weights*`）；
  - 保留既有 CLI 参数契约不变；
  - 失败时返回非 0 并输出可读日志。
- `README.md` 已同步说明：`gptsovits_infer.py` 不再是占位脚本。
- `requirements.txt` 已补 `requests>=2.31.0`（避免 `pytest` 收集 `test_auth.py` 时缺依赖）。

### 10.2 本地验证结果（Windows + conda `voice_api`）

- 测试命令：`conda run -n voice_api pytest -q`
- 结果：`26 passed`（有若干 Pydantic 警告，不影响通过）

### 10.3 服务器实跑结果（AutoDL）

- 已通过 SSH 将脚本同步到：
  - `/root/GPT-SoVITS/scripts/gptsovits_infer.py`
- 在服务器环境 `GPTSoVits` 中直接执行脚本推理成功，产物：
  - `/root/GPT-SoVITS/output/cover_test_from_backend.wav`
- `ffprobe` 结果：
  - `sample_rate=32000`
  - `channels=1`
  - `duration=2.100000`

### 10.4 当前已知瓶颈（为什么比 WebUI 慢）

- 当前是“任务脚本模式”，每个任务会重复初始化模型，冷启动开销大；
- 每个任务默认执行两次 ASR（参考音频 + 输入人声）；
- 服务器网络策略下，`faster-whisper` 未命中本地缓存会回退到 `openai-whisper`，首次会下载模型并变慢；
- WebUI 常驻进程通常可复用已加载模型，且可手填文本减少/跳过 ASR。

### 10.5 下轮执行指令（可直接抄给 AI）

```text
继续做“cover 端到端提速”：
1) 在不破坏现有 API 协议的前提下，为 /api/v1/cover/jobs 增加可选字段 reference_text、target_text；
2) 覆盖到 Celery 任务与 infer 命令，当文本存在时跳过 ASR；
3) 增加回归测试：有文本（跳过 ASR）与无文本（走 ASR）两条路径都通过；
4) 输出基准对比：改造前后同一输入的总耗时。
```
