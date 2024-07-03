#  coding=utf-8
import json
import os
import logging
import requests
from requests.exceptions import Timeout
from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstanceMonitorDataRequest import DescribeInstanceMonitorDataRequest
from aliyunsdkecs.request.v20140526.DescribeSecurityGroupAttributeRequest import DescribeSecurityGroupAttributeRequest
from aliyunsdkecs.request.v20140526.ModifySecurityGroupRuleRequest import ModifySecurityGroupRuleRequest
from aliyunsdkecs.request.v20140526.AuthorizeSecurityGroupRequest import AuthorizeSecurityGroupRequest
from aliyunsdkecs.request.v20140526.RevokeSecurityGroupRequest import RevokeSecurityGroupRequest

#20240624 修改屏幕日志输出模式
from ConsoleLog import LOGGER_CONSOLE as logger
#from ConsoleLog import LOGGER as logger

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data

def write_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

#读取端口json
def read_json_from_port(url):
    try:
        req = requests.get(url, timeout = 3)
        req.raise_for_status()
        return req.text
    except Timeout:
        return "TO"

def self_ip():
    try:
        req = requests.get("https://ifconfig.me/ip", timeout = 3)
        req.raise_for_status()
        return req.text
    except Timeout:
        return "Time Out"

def find_element(flist, keyword):
    try:
        flist.index(keyword)
        return True
    except ValueError:
        return False

double_zero = False

def check_inp(st, ed):
    global double_zero
    inp = input("请输入(" + str(st) + "-" + str(ed) + "): ")
    while 1:
        if double_zero == True:
            double_zero = False
            break
        if inp.isdigit() == True:
            num = int(inp)
            if num >= st and num <= ed:
                break
        logger.info("注意输入格式！")
        inp = input("请输入(" + str(st) + "-" + str(ed) + "): ")
    return inp

config_info = read_json_file('config.json')
clt = client.AcsClient(config_info.get('RAMuser').get('AccessKeyId'), config_info.get('RAMuser').get('AccessKeySecret'), config_info.get('RAMuser').get('RegionId'))

Sub_Instance = config_info.get('Subscribe').get('InstanceId')
Sub_Name = config_info.get('Subscribe').get('Name')
Ip_Protocol = ['TCP', 'UDP', 'ICMP', 'ICMPv6', 'GRE', 'ALL']

# output the instance owned in current region.
def list_instances():
    logger.info("请问要查询全部实例还是仅查询订阅实例：")
    logger.info("1: 查询全部实例")
    logger.info("2: 查询订阅实例")
    logger.info("0: 回到首页")
    inp = check_inp(0, 2)
    request = DescribeInstancesRequest()
    request.set_accept_format('json')
    response = _send_request(request)
    if response is not None:
        instance_list = response.get('Instances').get('Instance')
        #print(instance_list)
        if inp == '1':
            logger.info("当前地区有以下 %s 个实例：", len(instance_list))
        elif inp == '2':
            logger.info("您订阅了以下 %s 个实例：", len(Sub_Instance))
        elif inp == '0':
            return
        num = 0
        for x in range(0, len(instance_list)):
            if inp == '2':
                if find_element(Sub_Instance, instance_list[x].get('InstanceId')) == False:
                    continue
                num += 1
            elif inp == '1':
                num = x+1
            _print_instance(instance_list, x, num)
            

def list_cpu_memory_disk(url):
    #print(read_json_from_port(url))
    req = read_json_from_port(url)
    if req == "TO":
        logger.info("连接不上服务器的监测器！")
        return
    read_data = json.loads(req)
    cpu_list = read_data.get('CPU')
    disk_list = read_data.get('Disk')
    memory_list = read_data.get('Memory')
    logger.info("CPU使用率：%s", cpu_list)
    for disk_status in disk_list:
        logger.info(disk_status)
    logger.info("内存使用情况：%s", memory_list)

