# Install
## AICB
AICB等效于文中的SimAI-WG，用于实机运行模型或根据模型生成workload
```sh
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
pip install gymnasium==0.29
pip install matplotlib
pip install 'platformdirs>=2.1'
pip install einops
pip install git+https://github.com/fanshiqing/grouped_gemm@v1.0
```

### apex
```sh
git clone https://github.com/NVIDIA/apex.git
pip install -v --disable-pip-version-check --no-cache-dir --no-build-isolation --config-settings "--build-option=--cpp_ext" --config-settings "--build-option=--cuda_ext"  --config-settings "--build-option=--fast_layer_norm" ./
```

### flash-attention
```sh
git clone https://github.com/Dao-AILab/flash-attention.git
python setup.py install
```




# Topo
## Create Topo
```sh
python3 ./astra-sim-alibabacloud/inputs/topo/gen_Topo_Template.py -topo Spectrum-X -g 128 -gt A100 -bw 100Gbps -nvbw 2400Gbps
python3 ./astra-sim-alibabacloud/inputs/topo/gen_Topo_Template.py -topo NVL
python3 ./astra-sim-alibabacloud/inputs/topo/gen_Topo_Template.py -topo NVL -gps 36
python3 ./astra-sim-alibabacloud/inputs/topo/gen_Topo_Template.py -topo NVL -gps 36　
```
-g 128个GPU   
-gt GPU Type  

### Topo type 
#### Spectrum-X
每个Node/Server有8[gpu_per_server]个GPU
Node 0中GPU0和ASW0连，Node 0中GPU1和ASW1连，共8个ASW
每个ASW和PSW连，共64个PSW

## Topo file
`Spectrum-X_128g_8gps_100Gbps_A100`

1. 网络的基本参数。
```
216 8 16 72 768 A100
```
- `216`: 总节点数，包括 GPU 节点和交换机节点。
- `8`: 每台服务器上的 GPU 数量。
- `16`: NVSwitch 的数量。
- `72`: 非NVSwitch的交换机的数量。
- `768`: 总链路数。
- `A100`: GPU 类型。

2. 交换机节点的编号。
```
128 129 130 ... 215
```
- 表示从 `128` 到 `215` 的节点是交换机节点，包括 NVSwitch、AccessSwitch (ASW) 和 PodSwitch（PSW）[节点按照此顺序]。

3. 节点之间的连接关系。
每一行表示一个连接，格式如下：
```
<源节点> <目标节点> <带宽> <延迟> <错误率>
```
- `<源节点>`: 起始节点编号。
- `<目标节点>`: 目标节点编号。
- `<带宽>`: 链路带宽，例如 `2400Gbps` 或 `100Gbps`。
- `<延迟>`: 链路延迟，例如 `0.000025ms` 或 `0.0005ms`。
- `<错误率>`: 链路错误率（通常为 `0`）。




# AICB
AICB等效于文中的SimAI-WG，用于实机运行模型或根据模型生成workload
包括典型的配置LLM运行配置（典型模型在典型框架Megatron/DeepSpeed的典型并行配置）


其运行方式主要包括三个
1. 实机测量计算、通信耗时，生成`Workload`
2. 根据已有的耗时，生成和可以用于`SIMAI_workload`

## Term
### `aiob`
一种机制/模式  
在模型运行时则实际记录其计算、通信耗时；或在在生成workload时填入前者获得的耗时数据
### workload
分为`Workload`和`SIMAI_workload`
#### `Workload`
`aicb/log_analyzer/log.py/Wordload`  
其本质是`aicb/log_analyzer/log.py/LogItem`的list容器。  
#### `SIMAI_workload`
`aicb/workload_generator/AIOB_simAI_workload_generator.py/SIMAI_workload`  
其本质是其子成员`SIMAI_workload.work`的生成器  
`SIMAI_workload.work`是`aicb/workload_generator/AIOB_simAI_workload_generator.py/Work_Item`的list容器

## 实机测量，生成workload日志
```sh
export MASTER_ADDR=127.0.0.1                                                
export MASTER_PORT=23089
export WORLD_SIZE=1
export RANK=0

sh ./scripts/megatron_gpt.sh \
-m 13 --world_size 4 --tensor_model_parallel_size 4 --pipeline_model_parallel 1 \
--frame Megatron --global_batch 2  \
--micro_batch 1 --seq_length 4096 \
--workload_only \
--swiglu --use_flash_attn  --aiob_enable
```
### 代码解析
该场景下的workload指的是`aicb/log_analyzer/log.py/Wordload`。

