"""
岗位差异化评估标准。

每个岗位的"考察重点"和"扣分项"不一样，注入到 evaluator prompt 中
让 LLM 按岗位特性打分。

格式：每个岗位一段中文文字，会被嵌入到 prompt 的【岗位特定评估侧重】块。
"""

ROLE_SPECIFIC_CRITERIA = {
    "Java后端开发工程师": (
        "本岗位重点考察：\n"
        "- JVM 内存模型、GC 调优、类加载机制等底层原理\n"
        "- 并发编程（线程池、JUC、synchronized vs Lock、CAS）\n"
        "- Spring 全家桶（IoC/AOP 原理、Spring Boot 自动装配、Spring Cloud 微服务）\n"
        "- MySQL 索引/事务/锁、Redis 数据结构与缓存策略、消息队列（Kafka/RocketMQ）\n"
        "- 分布式系统设计（CAP、一致性、限流降级）\n"
        "扣分项：\n"
        "- 只会用框架不懂原理（如能写注解但说不清 AOP 是怎么实现的）\n"
        "- 在并发/事务/分布式场景下回答不能涉及边界条件和异常\n"
        "- 项目经历缺乏量化数据（QPS、延迟、容量等）"
    ),

    "Web前端开发工程师": (
        "本岗位重点考察：\n"
        "- JavaScript 核心（事件循环、闭包、原型链、this、async/await）\n"
        "- 框架原理（Vue 响应式 / React Fiber / 虚拟 DOM diff）\n"
        "- 浏览器原理（渲染流水线、回流重绘、跨域、HTTP 缓存）\n"
        "- 工程化（Webpack/Vite 打包优化、Tree Shaking、代码分割）\n"
        "- 性能优化（首屏加载、Lighthouse 指标、骨架屏、懒加载）\n"
        "扣分项：\n"
        "- 只会调 API 不懂底层（如能用 Vue 但说不清响应式原理）\n"
        "- 性能优化只会喊口号没具体方案和指标\n"
        "- CSS/兼容性问题处理经验不足"
    ),

    "Python算法工程师": (
        "本岗位重点考察：\n"
        "- 机器学习基础（过拟合、正则化、梯度下降、损失函数选择）\n"
        "- 深度学习框架（PyTorch / TensorFlow，模型搭建、训练循环、调参）\n"
        "- 数据处理与特征工程（缺失值、归一化、特征选择）\n"
        "- 模型评估与部署（混淆矩阵、AUC、模型压缩、推理加速）\n"
        "- 算法基础（数据结构、复杂度分析、动态规划/贪心）\n"
        "扣分项：\n"
        "- 只会调 sklearn / transformers 不懂数学原理\n"
        "- 项目缺乏完整闭环（只会训练不会评估、不会部署）\n"
        "- 模型选型缺乏对比和数据支撑"
    ),
}


def get_role_criteria(role: str) -> str:
    """
    根据岗位名返回特定评估标准文字。
    若岗位未注册，返回通用提示。
    """
    if not role:
        return "（按通用计算机岗位标准评估）"
    return ROLE_SPECIFIC_CRITERIA.get(role, f"（{role} 暂无定制评估标准，按通用计算机岗位评估）")
