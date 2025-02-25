#1. 先到先服务（FCFS）
#需要的库
import time,csv,os
# import numpy as np
# cargo=np.zeros((34,6,6))#货场
all_aek_boxes=[]
#这里需要先定义一个货箱的类（航司、重量、入仓时间、出仓时间、位置[6行、34列、6层]）
# 举例，有下列航司
airline_companies = {1:'东方航空', 2:'中国国际航空', 3:'南方航空', 4:'国泰航空'}
key_words={'ID':'ID','航司':'airlines','位置':'site'}
keywords=['ID','航司','位置']
total=5#表示总存储的箱子数量
class aek_box(object):
    #货箱入库
    def __init__(self,box_id,airlines,weight,time_entry,site):#初始化box的类对象，类属性依次为ID、航司、重量、入场时间、算法计算得出来的位置
        self.ID = box_id
        self.airlines = airlines
        self.time_entry =time_entry
        self.weight = weight
        self.site = site
        # all_aek_boxes.append(self)
        with open('data.csv',mode='a',encoding='utf-8') as f:
            new=csv.writer(f)
            new.writerow([self.ID,self.airlines,self.time_entry,self.weight,self.site])
        print('AEK箱入库成功！')
    #修改aekbox的参数：航司、重量、入仓时间、出仓时间、位置
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

def show_box():
    #这里还必须显示它所处的位置——x、y、z——行数、列数、层数
    if(total==0):
        print('当前货场中未存放任何货箱！')
    else :
        number = 1
        with open('data.csv',mode='r',encoding='utf-8') as f:
            read_box=csv.reader(f)
            for box in read_box:
                if(box==[ ]) :
                    pass
                else :
                    temp=list(box)
                    print('%d号AEK货箱，ID：%s,所属航司：%s,入场时间：%s,货箱重量：%s,位置：%s' % (number, temp[0], temp[1],temp[2],temp[3],temp[4],temp[5]))
                    number += 1
        print('当前共有%d个AEK箱'%total)
def query_box(property,key):
    result=[]#空集合，用于返回多个查找结果
    for i in range(len(all_aek_boxes)):
        if property=='ID' and all_aek_boxes[i].ID==key :
            result.append(all_aek_boxes[i])
        if property=='airlines' and all_aek_boxes[i].airlines==key :
            result.append(all_aek_boxes[i])
        if property=='site' and all_aek_boxes[i].site==key :
            result.append(all_aek_boxes[i])
    return result

def quit():
    print('程序已退出！')

automatic_identification=False
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
                for box in all_aek_boxes:
                    if box_ID == box.ID:
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
            total+=1
        elif op=='2':#显示库中货箱-必须先判断有没有货！
            show_box()
        elif op=='3':#查询库中货箱
            while True :
                temp_3=True
                print(keywords)
                kw = input('请输入查询的关键字的种类：')#现在只限制能查一个关键字
                for k,v in key_words.items() :
                    if kw == k:
                        temp_3 = False
                        key=input('请输入要查询的关键字：')
                        result_queue=query_box(key_words[kw],key)
                        break
                if not temp_3:
                    break
                else :
                    print('关键字不合法，请重新输入！')
            # #如果关键值对应多个货箱呢？？？用列表进行输出
            if len(result_queue)>0 :
                num=1
                for box in result_queue:
                    print('%d号货箱：ID：%s,所属航司：%s,入场时间：%s,货箱重量：%s,位置：%s' % (num,box.ID, box.airlines, box.time_entry, box.weight, box.site))
                    num += 1
                op2 = input('输入4修改货箱的信息，输入5删除货箱的信息：')
                if op2 == '4':#修改信息支持多关键字修改
                    while True :
                        temp_4=True
                        print(keywords)  # 显示全部可以修改的属性
                        info_property=input('请输入要修改的信息关键字：')
                        for k, v in key_words.items():
                            if info_property == k:
                                temp_4 = False
                                while True :#进行查询结果的编号合法性检验
                                    temp_4_1=True
                                    target=int(input('请输入要修改的货箱的编号'))
                                    if target >=1 and target <=len(result_queue) :
                                        info = input('请输入修改的内容：')


                                        #这一块要改回去
                                        if info_property == 'ID' :
                                            result_queue[target-1].ID=info
                                        if info_property == 'airlines':
                                            result_queue[target-1].airlines=info
                                        if info_property == 'site':
                                            result_queue[target-1].site=info
                                        temp_4_1=False




                                    else :
                                        print('编号不合法，请重新输入！')
                                    if not temp_4_1 :
                                        decision=input('是否继续修改？继续请只输入Yes')
                                        if decision=='Yes':
                                            info_property=input('请输入要修改的信息关键字：')#这里没有合法性检查
                                        else:
                                            break
                                break
                        if not temp_4:
                            break
                        else:
                            print('关键字不合法，请重新输入！')
                if op2 == '5':
                    pass#需要在原列表中删除
                else:
                    print('没有查到相关信息')
            else :
                print('未找到任何相符合的结果！')
        elif op=='0':
            quit()
            break
