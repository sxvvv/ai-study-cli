# AI Study CLI - AI Infra 学习助手 🚀

一个帮助你系统学习 AI 基础设施知识的命令行工具。每个知识点都配"mini实现"仓库做跳板，先跑通最小版本再读生产级源码。

## 为谁设计？

如果你在做国产 GPU 推理加速 / RL 基建 / AI Infra 相关工作，需要系统掌握从 LLM 训练到推理引擎到国产硬件适配的全栈能力，这个工具就是为你准备的。

## 学习路线（84天，6层渐进）

| 阶段 | 天数 | 内容 | 核心仓库 |
|------|------|------|----------|
| 1 | Day 1-15 | **LLM从零理解** | MiniMind → MiniMind-V |
| 2 | Day 16-27 | **GPU编程 CUDA/Triton** | LeetCUDA + Triton-Puzzles |
| 3 | Day 28-45 | **推理引擎** | nano-vllm → vLLM V1 |
| 4 | Day 46-58 | **自制推理框架** | llm.c → KuiperLLama |
| 5 | Day 59-72 | **RL训练基建** | veRL + OpenRLHF |
| 6 | Day 73-84 | **国产GPU适配** | 昇腾CANN + 海光HIP |

同时穿插 **精选算法刷题**（~30题，聚焦 AI Infra 相关：LRU Cache、调度、Trie、拓扑排序、DP）。

## 核心理念

- **每层都有mini版跳板**：看不懂 vLLM 十万行？先读 nano-vllm 1200行
- **CS底层按需补课**：不考408，只学和AI Infra直接相关的OS/体系结构概念
- **通关标准明确**：每层都有"你必须能做到"的验收指标

## 快速开始

```bash
git clone https://github.com/你的用户名/ai-study-cli.git
cd ai-study-cli
python study.py init     # 可选：配置微信推送
python study.py today    # 查看今日任务
python study.py done 1-1-1  # 完成后标记
python study.py quiz     # 做知识自测
python study.py status   # 查看总进度
```

## 所有命令

| 命令 | 说明 |
|------|------|
| `study today` | 📅 查看今日学习任务 |
| `study done <ID>` | ✅ 标记任务完成 |
| `study skip <ID> [原因]` | ⏭️ 跳过任务 |
| `study status` | 📊 查看总体进度 |
| `study quiz` | 🧠 知识自测（间隔重复） |
| `study quiz-done <ID> <结果>` | 📝 记录答题（understand/fuzzy/not） |
| `study resources` | 📚 查看当前阶段推荐资料 |
| `study add <url> [标签]` | 📌 添加自定义资料 |
| `study history` | 📜 最近学习记录 |
| `study week` | 📊 本周学习周报 |
| `study init` | 🔧 首次初始化设置 |
| `study notify` | 📱 发送今日任务到微信 |
| `study remind [HH:MM]` | ⏰ 设置定时提醒 |

## 每层通关标准

| 层级 | 你必须能做到 |
|------|-------------|
| 第一层 | 自己训练一个能对话的小LLM（含GRPO），能讲清Transformer每一层 |
| 第二层 | 用Triton写一个Fused RMSNorm kernel，性能超过PyTorch原生 |
| 第三层 | 能画出vLLM数据流图，能解释PagedAttention |
| 第四层 | 有一个能跑的C++/CUDA推理引擎 |
| 第五层 | 能跑通veRL的PPO训练，能解释Actor/Critic通信机制 |
| 第六层 | 能把一个CUDA kernel改为HIP/CANN版本跑通 |

## 内置精选资料

包含 Datawhale 系列（diy-llm / happy-llm / self-llm / unlock-deepseek）、MiniMind 系列、nano-vllm / KuiperLLama 等优质开源仓库，按阶段组织。运行 `study resources` 查看。

## 知识自测

基于**间隔重复**算法，题目紧扣 AI Infra 核心概念：
- PagedAttention / Continuous Batching / FlashAttention
- CUDA memory hierarchy / Triton编程模型
- PPO / DPO / GRPO 对比
- 国产GPU适配要点

## 技术栈

- 纯 Python 3，无第三方依赖
- PushPlus API（微信推送）
- Windows Task Scheduler / crontab（定时提醒）
- JSON 文件存储（轻量可移植）

## 许可

MIT License - 随便用，学习最重要 📖