# output the security groups info owned in current region
def list_security_groups():
    request = DescribeInstancesRequest()
    request.set_accept_format('json')
    response = _send_request(request)
    if response is not None:
        instance_list = response.get('Instances').get('Instance')
        logger.info("请选择一个实例来查询安全组信息：")
        for x in range(0, len(instance_list)):
            logger.info("%s: %s %s", x+1, instance_list[x].get('InstanceId'), instance_list[x].get('InstanceName'))
        logger.info("0: 回到首页")
        inp = check_inp(0, len(instance_list))
        if inp == '0':
            return
        else:
            new_request = DescribeSecurityGroupAttributeRequest()
            new_request.set_accept_format('json')
            new_request.set_SecurityGroupId(instance_list[int(inp)-1].get('SecurityGroupIds').get('SecurityGroupId')[0])
            new_response = _send_request(new_request)
            if new_response is not None:
                inp1 = 'a'
                while inp1 != '0':
                    logger.info("安全组名称：%s", new_response.get('SecurityGroupName'))
                    group_list = new_response.get('Permissions').get('Permission')
                    logger.info("可以选择以下指令：")
                    logger.info("1: 查询所有安全组入规则")
                    logger.info("2: 修改安全组入规则")
                    logger.info("3: 添加安全组入规则")
                    logger.info("4: 删除安全组入规则")
                    logger.info("0: 回到首页")
                    inp1 = check_inp(0, 4)
                    if inp1 == '1':
                        logger.info("该安全组有 %s 条规则：", len(group_list))
                        for x in range(0, len(group_list)):
                            _print_rule(group_list[x], x+1)
                    elif inp1 == '2':
                        #modify security group rule
                        logger.info("请选择一个安全组规则或回到首页(0)")
                        inp2 = check_inp(0, len(group_list))
                        if inp2 == '0':
                            return
                        logger.info("您选择了这个规则：")
                        srule = group_list[int(inp2)-1]
                        _print_rule(srule, int(inp2))
                        modify_policy = srule.get('Policy')
                        modify_priority = srule.get('Priority')
                        modify_protocol = srule.get('IpProtocol')
                        modify_range = srule.get('PortRange')
                        modify_cidr = srule.get('SourceCidrIp')
                        modify_description = srule.get('Description')
                        _print_modify()
                        global double_zero
                        double_zero = True
                        inp3 = check_inp(0, 6)
                        while inp3 != '0':
                            if inp3 == '1':
                                logger.info("请选择访问权限：")
                                logger.info("1: 允许")
                                logger.info("2: 拒绝")
                                inp4 = check_inp(1, 2)
                                if inp4 == '1':
                                    modify_policy = 'Accept'
                                elif inp4 == '2':
                                    modify_policy = 'Drop'
                            elif inp3 == '2':
                                logger.info("优先级格式：数字1-100")
                                inp4 = check_inp(1, 100)
                                modify_priority = inp4
                            elif inp3 == '3':
                                logger.info("请选择协议类型：")
                                for x in range(0, 6):
                                    logger.info("%s: %s", x+1, Ip_Protocol[x])
                                logger.info("！请输入协议类型前编号")
                                inp4 = check_inp(1, 6)
                                modify_protocol = Ip_Protocol[int(inp4)-1]
                            elif inp3 == '4':
                                logger.info("TCP/UDP端口范围格式：起始端口/终止端口")
                                logger.info("ICMP/GRE/ALL端口范围：-1/-1")
                                inp4 = input("请按照格式输入端口范围：")
                                modify_range = inp4
                            elif inp3 == '5':
                                logger.info("源端IPv4 CIDR地址段格式：IP/端口")
                                logger.info("所有IPv4：0.0.0.0/0")
                                logger.info("您的网络IP：%s", self_ip())
                                inp4 = input("请按照格式输入IPv4 CIDR地址段：")
                                modify_cidr = inp4
                            elif inp3 == '6':
                                inp4 = input("请输入描述：")
                                modify_description = inp4
                            elif inp3 == '00':
                                logger.info("请确认更改后的安全组规则：")
                                logger.info("-------------------%s------------------", int(inp2))
                                logger.info("方向：%s", srule.get('Direction'))
                                logger.info("访问权限：%s", modify_policy)
                                logger.info("规则优先级：%s", modify_priority)
                                logger.info("协议类型：%s", modify_protocol)
                                logger.info("端口范围：%s", modify_range)
                                logger.info("源端IPv4 CIDR地址段：%s", modify_cidr)
                                logger.info("规则描述：%s", modify_description)
                                logger.info("网卡类型：%s", srule.get('NicType'))
                                logger.info("创建时间：%s", srule.get('CreateTime'))
                                logger.info("-------------------%s------------------", int(inp2))
                                logger.info("！是否确认当前修改内容（1:是/0:否）")
                                inp4 = check_inp(0, 1)
                                if inp4 == '1':
                                    rule_request = ModifySecurityGroupRuleRequest()
                                    rule_request.set_SecurityGroupId(new_response.get('SecurityGroupId'))
                                    rule_request.set_SecurityGroupRuleId(srule.get('SecurityGroupRuleId'))
                                    rule_request.set_Policy(modify_policy)
                                    rule_request.set_Priority(modify_priority)
                                    rule_request.set_IpProtocol(modify_protocol)
                                    rule_request.set_PortRange(modify_range)
                                    rule_request.set_SourceCidrIp(modify_cidr)
                                    rule_request.set_Description(modify_description)
                                    _send_request(rule_request)
                                    logger.info("修改完成！")
                            _print_modify()
                            inp3 = check_inp(0, 6)
                    elif inp1 == '3':
                        # add security group rule
                        add_policy = 'Accept'
                        add_priority = '1'
                        add_protocol = 'TCP'
                        add_range = '1/1'
                        add_cidr = '0.0.0.0/0'
                        add_description = 'This is a description'
                        logger.info("准备添加规则，您需要依次输入访问权限、优先级、协议类型、端口范围、源端IPv4 CIDR地址段、描述")
                        logger.info("请选择访问权限：")
                        logger.info("1: 允许")
                        logger.info("2: 拒绝")
                        inp4 = check_inp(1, 2)
                        if inp4 == '1':
                            add_policy = 'Accept'
                        elif inp4 == '2':
                            add_policy = 'Drop'
                        logger.info("优先级格式：数字1-100")
                        inp4 = check_inp(1, 100)
                        add_priority = inp4
                        logger.info("请选择协议类型：")
                        for x in range(0, 6):
                            logger.info("%s: %s", x+1, Ip_Protocol[x])
                        logger.info("！请输入协议类型前编号")
                        inp4 = check_inp(1, 6)
                        add_protocol = Ip_Protocol[int(inp4)-1]
                        logger.info("TCP/UDP端口范围格式：起始端口/终止端口")
                        logger.info("ICMP/GRE/ALL端口范围：-1/-1")
                        inp4 = input("请按照格式输入端口范围：")
                        add_range = inp4
                        logger.info("源端IPv4 CIDR地址段格式：IP/端口")
                        logger.info("所有IPv4：0.0.0.0/0")
                        logger.info("您的网络IP：%s", self_ip())
                        inp4 = input("请按照格式输入IPv4 CIDR地址段：")
                        add_cidr = inp4
                        inp4 = input("请输入描述：")
                        add_description = inp4
                        logger.info("请确认更改后的安全组规则：")
                        logger.info("-------------------------------------")
                        logger.info("方向：ingress")
                        logger.info("访问权限：%s", add_policy)
                        logger.info("规则优先级：%s", add_priority)
                        logger.info("协议类型：%s", add_protocol)
                        logger.info("端口范围：%s", add_range)
                        logger.info("源端IPv4 CIDR地址段：%s", add_cidr)
                        logger.info("规则描述：%s", add_description)
                        logger.info("-------------------------------------")
                        logger.info("！是否确认当前修改内容（1:是/0:否）")
                        inp4 = check_inp(0, 1)
                        if inp4 == '1':
                            rule_request = AuthorizeSecurityGroupRequest()
                            rule_request.set_SecurityGroupId(new_response.get('SecurityGroupId'))
                            rule_request.set_Policy(add_policy)
                            rule_request.set_Priority(add_priority)
                            rule_request.set_IpProtocol(add_protocol)
                            rule_request.set_PortRange(add_range)
                            rule_request.set_SourceCidrIp(add_cidr)
                            rule_request.set_Description(add_description)
                            _send_request(rule_request)
                            logger.info("添加完成！")
                    elif inp1 == '4':
                        # delete security group rule
                        logger.info("请选择一个安全组规则或回到首页(0)")
                        inp2 = check_inp(0, len(group_list))
                        if inp2 == '0':
                            return
                        logger.info("您选择了这个规则：")
                        srule = group_list[int(inp2)-1]
                        _print_rule(srule, int(inp2))
                        logger.info("！是否确认删除当前安全组规则（1:是/0:否）")
                        inp4 = check_inp(0, 1)
                        if inp4 == '1':
                            rule_request = RevokeSecurityGroupRequest()
                            rule_request.set_SecurityGroupId(new_response.get('SecurityGroupId'))
                            rule_request.set_SecurityGroupRuleIds([group_list[int(inp2)-1].get('SecurityGroupRuleId')])
                            _send_request(rule_request)
                            logger.info("删除完成！")

