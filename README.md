# 阿里云ECS服务器管理系统
#### Made by Skyzhou
#### Supported by Rocky
---

***推荐使用python虚拟环境virtualenv**

## 服务器配置监测器
阿里云ECS服务器监测器，用于监测服务器的CPU、内存、磁盘等无法通过阿里云ECS SDK获取的信息，并通过flask框架将信息以json格式返回给客户端

将aliyunECS_data.py放在服务器上，运行后会在本地开放一个端口，客户端可以通过该端口获取服务器信息，默认端口为18923，请确保服务器防火墙以及ECS安全组开放了该端口。

复制```monitor_config_demo.json```文件，将其改名为```monitor_conifg.json```

根据服务器情况填写```monitor_conifg.json```格式如下

```json
{
    "host": "0.0.0.0", //本地IP
    "port": 18923 //本地开放端口，默认为18923，可自行修改，修改后请同时修改客户端配置中的MonitorPort
}
```

并上传到服务器上aliyunECS_data.py同一目录下

确保服务器拥有json, flask和psutil库，检查端口和防火墙情况后，在服务器运行```python aliyunECS_data.py```


## 客户端配置

复制```config_demo.json```文件，将其改名为```conifg.json```

根据用户自己的情况填写```conifg.json```格式如下

```json
{
    "RAMuser": {
        "AccessKeyId": "AAA", //KeyId
        "AccessKeySecret": "BBB", //KeySecret
        "RegionId": "cn-shenzhen" //地区ID
        //以上三项都可以通过阿里云ECS管理控制台获取
    },
    "MonitorPort": "18923", //监视服务器开放的端口，默认为18923，与服务器配置文件中monitor_config的port一致，目前暂不支持不同机器不同端口
    "Subscribe": {
        "InstanceId": [],
        "Name": []
        //订阅信息为程序中自动填写记录，可以不手工修改
    }
}
```

先运行以下命令来安装阿里云ECS的Python SDK:
```
pip install aliyun-python-sdk-ecs
```

确保python环境安装了aliyun-python-sdk-ecs, json, requests, concurrent_log_handler等库，即可运行```python aliyunECS.py```

---

参考文档：

[阿里云ECS服务器API参考](https://help.aliyun.com/zh/ecs/developer-reference/api-reference-ecs/)"# Aliyun_ECS" 