#### `MegatronModel`及其子模块
模型，分为真实模型（继承于`torch.nn.Module`）和模仿模型（继承于`aicb/workload_generator/mocked_model/MockedModel.py/MockedModel`）
##### `torch.nn.Module`
`MegatronModel`下的包括的所有的模块的forward（即__calll__）的具体GPU计算调用都封装在以`_apply`开头的函数中  
此类函数被`aicb/utils/utils.py`中的装饰器`cuda_timing_decorator`装饰，计算cuda的执行时间，并在`_apply`开头的函数的计算返回值中附带执行时间
`MegatronModel`的forward统计这些模块的执行时间，经过处理（计算min，avg）后并将其写入到指定的文件中


##### `MockedModel`
模仿模型`aicb/workload_generator/mocked_model/MockedMegatron.py/MegatronModel`继承于`aicb/workload_generator/mocked_model/MockedModel.py/MockedModel`
此时`MegatronModel`下的包括的所有的模块的forward和backward中不涉及具体计算，而是递归地**返回**汇总每一个模块的**workload**

#### `run_suites.py`
`aicb/run_suites.py`
在物理机上运行workload，包括所有的运行配置，调用`megatron_gpt.sh`或`deepspeed_llama.sh`

#### `megatron_gpt.sh`/`deepspeed_llama.sh`
`aicb/scripts/megatron_gpt.sh`
`aicb/scripts/deepspeed_llama.sh`
Shell形式的入口，启动调用`aicb/aicb.py`或`aicb/workload_generator/generate_megatron_workload.py`  
如果启用`aiob`则会调用`aicb.py`，反之会直接调用`generate_megatron_workload`  
在`aicb.py`中包括对于`generate_megatron_workload.py`的调用，还包括其他逻辑

#### `generate_megatron_workload.py`
仅生成基于`MockedModel`的完整workload
##### `MegatronWorkload`
`aicb/workload_generator/generate_megatron_workload.py/MegatronWorkload`继承于`aicb/workload_generator/workload_generator.py/WorkloadGenerator`，即`MegatronWorkload`本身是一个`WorkloadGenerator`而不当作wordload本身，它需要attach一个 `MockedModel`模型  
`WorkloadGenerator`
> forward和backward通过调用`MockedModel`的forward和backward获取模型本身的wordload外，还会处理流水线并行pp等引入的的额外workload
> `__call__`函数数会调用自身的forward和backward，处理汇总后返回模型的workload  


##### `__main__`
1. 创建一个继承于`MockedModel`的`MegatronModel`
2. 针对该`MockedModel`创建一个`MegatronWorkload`，调用该generator的`__call__`函数得到模型的workload
3. 输出workload，然后可视化

#### `aicb.py`
先调用`generate_megatron_workload.py`获得完整的workload，然后在GPU上简单测试模型中模块的计算、通信时间，最后基于测得的时间填入workload得到完整的含有预估时间的workload

1. 和`generate_megatron_workload.py`的`__main__`相同，获得基于`MockedModel`完整的workload
2. 调用`aicb/utils/utils.py`中的`get_comp_out`函数，该函数会
    运行使用一个dummpy_input输入到继承于`torch.nn.Module`的真实模型`aicb/workload_generator/mocked_model/AiobMegatron.py/MegatronModel`
    真实模型运行计算的同时会统计自身模块的执行时间，经过处理（计算min，avg）后并将其写入到指定的文件中
    返回时间统计文件的地址
3. 调用`aicb/utils/utils.py`中的`extract_averages`函数，该函数会
    正则读取上述执行时间统计文件，保存到dict`compute_cache`中
    grad_forward,grad_backward为统计文件中的`param_time`部分下的`time_gpu_min`和`time_gpu_min`
4. 调用`aicb/utils/utils.py`中的`Comp_with_aiob`函数，该函数会
    将`compute_cache`写入到workload中每一个item的`_elapsed_time`
5. 如果要测量通讯时间
    会针对workload创建一个`aicb/workload_applyer.py/WorkloadApplyer`
    `WorkloadApplyer`执行其`apply_workload`，该函数会将将workload中所有的通信都执行一遍，统计总耗时，其中
        会调用`aicb/workload_applyer.py/WorkloadApplyer`中通信操作对应的"__apply"开头的函数
        这些函数被`aicb/log_analyzer/log.py/bench_logger.log_timing`装饰器装饰
        该装饰器会统计"__apply"开头的函数内部的耗时，并记录到`bench_logger`中
6. 输出、分析`bench_logger`的日志



## 基于测量时间，生成`SIMAI_workload`
```sh
sh ./scripts/megatron_workload_with_aiob.sh \
-m 7 --world_size 4096 \
--tensor_model_parallel_size 2 --pipeline_model_parallel 1 \
--frame Megatron --global_batch 8192 \
--micro_batch 1 --seq_length 4096 \
--swiglu --use_flash_attn  --aiob_enable

```
`AIOB`启用时在使用物理GPU上实测的计算和通讯时间`compute_cache`，反之使用默认值

