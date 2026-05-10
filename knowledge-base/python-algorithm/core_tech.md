# Python 算法工程师核心技术能力

本指南详细说明了算法工程师在面试中所需具备的核心能力维度，这些维度与我们的面试题库直接对应。

## Python语言核心
- **底层原理**：CPython 内存模型、引用计数与分代回收机制、小整数池与 intern 机制、PyMalloc 内存池架构。
- **并发异步**：GIL 机制原理及其对多线程的影响、协程 (asyncio) 事件循环底层实现、多进程 (multiprocessing) 进程间通信逻辑。
- **高级编程**：装饰器逻辑与闭包、生成器与迭代器协议、上下文管理器、元类 (metaclass)、面向切面编程 (AOP) 模拟实现。
- **性能加速**：NumPy 向量化运算原理、Cython 静态编译、Numba 原时编译 (JIT) 优化、多线程/多进程选型策略。

## 数据结构与算法基础
- **核心结构**：哈希表工业级实现（冲突解决/扩容）、堆（优先队列）、红黑树/B+ 树应用场景、并查集、前缀树 (Trie)。
- **算法范式**：动态规划 (DP) 状态转移方程推导、贪心算法证明、深搜 (DFS) 与广搜 (BFS) 启发式搜索 (A*)、二分查找变体。
- **高级场景**：海量数据处理 (Bloom Filter/Bitmap)、滑动窗口、双指针、Top-K 问题、排序算法稳定性与空间开销对比。

## 机器学习与数据处理
- **核心算法**：线性回归/逻辑回归数学推导、支持向量机 (SVM) 核函数、决策树体系 (ID3/C4.5/CART)。
- **集成学习**：Bagging (Random Forest) 与 Boosting (XGBoost/LightGBM/CatBoost) 底层优化机制、Stacking 策略。
- **深度评估**：损失函数 (Loss Functions) 选型、L1/L2 正则化物理意义、模型过拟合/欠拟合调优、样本不平衡处理。
- **特征工程**：特征编码 (One-hot/Target)、特征降维 (PCA/LDA)、特征选择算法、归一化与标准化应用时机。

## 深度学习与大模型
- **核心组件**：CNN (感受野/池化/空洞卷积)、RNN/LSTM 梯度消失问题、Transformer 全架构深度拆解（Self-Attention/Positional Encoding）。
- **大模型进阶**：参数高效微调 (LoRA/AdaLoRA/P-Tuning)、RAG 环境搭建与向量检索流、RLHF 强化学习对齐、量化感知训练 (QAT)。
- **训练逻辑**：优化器 (Adam/AdamW/LAMB) 内部原理、权重初始化策略、Dropout/LayerNorm 选型。

## 模型部署与工程实践
- **推理加速**：模型量化 (INT8/FP8/NF4)、剪枝与蒸馏技术、算子融合、TensorRT/ONNX Runtime 推理框架应用、Triton Inference Server。
- **工程实践**：FastAPI/Flask 模型接口高度封装、Docker 容器化 AI 环境、分布式训练 (DDP/TP/PP/ZeRO)、MLflow 生命周期管理。
- **性能监控**：数据漂移 (Data Drift) 监控、模型版本回滚策略、A/B 测试方案设计。
