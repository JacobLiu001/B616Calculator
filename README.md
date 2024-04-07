# B616 Calculator
根据用户手动管理的excel成绩表生成Arcaea ptt 统计分析的程序.

## Contributing
`requirements.txt` 包含了运行所有Python脚本所需要的依赖项.
如果打算向项目贡献代码, 请按照 `pip install -r requirements-dev.txt` 安装开发依赖.
安装完开发依赖以后, 请使用 `pre-commit install` 安装本项目使用的pre-commit hooks.
这样每次commit的时候就会自动运行代码格式化和代码检查.

如果想要使用PyInstaller打包出最小的可执行文件, 请新建一个venv, 并在venv里面打包.

整套项目在mac和win下应当都通用, 有其他系统测试需求可以在群里提或者提Issue.

## Usage Instructions
首次使用:

1. 右键 `history_b30.csv`, 属性, 打开方式改为'记事本' (或其他plain text editor),
2. 运行 `generate_excel.py`. \*需要网络链接, 请耐心等待.
该程序会在当前目录下创建一个叫做 `put_your_score_in_here.xlsx` 的文件,
此 `xlsx` 请用 `MS Excel` 打开, 或者其他表格编辑器如 `numbers` 或者 `wps`, 拓展名请固定为 `.xlsx`.
3. 编辑 `put_your_score_in_here.xlsx`,
在score列输入分数, 无需全都填写, 没打的/不需要参与计算的留空不填就成.
4. 运行 `b616.py`, 第一行输入的数字为参与计算的数据量.
该输入会调整均值计算和图表生成的范围, 不会影响历史b30输入和推分推荐, 如果小于30则不会计算b30.


其他:
1. 如果Arcaea(wiki)有更新, 运行 `generate_excel.py`, 通常能一步到位更新.
运行后请检查 `put_your_score_in_here.xlsx` , 如果出现数据丢失, 结构错误等问题, 请 *不要* 重复运行程序.
更新前的数据放在同目录下的 `scores_here_backup.xlsx` , 请单独存好并在群里@GK说明 `generate_excel` 错误, 或者提issue.

2. 如果不小心记录了错误/不需要的历史b30数据, 可以直接(用记事本)打开 `history_b30.csv` 修改数据.
