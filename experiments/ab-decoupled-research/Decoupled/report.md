# Python GIL 调研报告

## 定义
GIL（Global Interpreter Lock）是CPython中的全局互斥锁，保证同一时刻只有一个线程执行Python字节码。它保护引用计数等内部状态，但导致CPU密集型多线程无法利用多核。

## 历史
- 1990年代：GIL随CPython诞生
- 1999/2007/2015：多次移除尝试失败（性能下降）
- 2023.07：Sam Gross提交PEP 703
- 2024.01：指导委员会接受PEP 703
- 2024.10：Python 3.13发布，实验性自由线程
- 2025.10：Python 3.14发布，自由线程正式支持（PEP 779）

## 影响
- CPU密集型：多线程无法并行，甚至因线程切换开销更慢
- I/O密集型：GIL在等待I/O时自动释放，网络请求和文件读写仍有加速效果
- C扩展：可主动释放GIL，numpy、pandas等底层计算可并行
- 移除GIL后：单线程性能可能下降5-15%（更细粒度锁的开销），但多线程可线性扩展到多核
- 生态影响：C扩展需要适配自由线程模式，预计2-3年完成主流库适配

## 解决方案
1. 多进程（multiprocessing）：每个进程独立GIL，适合CPU密集型，但进程间通信有开销
2. 异步（asyncio）：单线程事件循环，适合I/O密集型高并发场景
3. C扩展释放GIL：在C层计算时主动释放，numpy等库已支持
4. 自由线程构建：Python 3.13实验性支持，3.14起正式受支持，未来将成为默认

## 未来展望
根据PEP 703路线图，Phase III将在3.15+版本让自由线程成为默认构建，GIL变为可选项。最终目标是完全移除GIL，让Python真正拥抱多核时代。但这需要整个生态的配合，预计还需要数年时间完成过渡。

## 参考
- PEP 703: https://peps.python.org/pep-0703/
- PEP 779: https://peps.python.org/pep-0779/
- Python 3.13: https://docs.python.org/3.13/whatsnew/3.13.html