def manage_subscribe():
    inp = 'a'
    while inp != '0':
        _print_subscribe()
        inp = check_inp(0, 2)
        if inp == '1':
            request = DescribeInstancesRequest()
            request.set_accept_format('json')
            response = _send_request(request)
            if response is not None:
                instance_list = response.get('Instances').get('Instance')
                logger.info("当前地区有以下 %s 个实例：", len(instance_list))
                for x in range(0, len(instance_list)):
                    if find_element(Sub_Instance, instance_list[x].get('InstanceId')):
                        logger.info("*%s: %s %s", x+1, instance_list[x].get('InstanceId'), instance_list[x].get('InstanceName'))
                    else:
                        logger.info("%s: %s %s", x+1, instance_list[x].get('InstanceId'), instance_list[x].get('InstanceName'))
                logger.info("标 * 号表示已订阅")
                logger.info("请输入要订阅的实例编号或返回上一级(0)")
                inp1 = check_inp(0, len(instance_list))
                if inp1 == '0':
                    continue
                need_sub_id = instance_list[int(inp1)-1].get('InstanceId')
                need_sub_name = instance_list[int(inp1)-1].get('InstanceName')
                if find_element(Sub_Instance, need_sub_id):
                    logger.info("！请勿重复订阅！")
                else:
                    Sub_Instance.append(need_sub_id)
                    Sub_Name.append(need_sub_name)
                    logger.info("！订阅成功！")
        if inp == '2':
            logger.info("请选择一个实例编号来取消订阅或返回上一级(0)")
            inp1 = check_inp(0, len(Sub_Instance))
            if inp1 == '0':
                continue
            Sub_Instance.pop(int(inp1)-1)
            Sub_Name.pop(int(inp1)-1)
            logger.info("！取消订阅成功！")
    
    config_info['Subscribe']['InstanceId'] = Sub_Instance
    write_json_file('config.json', config_info)
    logger.info("保存订阅信息成功！")

