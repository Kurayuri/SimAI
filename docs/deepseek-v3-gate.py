import torch
import torch.nn.functional as F
h = 1024
n_experts = 256
n_groups = 8
n_experts_per_group = n_experts // n_groups

top_experts = 8
top_groups = 4
top_experts_per_group = top_experts // top_groups

experts = [torch.nn.Linear(h, h) for _ in range(n_experts)]
ep_size = 1
ep_rank = 0
experts_per_rank = n_experts // ep_size

hidden_states = torch.rand(3, 2, h)
print("\nhidden_states.shape")
print(hidden_states.shape)
gate_weights = torch.rand(n_experts, h)

bsz, seq_len, h = hidden_states.shape
hidden_states = hidden_states.view(-1, h)
logits = F.linear(hidden_states, gate_weights)
scores = torch.sigmoid(logits)
print("\nscores.shape")
print(scores.shape)
scores = scores.view(bsz * seq_len, -1)

group_scores = scores.view(bsz * seq_len, n_groups, -1).topk(top_experts_per_group, dim=-1)[0].sum(dim=-1)
print("\ngroup_scores")
print(group_scores)
group_idx = torch.topk(group_scores, top_groups, dim=-1, sorted=False)[1]
print("\ngroup_idx")
print(group_idx)
group_mask = torch.zeros_like(group_scores)
group_mask.scatter_(1, group_idx, 1)
print("\ngroup_mask")
print(group_mask)
score_mask = group_mask.unsqueeze(-1).expand(bsz * seq_len, n_groups, n_experts_per_group).reshape(bsz * seq_len, -1)
print("\nscore_mask")
print(score_mask)
tmp_scores = scores.masked_fill(~score_mask.bool(), float("\n-inf"))
print("\ntmp_scores")
print(tmp_scores)
_, topk_idx = torch.topk(
    tmp_scores, top_experts, dim=-1, sorted=False
)
print("\ntopk_idx")
print(topk_idx)  # (bsz * seq_len, top_experts)
topk_weight = scores.gather(1, topk_idx)
print("\ntopk_weight")
print(topk_weight)
topk_ids = topk_idx
cnts = topk_idx.new_zeros((topk_idx.shape[0], n_experts))
print("\ncnts.shape")
print(cnts.shape)
cnts.scatter_(1, topk_ids, 1)
print("\ncnts")
print(cnts)
tokens_per_expert = cnts.sum(dim=0)
print("\ntokens_per_expert")
print(tokens_per_expert) # 在给定的bsz * seq_len个token下，每个expert的token数量

# topk_idx.shape = (bsz * seq_len, top_experts)，即bsz * seq_len个token各自选中的expert的序号
idxs = topk_ids.view(-1).argsort() # 将所有的token的选中expert序号按升序排列时，第几小的元素是原来的第几个（即argsort返回的就是sort的结果中每个元素是原来的对应元素的index）
print("\nidxs")
print(idxs)

x = hidden_states
print("\nidx//topk_ids.shape[1]")  # topk_ids.shape[1]即为top_experts
print(idxs // topk_ids.shape[1])   # idxs // topk_ids.shape[1] 即为所有的要dispatch的token究竟是哪一个token

sorted_tokens = x[idxs // topk_ids.shape[1]]
print("\nsorted_tokens.shape") # sorted_tokens 将所有要dispatch的token按expert的序号升序排列
print(sorted_tokens.shape)  # (bsz * seq_len * top_experts, h)

outputs = []
start_idx = 0
for i, num_tokens in enumerate(tokens_per_expert): # 每次处理一个expert下所有的被dispatch的token
    end_idx = start_idx + num_tokens
    if num_tokens == 0:
        continue
    print(i, num_tokens)
    expert = experts[i + ep_rank * experts_per_rank]
    tokens_for_this_expert = sorted_tokens[start_idx:end_idx]
    expert_out = expert(tokens_for_this_expert)
    outputs.append(expert_out)
    start_idx = end_idx
outs = torch.cat(outputs, dim=0) if len(outputs) else sorted_tokens.new_empty(0)
print("\nouts.shape")
print(outs.shape)  # (bsz * seq_len * top_experts, h)

new_x = torch.empty_like(outs)
new_x[idxs] = outs
print("\nnew_x.shape")
print(new_x.shape)  # (bsz * seq_len, h)

final_out = (
    new_x.view(*topk_ids.shape, -1)
    .type(topk_weight.dtype)
    .mul_(topk_weight.unsqueeze(dim=-1))
    .sum(dim=1)
    .type(new_x.dtype)
    )
print("\nfinal_out.shape")
print(final_out.shape)  # (bsz * seq_len, h)

