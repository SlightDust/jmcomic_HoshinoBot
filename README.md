# 不建议在QQ群使用本插件


## jmcomic_HoshinoBot

下载并加密指定jmid的漫画并上传到群文件。基于[hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)，适用于[HoshinoBot](https://github.com/Ice9Coffee/HoshinoBot)。  
需要Python3.9+

## 安装方法
1. 在module目录下克隆本仓库 `git clone https://github.com/SlightDust/jmcomic_HoshinoBot.git`
2. 下载依赖 `pip install jmcomic PyPDF2 img2pdf`
3. 复制`jm_config_example.yml`到`jm_config.yml`
4. 在`__bot__.py`的`module`中添加`jmcomic_HoshinoBot`
5. 在群内发送`enable jmcomic`以启用本插件

## 遗留问题
- 下载的文件会全部积攒在硬盘中，没有做自动清理。  

## 更新日志
2025.05.06 可用

## 碎碎念
随便写写，可能不会长期维护。  
**搞这个的bot，不会长久的。**  
也可以看看[Fatfish588/jmid2name-hoshino](https://github.com/Fatfish588/jmid2name-hoshino)，这个是jmid转漫画名字的。  

`jm_config.yml`的第4行是下载的全部图片文件的路径，35行是输出未加密pdf的路径，如果是windows用的话要改成windows的路径格式。这个配置文件的其他设置可以参考[jmcomic配置文件指南](https://jmcomic.readthedocs.io/zh-cn/latest/option_file_syntax/#)。  
`jmcomic_HoshinoBot.py`的14行也是。  
  
默认情况下，仅允许SUPERUSER权限的用户开启本插件，可以按需求该manage_priv。  
  
默认情况下，文件密码是jmid的倒序，可以改`_enctypt_pdf`函数的password传参设置别的密码。  
  
`llob_cross_host_download_file`这个我只试了LLOneBot。根据[NapCat文档](https://napneko.github.io/onebot/napcat#napcat-%E8%B5%84%E6%BA%90-url-%E5%8F%82%E6%95%B0%E7%B1%BB%E5%9E%8B)，这么写对于NapCat似乎不太适用。有人用的话试一下吧(x)  
    
<br>

![](https://s2.loli.net/2025/05/07/3tic9aP45MJAqGw.png)
