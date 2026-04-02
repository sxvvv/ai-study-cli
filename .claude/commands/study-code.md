# Code Practice Session

Help the user practice coding for their current study topic.

## Steps

1. Run `python study.py today` to determine the current phase and day.

2. Based on the phase, create a focused coding exercise:

   **Phase 1 (LLM Basics)**: Implement a Transformer component from scratch
   - Write a self-attention function, implement RoPE, build RMSNorm, etc.
   - Goal: understand every line of a Transformer

   **Phase 2 (GPU/CUDA/Triton)**: Write a CUDA or Triton kernel
   - Vector add → Softmax → RMSNorm → GEMM → FlashAttention mini
   - Start naive, then optimize step by step

   **Phase 3 (Inference Engine)**: Implement a PagedAttention component
   - Block manager, KV cache allocation, continuous batching scheduler
   - Read nano-vllm source first, then reimplement a simplified version

   **Phase 4 (C++ Framework)**: Write C++ inference code
   - Weight loading, matrix multiply, KV cache in C/C++
   - Start from llama2.c style

   **Phase 5 (RL Training)**: Implement PPO/GRPO components
   - Advantage computation, reward normalization, clip mechanism
   - Compare veRL and OpenRLHF implementations

   **Phase 6 (MACA Adaptation)**: Write MACA kernel or migration code
   - Port a CUDA kernel to MACA (API renaming)
   - Write a macaBLAS GEMM call
   - Create a torch_maca inference script

3. Guide the user step by step:
   - Show the problem statement and expected output first
   - Give hints, not answers
   - When they finish, review their code for correctness, then performance
   - Show the "production-quality" version and explain the differences

4. Focus on: **correctness first, then performance, then style**

## Rules
- The user should write the code themselves. You guide, don't write for them.
- Start with the simplest version that works, then iterate.
- After each exercise, suggest what to study next.
- If the user is stuck for more than 5 minutes, give a more specific hint.