生成Seq of 计算和通讯操作（子模块/Kernel级别）
**不能实现Kernal融合**只能实现无依赖关系时的overlap

### 代码分析
该场景下的workload指的是`aicb/workload_generator/AIOB_simAI_workload_generator.py/SIMAI_workload` 的list子成员work，work中包括一系列的`aicb/workload_generator/AIOB_simAI_workload_generator.py/Work_Item`
#### `megatron_workload_with_aiob.sh`
`./scripts/megatron_workload_with_aiob.sh`
Shell入口调用`AIOB_simAI_workload_generator`

#### `AIOB_simAI_workload_generator.py`
`aicb/workload_generator/AIOB_simAI_workload_generator.py`
1. 读取`compute_cache`（可选）
2. 针对`MockedModel`生成一个`SIMAI_workload`
3. 调用`SIMAI_workload`的`workload_generate` （不用`compute_cache`，work项填入默认时间） 或 `workload_generate_aiob`（根据`compute_cache`，work项填入时间），生成`SIMAI_workload`的内容
4. 输出`SIMAI_workload`的内容

##### `workload_generate`  
`forward_compute_time`，`backward_compute_time`，`dp_compute_time`都是`default_compute_time`为1

##### `workload_generate_aiob`  
1. 使用`self.get_model_details`,迭代遍历model的child_module，读取每个child_module的parameters，只有特定的module为Layer，将Layer和其parameters信息构成LayerInfo保存到layers
2. 使用`self._get_total_params`，将`self.get_model_details`获得的layers中的每个LayerInfo的param_count分一般和moe两类，计算总一般参数量和moe参数量
3. 使用`_get_aiob_compute_time` 根据`compute_cache`中`grad_forward`、`grad_backward`填
入forward_compute_time和backward_compute_time








# Simulation
`SimAI/astra-sim-alibabacloud/astra-sim/workload`读取workload文件

# SimAI-CM
SimAI-Analytical下，不做包级别的模拟，直接用大小/带宽计算耗时
`SimAI/astra-sim-alibabacloud/astra-sim/network_frontend/`
`analytical`  


SimAI-Simulation下，包级别仿真（ns-3-alibabacloud）或直接物理运行
`ns3`
`phynet`


SimCCL通过劫持NCCL实现集合算子到p2p的流通信（包括使用gpu中转时的步骤）
`SimAI/astra-sim-alibabacloud/astra-sim/system/MockNCCL**`模仿劫持NCCL
`SimAI/astra-sim-alibabacloud/astra-sim/system/collective`集合通信算法
`SimAI/astra-sim-alibabacloud/astra-sim/system/topology`集合通信逻辑拓扑


**在专家并行 （EP） 中，门控模块的令牌分布受数据值的影响。在仿真中，我们假设分布均衡，这对仿真结果的影响最小。**

# SimAI-CP
"SimAI-WG 输出具有相应 GPU 的主机上所有子模块的执行时间"
如果submodule级别不够精确，就用kernel级别
（在 SimAI-CP 中维护一个作数据库，该数据库记录基准测试套件中所有子模块/kernel的执行时间。）

SimAI-CP-Model
对于不能在实机上确定的运行时间的情况，可以通过区分内存/计算瓶颈来估算新内存/算力下的运行时间

**元数据交换和 barrier作（小于 1 KB）可以忽略不计，不是我们模拟的重点**








# 关系计算
epoch: dataset的数据全部过一遍
batch: 一批次处理的数据

batch_size=一批次处理的数据的数量
n_batches：批次数

minibatch_size=一mini批次处理的数据的数量
```
dataset_size = n_batches * batch_size
```

`dp_degree` ：一batch数据分给dp_degree组不同的Device



```
batch_size = dp_degree * (n_minibatches * minibatch_size)
n_minibatches = gradient_accumulation_steps
```


```
world_size = dp_degree * dp_group_size
dp_group_size = pp_degree * pp_group_size
pp_group_size = ep_degree * ep_group_size
ep_group_size = tp_degree = tp_group_size
```
```
n_experts % ep_degree == 0 
```

aicb/utils/utils.py/RankGenerator



## pp_comm_value 在一个minibatch中每个GPU的tensor传输大小
LLM中每一“个”数据由seq_length个token组成，每一个token是hidden_size大小的向量

```
pp_comm_value = 2 * minibatch_size * seq_length * hidden_size
if enable_sp:
    pp_comm_value /= tp_size
```
