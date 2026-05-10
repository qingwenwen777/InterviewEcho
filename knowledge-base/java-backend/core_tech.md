# Java 后端开发核心技术能力

本指南详细说明了 Java 后端工程师在面试中所需具备的核心能力维度，这些维度与我们的面试题库直接对应。

## Java基础
- **语言核心**：数据类型（位运算、包装类缓存、浮点精度）、String 原理（intern、对象布局）、异常体系（Checked vs Unchecked、try-with-resources）。
- **面向对象**：接口与抽象类演进（Java 8-17 特性）、内部类原理、Lambda 表达式与 Stream API 底层机理。
- **集合框架**：List (ArrayList/LinkedList)、Set (HashSet/TreeSet/LinkedHashSet)、Map (HashMap/TreeMap/ConcurrentHashMap)、Queue (PriorityQueue/DelayQueue)、核心扩容机制、迭代器 Fail-fast。
- **泛型与反射**：类型擦除、通配符（PECS原则）、反射机制对性能的影响、动态代理原理（JDK vs CGLIB）。
- **IO 模型**：BIO、NIO（Buffer、Channel、Selector）、AIO 原理，Netty 框架基础架构。

## 并发编程
- **底层原理**：JMM 内存模型、原子性/可见性/有序性、Happens-before 规则、synchronized 锁升级逻辑、volatile 屏障。
- **AQS 体系**：ReentrantLock、ReentrantReadWriteLock、Semaphore、CountDownLatch、CyclicBarrier、Phaser。
- **原子类**：AtomicInteger/Long、LongAdder (分段累加原理)、CAS 与 ABA 问题。
- **线程池**：ThreadPoolExecutor 核心参数、阻塞队列类型、拒绝策略、ForkJoinPool 工作窃取算法、优雅关闭机制。
- **线程通信**：wait/notify、Condition、ThreadLocal (内存泄漏预防)、CompletableFuture 异步编排。

## JVM原理
- **内存布局**：运行时数据区（堆、栈、方法区、元空间、直接内存）、TLAB、PLAB 分配。
- **垃圾回收**：分代模型、可达性分析、GC 算法（复制/标清/标整）、CMS (并发标记)、G1 (Region/SATB/CSet)、ZGC (染色指针/Load Barrier)。
- **类加载机制**：加载、验证、准备、解析、初始化；双亲委派、沙箱安全、自定义类加载器、破坏双亲委派（SPI/热部署）。
- **性能监控与调优**：OOM 诊断（堆溢出、栈溢出、方法区溢出）、CPU 飙升定位、常用指令（jps、jstat、jinfo、jmap、jstack、jcmd）、Arthas 或可视化诊断工具。

## Spring框架与工程化
- **Spring 核心**：IoC 容器逻辑、Bean 生命周期（三级缓存/循环依赖）、BeanPostProcessor、AOP 增强（切面/切点/切入点）、声明式事务机制。
- **Spring Boot**：自动装配机制原理（SPI/Imports）、Starter 设计模式、自洽配置体系。
- **Spring MVC**：请求处理流程（DispatcherServlet）、过滤器与拦截器机制。
- **Spring Cloud**：注册中心（Nacos/Consul）、配置中心、负载均衡（Ribbon/LoadBalancer）、熔断限流（Sentinel/Hystrix）、网关（Gateway）、Feign 声明式调用。

## 数据库与缓存
- **关系型数据库 (MySQL)**：B+ 树索引结构、覆盖索引、最左前缀原则、事务 ACID、隔离级别（MVCC）、锁机制（行锁/间隙锁/临键锁）、SQL 优化、Explain 分析、Buffer Pool。
- **非关系型数据库 (Redis)**：五种基础结构、Bitmaps/HyperLogLog/GEO、持久化（RDB/AOF）、主从/哨兵/集群、缓存穿透/击穿/雪崩、双写一致性、分布式锁。
- **其他中间件**：Kafka/RabbitMQ 选型、可靠传输保障、搜索引擎 (ES) 倒排索引原理。

## 分布式与微服务架构
- **分布式理论**：CAP 定理、BASE 理论、Paxos 与 Raft 算法。
- **分布式事务**：2PC/3PC、TCC 补偿模式、Saga 柔性事务、本地消息表、Seata 框架。
- **稳定性治理**：服务注册发现、全链路追踪（Zipkin/Skywalking）、蓝绿发布、金丝雀发布、熔断/降级/限流。
