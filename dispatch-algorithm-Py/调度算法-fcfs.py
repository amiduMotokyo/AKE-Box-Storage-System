#1. 先到先服务（FCFS）
#需要的库
import time,csv,os
import pandas as pd
import subprocess

airline_companies = {1:'东方航空', 2:'中国国际航空', 3:'南方航空', 4:'国泰航空'}
key_words={'ID':'ID','航司':'airlines','位置':'site'}
keywords=['ID','航司','位置']

class aek_box(object):
    #货箱入库
    def __init__(self,box_id,airlines,weight,time_entry,site):#初始化box的类对象，类属性依次为ID、航司、重量、入场时间、算法计算得出来的位置
        self.ID = box_id
        self.airlines = airlines
        self.time_entry =time_entry
        self.weight = weight
        self.site = site
        # all_aek_boxes.append(self)
        with open('data.csv',mode='a',encoding='utf-8',newline='') as f:
            new=csv.writer(f)
            new.writerow([self.ID,self.airlines,self.time_entry,self.weight,self.site])
        print('AEK箱入库成功！')
#调度算法
# def fcfs(processes):
#     """
#     先到先服务调度算法
#     :param processes: 进程列表，每个进程包含到达时间和执行时间
#     """
#     n = len(processes)#进程的总数量
#     wait_times = [0] * n#初始化等待时间列表
#     turnaround_times = [0] * n#初始化周转时间列表
#     total_wait_time = 0#总等待时间
#     total_turnaround_time = 0#总周转时间
#
#     current_time = 0
#     for i in range(n):#按照进程到达的顺序遍历进程列表
#         process = processes[i]
#         # 如果当前时间小于进程的到达时间，则更新当前时间为进程的到达时间。进程的等待时间等于当前时间减去进程的到达时间
#         if current_time < process['arrival_time']:
#             current_time = process['arrival_time']
#         #计算进程的等待时间
#         wait_times[i] = current_time - process['arrival_time']
#         #进程的周转时间等于等待时间加上执行时间
#         turnaround_times[i] = wait_times[i] + process['burst_time']
#         # 当前时间加上进程的执行时间
#         current_time += process['burst_time']
#         #计算总的等待时间
#         total_wait_time += wait_times[i]
#         #计算总的周转时间
#         total_turnaround_time += turnaround_times[i]
#     #计算平均等待时间&平均周转时间
#     avg_wait_time = total_wait_time / n
#     avg_turnaround_time = total_turnaround_time / n
#     #返回上述两个值给主函数
#     return avg_wait_time, avg_turnaround_time
#

#The info management of the AEK_boxes
def menu():
    print('*'*30)
    print('''欢迎使用【AEK货箱管理系统】
    1.货箱入库
    2.显示库中货箱
    3.查询库中货箱
    0.退出系统''')
    print('*'*30)


def query_box(property,key):
    result=[]#空集合，用于返回多个查找结果
    with open('data.csv', mode='r', encoding='utf-8') as f:
            find_box = csv.reader(f)
            for i in find_box:
                temp_find = list(i)
                if property == 'ID' and temp_find[0] == key:
                    result.append(temp_find)
                if property == 'airlines' and temp_find[1] == key:
                    result.append(temp_find)
                if property == 'site' and temp_find[4] == key:
                    result.append(temp_find)
    return result

import csv

def delete_row_from_csv(csv_file, row_index):
    with open(csv_file, 'r', encoding='utf-8',newline='') as file:
        reader = csv.reader(file)
        rows = list(reader)  # 将所有行读取到列表中

    if 0 <= row_index < len(rows):  # 检查索引是否有效
        del rows[row_index]  # 删除指定行

        with open(csv_file, 'w', encoding='utf-8',newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)  # 将修改后的数据写回 CSV 文件
    else:
        print(f"行索引 {row_index} 超出范围。")

def quit():
    print('程序已退出！')

automatic_identification=False

def show_box():
    #这里还必须显示它所处的位置——x、y、z——行数、列数、层数
    if os.path.getsize('data.csv')==0 :
        print('当前货场中未存放任何货箱！')
    else :
        number = 1
        with open('data.csv',mode='r',encoding='utf-8') as f:
            read_box=csv.reader(f)
            for box in read_box:
                temp = list(box)
                print('%d号AEK货箱，ID：%s,所属航司：%s,入场时间：%s,货箱重量：%s,位置：%s' % (number, temp[0], temp[1], temp[2], temp[3], temp[4]))
                number += 1

