# B616 Calculator
根据用户手动管理的excel成绩表生成Arcaea ptt 统计分析的程序.

## Contributing
requirements.txt包含了所有.py开发需要的包,
如果想要使用PyInstaller打包出最小的可执行文件, 请新建一个venv, 并在venv里面打包.

整套项目在mac和win下应当都通用, 有其他系统测试需求可以在群里提或者提Issue.

## Usage Instructions
首次使用:
1. 右键 history_b30.csv, 属性, 打开方式改为'记事本'(或其他plain text editor).

2. 运行 GeneratExcel_GK.py *需要网络链接, 请耐心等待.
该程序会在当前目录下创建一个叫做 put_your_score_in_here.xlsx 的文件,
此xlsx请用excel打开, 或者其他表格编辑器如numbers和wps, 拓展名请固定为.xlsx.

3. 用excel编辑 put_your_score_in_here.xlsx,
在score列输入分数, 无需全都填写, 没打的/不需要参与计算的留空不填就成.

4. 运行B616_FV.py, 第一行输入的数字为参与计算的数据量.
该输入会调整均值计算和图表生成的范围, 不会影响历史b30输入和推分推荐, 如果小于30则不会计算b30.


其他:
1. 如果arcaea(wiki)有更新, 运行 GeneratExcel_GK.py, 通常能一步到位更新.
运行后请检查 put_your_score_in_here.xlsx , 如果出现数据丢失, 结构错误等问题, 请[不要]重复运行程序.
更新前的数据放在同目录下的 scores_here_backup.xlsx , 请单独存好并在群里@GK说明GeneratExcel错误.

2. 如果不小心记录了错误/不需要的历史b30数据, 可以直接(用记事本)打开history_b30.csv修改数据.