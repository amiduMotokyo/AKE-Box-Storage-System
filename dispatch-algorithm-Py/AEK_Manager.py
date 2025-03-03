#1. 先到先服务（FCFS）
#需要的库
import time,csv,os
import pandas as pd
import subprocess
import numpy as np
import wx

file_name='data.csv'
airline_companies = {1:'东方航空', 2:'中国国际航空', 3:'南方航空', 4:'上海航空',5:'春秋航空',6:'吉祥航空',7:'深圳航空',8:'中华航空',9:'全日空航空'}
key_words={'ID':'ID','航司':'airlines','位置':'site'}
keywords=['ID','航司','位置']
Shelf_total={}#用于存储所有航空公司的相对应的货架
tag_row_of_airlines_in_shelf=0#记录存放货架的列编号
is_thought={}#用于记录航空公司的货架是否已经被建立了

#目前还未编写的功能：1、自动调整货架中货箱按重量规律放置的功能    2、调度    3、航司名录在增加新条目之后退出程序不能存档



class Shelf:
    def __init__(self):
        """初始化一个 6×30×6 的货架，所有位置状态设为 0（空）。"""
        self.shelf = np.zeros((6, 1, 6), dtype=int)

    def is_valid_position(self, x,y,z):
        """检查坐标 (x, y, z) 是否有效。"""
        return 0 <= x < 6 and 0 <= y < 1 and 0 <= z < 6

    def is_empty(self, x, y, z):
        """检查位置 (x, y, z) 是否为空。"""
        if not self.is_valid_position(x, y, z):
            raise ValueError("无效的位置坐标")
        return self.shelf[x, y, z] == 0

    def is_full(self, x, y, z):
        """检查位置 (x, y, z) 是否为满。"""
        if not self.is_valid_position(x, y, z):
            raise ValueError("无效的位置坐标")
        return self.shelf[x, y, z] == 1

    def store_item(self, x,y,z):
        """在指定位置 (x, y, z) 入库货物。"""
        if not self.is_valid_position(x, y, z):
            raise ValueError("无效的位置坐标")
        if self.is_full(x, y, z):
            raise ValueError("该位置已有货物")
        self.shelf[x, y, z] = 1

    def remove_item(self, x,y,z):
        """从指定位置 (x, y, z) 出库货物。"""
        if not self.is_valid_position(x, y, z):
            raise ValueError("无效的位置坐标")
        if self.is_empty(x,y,z):
            raise ValueError("该位置没有货物")
        self.shelf[x, y, z] = 0


    def move_item(self, x,y,z):
        """从指定位置 (x, y, z) 出库货物。"""
        if not self.is_valid_position(x, y, z):
            raise ValueError("无效的位置坐标")
        if self.is_full(x,y,z):
            raise ValueError("该位置已经有货物")
        self.shelf[x, y, z] = 1
        return True

    def find_next_available(self):
        """找到下一个适合存放货物的空位，返回坐标 (x, y, z) 或 None（货架已满）。"""
        for z in range(6):
            for x in range(6):
                if self.shelf[x, 0, z] == 0:
                    return x,0,z

    def auto_store(self):
        """自动找到空位并存放货物，返回存放位置。"""
        pos = self.find_next_available()
        if pos is None:
            raise ValueError("货架已满")
        self.store_item(*pos)
        return pos



class aek_box(object):
    #货箱入库
    def __init__(self,box_id,airlines,weight,time_entry,site):#初始化box的类对象，类属性依次为ID、航司、重量、入场时间、算法计算得出来的位置
        self.ID = box_id
        self.airlines = airlines
        self.time_entry =time_entry
        self.weight = weight
        self.site = site
        # all_aek_boxes.append(self)
        with open(file_name,mode='a',encoding='utf-8',newline='') as f:
            new=csv.writer(f)
            new.writerow([self.ID,self.airlines,self.time_entry,self.weight,self.site])
        print('AEK箱入库成功！')
#调度算法
def fcfs(processes):
    """
    先到先服务调度算法
    :param processes: 进程列表，每个进程包含到达时间和执行时间
    """
    n = len(processes)#进程的总数量
    wait_times = [0] * n#初始化等待时间列表
    turnaround_times = [0] * n#初始化周转时间列表
    total_wait_time = 0#总等待时间
    total_turnaround_time = 0#总周转时间

    current_time = 0
    for i in range(n):#按照进程到达的顺序遍历进程列表
        process = processes[i]
        # 如果当前时间小于进程的到达时间，则更新当前时间为进程的到达时间。进程的等待时间等于当前时间减去进程的到达时间
        if current_time < process['arrival_time']:
            current_time = process['arrival_time']
        #计算进程的等待时间
        wait_times[i] = current_time - process['arrival_time']
        #进程的周转时间等于等待时间加上执行时间
        turnaround_times[i] = wait_times[i] + process['burst_time']
        # 当前时间加上进程的执行时间
        current_time += process['burst_time']
        #计算总的等待时间
        total_wait_time += wait_times[i]
        #计算总的周转时间
        total_turnaround_time += turnaround_times[i]
    #计算平均等待时间&平均周转时间
    avg_wait_time = total_wait_time / n
    avg_turnaround_time = total_turnaround_time / n
    #返回上述两个值给主函数
    return avg_wait_time, avg_turnaround_time
#

#The info management of the AEK_boxes
def menu():
    print('*'*30)
    print('''欢迎使用【AEK货箱管理系统】
    1.货箱入库
    2.显示库中货箱
    3.查询库中货箱
    4.新增航空公司
    0.退出系统''')
    print('*'*30)