while True :
    # step 1.先判断货物是否能够被扫描设备录入信息
    #这块需要一个返回值来判断是否自动录入是有效的
    # automatic_identification=f()
    if automatic_identification:
    # step 1.1   如果可以通过扫描仪直接录入信息

        pass  # 还没写

    # step 1.2   只能靠人工手动输入信息
    else:
        menu()
        #判断操作序号是否合法
        while True :
            flag=True
            op = input('请输入操作的序号：')
            if op not in ('1','2','3','0'):
                print('输入的操作序号不合法，请重新输入！')
            else :
                flag=False
            if not flag :
                break
        if op == '1':
            while True:
                temp = True#用于判断有重复ID情况的时候，是否要退出程序
                box_ID = input('请输入货箱的ID：')
                with open('data.csv', mode='r', encoding='utf-8') as f:
                    id_box = csv.reader(f)
                    rows=list(id_box)
                    for j in rows:
                        if box_ID == j[0] :
                            print('出错了！此ID对应的货物已经存在！')
                            instru=input('是否要退出程序？ 请输入Yes or no:')
                            if instru=='Yes':
                                break#退出程序
                            else:
                                temp=False#继续输入ID
                                break
                if temp :
                    break
            while True:
                temp_2=True
                print('请输入货箱隶属的航司的相应序号：')
                print(airline_companies)
                number = int(input())  # 举例现在就只有这四家航司
                if number <= len(airline_companies) and number >= 0 :
                    box_airlines=airline_companies[number]
                    temp_2=False
                else:
                    print('序号不合法，请重新输入！')
                if not temp_2:
                    break
            box_weight = input('请输入货箱的重量：')#这里还没有设置货物的最高限重与最低限重
            box_time_entry = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())


            #位置计算待完成
            box_site='null_site'



            aek_box(box_ID,box_airlines,box_weight,box_time_entry,box_site)#实例化box的类对象，类属性依次为ID、航司、重量、入场时间、算法计算得出来的位置
        elif op=='2':#显示库中货箱-必须先判断有没有货！
            show_box()
        elif op=='3':#查询库中货箱
            while True :
                temp_3=True
                print(keywords)
                kw = input('请输入查询的属性：')#现在只限制能查一个关键字
                for k,v in key_words.items() :
                    if kw == k:
                        temp_3 = False
                        key=input('请输入要查询的属性值：')
                        result_queue=query_box(key_words[kw],key)
                        break
                if not temp_3:
                    break
                else :
                    print('关键字不合法，请重新输入！')
            # #如果关键值对应多个货箱呢？？？用列表进行输出
            if len(result_queue)>0 :
                num=1
                for i in result_queue:
                    print('%d号货箱：ID：%s,所属航司：%s,入场时间：%s,货箱重量：%s,位置：%s' % (num,i[0],i[1],i[2],i[3],i[4]))
                    num += 1
                op2 = input('输入4修改货箱的信息，输入5删除货箱的信息，输入6退出：')
                if op2 == '4':#修改信息支持多关键字修改
                    while True :
                        temp_4=True
                        info_box_id=input('请输入要修改货箱ID：')
                        for find_id in result_queue:
                            if info_box_id == find_id[0]:
                                temp_4 = False
                                while True :#进行查询结果的编号合法性检验
                                    temp_4_1=True
                                    print(keywords)  # 显示全部可以修改的属性
                                    target=input('请输入要修改货箱的属性')
                                    if target in keywords:
                                        info = input('请输入修改的内容：')
                                        with open('data.csv', mode='r', encoding='utf-8') as f:
                                            find_box = csv.reader(f)
                                            rows_2 = list(find_box)
                                            if target == 'ID':
                                                for row in rows_2:
                                                    if row[0]==info_box_id :
                                                        row[0]=info
                                            elif target == '航司':
                                                for row in rows_2:
                                                    if row[0]==info_box_id :
                                                            row[1]=info
                                            elif target == '位置':
                                                for row in rows_2:
                                                    if row[0]==info_box_id :
                                                        row[4]=info
                                        with open('data.csv', 'w', encoding='utf-8',newline='') as file:
                                            writer = csv.writer(file)
                                            writer.writerows(rows_2)  # 将修改后的数据写回 CSV 文件
                                        temp_4_1=False
                                    else :
                                        print('属性不存在，请重新输入！')
                                    if not temp_4_1 :
                                        decision=input('是否继续修改？继续请只输入Yes')
                                        if decision=='Yes':
                                            info_box_id=input('请输入要修改信息的货箱ID：')#这里没有合法性检查
                                        else:
                                            break
                                break
                        if not temp_4:
                            break
                        else:
                            print('ID不存在，请重新输入！')
                elif op2 == '5':
                    while True:
                        temp_5 = True
                        info_box_id = input('请输入要删除的货箱ID：')
                        for find_id in result_queue:
                            if info_box_id == find_id[0]:
                                temp_5 = False
                                with open('data.csv', mode='r', encoding='utf-8') as f:
                                    find_box = csv.reader(f)
                                    rows_2 = list(find_box)
                                    row_num=0
                                    for row in rows_2:
                                        if row[0]==info_box_id :
                                            delete_row_from_csv('data.csv', row_num)
                                        row_num+=1
                                break
                        if not temp_5:
                            break
                        else:
                            print('ID不存在，请重新输入！')
                elif op2 == '6':
                    pass
                else:
                    print('指令错误，将回退到主页面！')
            else :
                print('未找到任何相符合的结果！')
        elif op=='0':
            quit()
            break