def _print_instance(instance_list, x, num):
    logger.info("-------------------%s------------------", num)
    logger.info("实例ID：%s", instance_list[x].get('InstanceId'))
    logger.info("实例名称：%s", instance_list[x].get('InstanceName'))
    logger.info("实例状态：%s", instance_list[x].get('Status'))
    logger.info("实例描述：%s", instance_list[x].get('Description'))
    logger.info("实例网络类型：%s", instance_list[x].get('InstanceNetworkType'))
    logger.info("实例公网IP：%s", instance_list[x].get('PublicIpAddress').get('IpAddress')[0])
    logger.info("实例私网IP：%s", instance_list[x].get('VpcAttributes').get('PrivateIpAddress').get('IpAddress')[0])
    logger.info("实例所在安全组：%s", instance_list[x].get('SecurityGroupIds').get('SecurityGroupId')[0])
    url = 'http://' + instance_list[x].get('PublicIpAddress').get('IpAddress')[0] + ':' + config_info.get('MonitorPort') + '/'
    list_cpu_memory_disk(url)
    logger.info("-------------------%s------------------", num)

def _print_rule(security_rule, num):
    logger.info("-------------------%s------------------", num)
    logger.info("方向：%s", security_rule.get('Direction'))
    logger.info("访问权限：%s", security_rule.get('Policy'))
    logger.info("规则优先级：%s", security_rule.get('Priority'))
    logger.info("协议类型：%s", security_rule.get('IpProtocol'))
    logger.info("端口范围：%s", security_rule.get('PortRange'))
    logger.info("源端IPv4 CIDR地址段：%s", security_rule.get('SourceCidrIp'))
    logger.info("规则描述：%s", security_rule.get('Description'))
    logger.info("网卡类型：%s", security_rule.get('NicType'))
    logger.info("创建时间：%s", security_rule.get('CreateTime'))
    logger.info("-------------------%s------------------", num)

def _print_modify():
    logger.info("请选择一个内容修改：")
    logger.info("1: 访问权限")
    logger.info("2: 优先级")
    logger.info("3: 协议类型")
    logger.info("4: 端口范围")
    logger.info("5: 源端IPv4 CIDR地址段")
    logger.info("6: 描述")
    logger.info("00: 保存修改！！！")
    logger.info("0: 取消/返回上一级")

def _print_commands():
    logger.info("有以下命令：\n")
    logger.info("1: 查询实例运行状态")
    logger.info("2: 查询和修改/添加/删除实例安全组规则")
    logger.info("3: 管理订阅")
    logger.info("0: 退出程序")

def _print_subscribe():
    logger.info("您订阅了以下 %s 个实例：", len(Sub_Instance))
    for x in range(0, len(Sub_Instance)):
        logger.info("%s: %s %s", x+1, Sub_Instance[x], Sub_Name[x])
    logger.info("请选择操作：")
    logger.info("1: 订阅实例")
    logger.info("2: 取消订阅实例")
    logger.info("0: 退出并保存订阅信息")

# send open api request
def _send_request(request):
    request.set_accept_format('json')
    try:
        response_str = clt.do_action_with_exception(request)
        response_detail = json.loads(response_str)
        return response_detail
    except Exception as e:
        logger.error("ERROR: ", e)

if __name__ == '__main__':
    logger.info("欢迎来到阿里云ECS管理系统！")
    logger.info("Made by Skyzhou\n")
    logger.info("使用之前请务必填写和检查config.json！")
    _print_commands()
    inp = check_inp(0, 3)
    while inp != '0':
        #logger.info("JUST INPUT %s", inp)
        if inp == '1':
            list_instances()
        elif inp == '2':
            list_security_groups()
        elif inp == '3':
            manage_subscribe()
        print('\n')
        _print_commands()
        inp = check_inp(0, 3)
    logger.info("GOODBYE!")