def query_box(property,key):
    result=[]#空集合，用于返回多个查找结果
    with open(file_name, mode='r', encoding='utf-8') as f:
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
    if os.path.getsize(file_name)==0 :
        print('当前货场中未存放任何货箱！')
    else :
        number = 1
        with open(file_name,mode='r',encoding='utf-8') as f:
            read_box=csv.reader(f)
            for box in read_box:
                temp = list(box)
                print('%d号AEK货箱，ID：%s,所属航司：%s,入场时间：%s,重量：%s,位置：%d行%d列%d层' % (number, temp[0], temp[1], temp[2], temp[3],int(temp[4][1]),is_thought[temp[1]],int(temp[4][7])))
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
            if op not in ('1','2','3','4','0'):
                print('输入的操作序号不合法，请重新输入！')
            else :
                flag=False
            if not flag :
                break
        if op == '1':
            while True:
                temp = True#用于判断有重复ID情况的时候，是否要退出程序
                box_ID = input('请输入货箱的ID：')
                with open(file_name, mode='r', encoding='utf-8') as f:
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
                number = int(input())
                if number <= len(airline_companies) and number >= 0 :
                    box_airlines=airline_companies[number]
                    temp_2=False
                else:
                    print('序号不合法，请重新输入！')
                if not temp_2:
                    break
            box_weight = input('请输入货箱的重量(仅数字)：')+'kg'#这里还没有设置货物的最高限重与最低限重
            box_time_entry = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())

            #预设每家航空公司最开始都是统一拥有一个6*1*6的存放大小（行数为六，列数为一，高度为六），货场总大小为6*30*6
            if airline_companies[number] in is_thought:#这个时候说明这个航空公司对应的货架已经存在了
                cargo=Shelf_total[airline_companies[number]]
                box_site=list(cargo.auto_store())
            else:#对应不存在的情况
                cargo=Shelf()
                box_site=list(cargo.auto_store())
                is_thought[airline_companies[number]]=tag_row_of_airlines_in_shelf
                Shelf_total[airline_companies[number]]=cargo
                tag_row_of_airlines_in_shelf+=1
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
                        key=input('请输入要查询的%s：'%kw)
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
                    print('%d号货箱：ID：%s,所属航司：%s,入场时间：%s,重量：%s,位置：%s行%d列%d层' % (num,i[0],i[1],i[2],i[3],int(i[4][1]),is_thought[i[1]],int(i[4][7])))
                    num += 1
                op2 = input('输入5修改货箱的信息，输入6删除货箱的信息，输入7退出：')
                if op2 == '5':#修改信息支持多关键字修改
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
                                        with open(file_name, mode='r', encoding='utf-8') as f:
                                            find_box = csv.reader(f)
                                            rows_2 = list(find_box)
                                            if target == 'ID':
                                                info = input('请输入修改的内容：')
                                                for row in rows_2:
                                                    if row[0]==info_box_id :
                                                        row[0]=info
                                            elif target == '航司':#如果改航司的话，改了之后的存放位置是改不了的
                                                # for row in rows_2:
                                                #     if row[0]==info_box_id :
                                                #             row[1]=info
                                                print('航司不能被修改！')
                                            elif target == '位置':
                                                temp_7=True
                                                while True :
                                                    for row in rows_2:
                                                        if row[0] == info_box_id:
                                                            x_site_change = input('请输入目的位置的行数:')
                                                            z_site_change = input('请输入目的位置的层数:')
                                                            cargo_shelf = Shelf_total[find_id[1]]
                                                            if cargo_shelf.move_item(int(x_site_change), 0, int(z_site_change)) :
                                                                # print(type(row[4]))
                                                                row[4]=row[4][:1]+x_site_change+row[4][2:7]+z_site_change+row[4][4][8:]
                                                                temp_7=False
                                                                break
                                                    if not temp_7:
                                                        break
                                        with open(file_name, 'w', encoding='utf-8',newline='') as file:
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
                elif op2 == '6':
                    while True:
                        temp_5 = True
                        info_box_id = input('请输入要删除的货箱ID：')
                        for find_id in result_queue:
                            if info_box_id == find_id[0]:
                                temp_5 = False
                                cargo_shelf=Shelf_total[find_id[1]]
                                site_x=int(find_id[4][1])
                                site_z=int(find_id[4][7])
                                cargo_shelf.remove_item(site_x,0,site_z)
                                with open(file_name, mode='r', encoding='utf-8') as f:
                                    find_box = csv.reader(f)
                                    rows_2 = list(find_box)
                                    row_num=0
                                    for row in rows_2:
                                        if row[0]==info_box_id :
                                            delete_row_from_csv(file_name, row_num)
                                        row_num+=1
                                break
                        if not temp_5:
                            break
                        else:
                            print('ID不存在，请重新输入！')
                elif op2 == '7':
                    pass
                else:
                    print('指令错误，将回退到主页面！')
            else :
                print('未找到任何相符合的结果！')
        elif op== '4':
            tag=len(airline_companies)+1
            while True :
                temp_6 = True
                airline_companies_name=input('请输入对应航司的名称:')
                for k,v in airline_companies.items() :
                    if airline_companies_name == v :
                        print('该航司已存在！请重新输入')
                        temp_6 = False
                        break
                if temp_6:
                    airline_companies[tag] = airline_companies_name
                    print('航司添加成功！')
                    break
        elif op=='0':
            quit()
            break
