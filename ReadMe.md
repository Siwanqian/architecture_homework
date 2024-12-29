# Note
- 四个文件夹中分别为支持/不支持推测的单/双发射处理器代码。
- **建议在vscode中打开输出结果的txt文件，可能是由于版本原因，windows自带的txt阅读器输出的表格不是对齐的。**
- 对于任务1中的两个output，是完整地运行结果，参考了书中的处理方式，对寄存器和存储器中的值没有设具体的值，而是用诸如Regs[x1]的方式替代。
- 任务2中的两个output的执行结果是完整地执行了两次迭代后的实验结果。由于存在迭代，为了避免冲突，因此对寄存器和存储器中的数据设置了具体的值。
- （其实代码中贼多错，基本只能运行input里面的指令片段，但一次改四个文件真的改不动。。。就这样吧。。

# 文件夹内容
## Dual
Dual文件夹中为不支持推测的双发射处理器，input.txt中为需要执行的指令片段，output.txt为输出的结果。执行preDualIssueProcessor.py文件即可重新输出结果，运行需要安装prettytable宏包以便于输出表格信息。

## Dual_spec
Dual_spec（Dual-Issue supporting speculate）文件夹中为支持推测的双发射处理器，input.txt中为需要执行的指令片段，output.txt为输出的结果。执行preDualIssueProcessor.py文件即可重新输出结果，运行需要安装prettytable宏包以便于输出表格信息。

## Single
文件夹中为不支持推测的单发射处理器，input.txt中为需要执行的指令片段，output.txt为输出的结果。执行SingleIssueProcessor.py文件即可重新输出结果，运行需要安装prettytable宏包以便于输出表格信息。


## Single_spec
文件夹中为支持推测的单发射处理器，input.txt中为需要执行的指令片段，output.txt为输出的结果。执行SingleIssueProcessorSpeculative.py文件即可重新输出结果，运行需要安装prettytable宏包以便于输出表格信息。