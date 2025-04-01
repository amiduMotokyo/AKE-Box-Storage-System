import wx
import wx.grid
import sqlite3
import time
import numpy as np
from contextlib import contextmanager
from dataclasses import dataclass

DATABASE_NAME = "cargo.db"
MAX_WEIGHT = 500
AIRLINE_LIST = ["东方航空", "南方航空", "春秋航空", "中国国际航空", "梅塞施密特", "三菱重工", "伏尔提", "霍克・西德利"]
# AIRLINE_LIST = ["东方航空", "南方航空", "春秋航空", "中国国际航空"]


@dataclass
class ShelfConfig:
    rows: int = 6
    columns: int = 1
    layers: int = 6


class DatabaseManager:
    @contextmanager
    def db_connection(self):
        conn = sqlite3.connect(DATABASE_NAME)
        try:
            yield conn
        finally:
            conn.close()

    def initialize_database(self):
        with self.db_connection() as conn:
            cursor = conn.cursor()
            # Create tables
            cursor.execute('''CREATE TABLE IF NOT EXISTS agv (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            position INTEGER NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS cargo (
                            id TEXT PRIMARY KEY,
                            airline TEXT,
                            timestamp TEXT,
                            weight INTEGER,
                            position TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS airlines (
                            name TEXT PRIMARY KEY,
                            row_index INTEGER)''')
            conn.commit()


class Shelf:
    def __init__(self, config=ShelfConfig(), max_weight=MAX_WEIGHT):
        self.config = config
        self.max_weight = max_weight
        self.storage = np.zeros((config.rows, config.columns, config.layers), dtype=int)
    def is_layer_full(self, z):
        """修正层满判断逻辑（原代码只检查了第一列）"""
        return all(self.storage[x, y, z] != 0 
                 for x in range(self.config.rows)
                 for y in range(self.config.columns))  # 增加y轴遍历
    def validate_position(self, x, y, z):
        if not (0 <= x < self.config.rows and
                0 <= y < self.config.columns and
                0 <= z < self.config.layers):
            raise ValueError("Invalid position coordinates")

    def get_position_status(self, x, y, z):
        self.validate_position(x, y, z)
        return self.storage[x, y, z]

    def modify_position(self, x, y, z, value):
        self.validate_position(x, y, z)
        self.storage[x, y, z] = value

    def find_available_position(self):
        """修正列坐标遍历逻辑"""
        for z in range(self.config.layers):
            if not self.is_layer_full(z):
                # 修改点：遍历所有列（原代码固定为0列）
                for y in range(self.config.columns):
                    for x in range(self.config.rows):
                        if self.get_position_status(x, y, z) == 0:
                            return (x, y, z)
        return None


class CargoManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.airline_shelves = {}
        self.airline_row_mapping = {}
        self.max_weight = MAX_WEIGHT
        self.airline_list = AIRLINE_LIST.copy()
        self.load_initial_data()

    def init_database_tables(self):
        """确保数据库表结构存在"""
        with self.db.db_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS airlines (
                            name TEXT PRIMARY KEY, 
                            row_index INTEGER)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS cargo (
                            id TEXT PRIMARY KEY,
                            airline TEXT,
                            timestamp TEXT,
                            weight INTEGER,
                            position TEXT)''')
            conn.commit()

    def load_initial_data(self):
        with self.db.db_connection() as conn:
            # 如果airlines表为空，插入初始数据
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM airlines")
            if cursor.fetchone()[0] == 0:
                for airline in self.airline_list:
                    row_idx = len(self.airline_row_mapping)
                    self.airline_row_mapping[airline] = row_idx
                    self.airline_shelves[airline] = Shelf()
                    conn.execute("INSERT INTO airlines VALUES (?,?)", (airline, row_idx))
                conn.commit()
            else:
                # 已有数据时加载
                cursor.execute("SELECT name, row_index FROM airlines")
                for airline, row_idx in cursor.fetchall():
                    self.airline_row_mapping[airline] = row_idx
                    shelf = Shelf()
                    self.airline_shelves[airline] = shelf
                    
                    # 新增：加载已有货物位置到货架
                    cursor.execute("SELECT position FROM cargo WHERE airline=?", (airline,))
                    for (pos_str,) in cursor.fetchall():
                        x, _, z = map(int, pos_str.split('-'))
                        shelf.modify_position(x, 0, z, 1)  # 标记已占用的位置

    def get_airline_shelf(self, airline):
        if airline not in self.airline_shelves:
            row_idx = len(self.airline_row_mapping)
            self.airline_row_mapping[airline] = row_idx
            self.airline_shelves[airline] = Shelf()
            with self.db.db_connection() as conn:
                conn.execute("INSERT INTO airlines VALUES (?,?)", (airline, row_idx))
        return self.airline_shelves[airline]


class BaseFrame(wx.Frame):
    def __init__(self, parent, title, size=(300, 300)):
        super().__init__(parent, title=title, size=size)
        self.SetBackgroundColour(wx.WHITE)
        self.cargo_mgr = parent.cargo_mgr if parent else CargoManager()

    def show_message(self, message, title, style=wx.OK | wx.ICON_INFORMATION):
        dialog = wx.MessageDialog(self, message, title, style)
        dialog.ShowModal()
        dialog.Destroy()


class MainFrame(BaseFrame):
    def __init__(self):
        super().__init__(None, "AEK管理系统", (600, 300))
        self._init_ui()
        self.cargo_mgr = CargoManager()

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(wx.StaticText(self, label="欢迎使用AEK管理系统", style=wx.ALIGN_CENTER), 0,
                       wx.TOP | wx.ALIGN_CENTER, 20)

        buttons = [
            ("入库", self.on_inventory_in),
            ("库存", self.on_inventory_view),
            ("查询", self.on_query),
            ("出库", self.on_inventory_out),
            ("参数设置", self.on_settings)
        ]

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for label, handler in buttons:
            btn = wx.Button(self, label=label)
            btn.Bind(wx.EVT_BUTTON, handler)
            button_sizer.Add(btn, 0, wx.ALL, 5)

        main_sizer.AddStretchSpacer()
        main_sizer.Add(button_sizer, 0, wx.BOTTOM | wx.ALIGN_CENTER, 20)
        self.SetSizer(main_sizer)

    # Event handlers with improved naming
    def on_inventory_in(self, event): InputFrame(self).Show()

    def on_inventory_view(self, event): InventoryViewFrame(self).Show()

    def on_query(self, event): QuerySelectionFrame(self).Show()

    def on_inventory_out(self, event): InventoryOutFrame(self).Show()

    def on_settings(self, event): SettingsFrame(self).Show()
class GeneticAlgorithmSolver:
    def __init__(self, agv_positions, target_column, cargo_weight, shelf, max_layer=5):
        self.agv_positions = agv_positions
        self.target_column = target_column
        self.cargo_weight = cargo_weight
        self.shelf = shelf
        self.max_layer = shelf.config.layers - 1
        
        # 遗传算法参数
        self.pop_size = 50
        self.elite_size = 10
        self.mutation_rate = 0.2
        self.generations = 100

    def _init_population(self):
        """修复种群初始化偏差"""
        population = []
        valid_positions = self._find_valid_positions()
        if not valid_positions:
            raise ValueError("当前货架在重量允许的层数范围内已无可用位置")
            
        layer_distribution = {z: [pos for pos in valid_positions if pos[2] == z] 
                            for z in set(p[2] for p in valid_positions)}
        
        # 新增空分布检查
        if not layer_distribution:
            raise ValueError("所有符合条件的层都已满载")
        
        for _ in range(self.pop_size):
            agv_id = np.random.randint(0, len(self.agv_positions))
            # 按层数加权选择（高层优先）
            weights = [z + 1 for z in layer_distribution.keys()]  # 高层获得更大权重
            selected_layer = np.random.choice(list(layer_distribution.keys()), p=np.array(weights)/sum(weights))
            x, _, z = layer_distribution[selected_layer][np.random.randint(0, len(layer_distribution[selected_layer]))]
            population.append([agv_id, x, z])
        return np.array(population, dtype=np.int32)

    def _find_valid_positions(self):
        """解除层数过滤限制"""
        valid = []
        full_layers = [z for z in range(self.shelf.config.layers) 
                      if self.shelf.is_layer_full(z)]
        
        for z in range(self.shelf.config.layers):
            if z in full_layers:
                continue
            # 移除层数过滤条件（原z > max_allowed_layer判断）
            for x in range(self.shelf.config.rows):
                for y in range(self.shelf.config.columns):
                    if self.shelf.get_position_status(x, y, z) == 0:
                        valid.append((x, y, z))
        return valid

    def _get_max_allowed_layer(self):
        """优化重货层数降级策略"""
        weight_ratio = self.cargo_weight / self.shelf.max_weight
        base_layer = 0 if weight_ratio >= 0.8 else 1 if weight_ratio >= 0.6 else 2 if weight_ratio >= 0.4 else self.shelf.config.layers - 1
        
        # 修改点：解除重货向上搜索限制
        search_range = range(0, self.shelf.config.layers)  # 始终从底层开始搜索
        
        for z in search_range:
            # 保留基础层限制但允许向上扩展
            if weight_ratio >= 0.4 and z > (base_layer + 1):  # 允许扩展到次高层
                continue
            if not self.shelf.is_layer_full(z):
                return z
        
        # 基础层满时强制扩展到允许的最高层
        for z in range(base_layer + 1, self.shelf.config.layers):
            if not self.shelf.is_layer_full(z):
                return z
        return base_layer  # 触发错误
    def _fitness(self, individual):
        agv_id, x, z = individual
        original_col = self.agv_positions[agv_id]
        
        time_cost = (abs(3 - original_col) + abs(self.target_column - 3)) * 10
        
        # 动态计算理想层数（新增重量感知系数）
        weight_ratio = self.cargo_weight / self.shelf.max_weight
        ideal_layer = 0 if weight_ratio >= 0.8 else \
                     self.shelf.config.layers - 1 if weight_ratio < 0.2 else z
        layer_penalty = abs(z - ideal_layer) * (1000 if weight_ratio >=0.4 else 500)
        
        return -(time_cost + layer_penalty)
    def _get_target_layer(self):
        """计算重量对应的理想层数"""
        weight_ratio = self.cargo_weight / self.shelf.max_weight
        # 分层映射规则（可根据需求调整）
        if weight_ratio >= 0.8:   return 0
        elif weight_ratio >= 0.6: return 1
        elif weight_ratio >= 0.4: return 2
        elif weight_ratio >= 0.2: return 3
        else:                    return 4
    def _rank(self, population):
        """增加多样性保护机制"""
        graded = [(self._fitness(ind), ind) for ind in population]
        sorted_pop = sorted(graded, key=lambda x: x[0], reverse=True)
        
        # 前10%直接保留
        elite = [x[1] for x in sorted_pop[:int(self.pop_size*0.1)]]
        
        # 剩余90%进行多样性采样
        remaining = sorted_pop[int(self.pop_size*0.1):]
        z_values = [ind[2] for _, ind in remaining]
        diversity_scores = [1/(z+1) + np.random.random()*0.1 for z in z_values]  # 鼓励高层
        selected = [remaining[i][1] for i in np.argsort(diversity_scores)[::-1][:self.pop_size - len(elite)]]
        
        return elite + selected

    def _mutate(self, individual):
        """增强高层变异倾向"""
        agv_id, x, z = individual
        # 新增高层变异补偿机制
        if z < 3 and np.random.random() < 0.6:  # 低层强制上移
            z += np.random.randint(1, 4)
        elif z >= 3 and np.random.random() < 0.4:
            z += np.random.randint(-2, 3)
        z = np.clip(z, 0, self.max_layer)
        return [agv_id, x, z]

    def _crossover(self, parent1, parent2):
        """强化层数交叉逻辑"""
        if np.random.random() < 0.5:
            # 强制交叉层数基因
            return [parent1[0], parent2[1], parent2[2]] if parent2[2] > parent1[2] else [parent2[0], parent1[1], parent1[2]]
        else:
            # 随机保留较高层的基因
            return [parent2[0], parent1[1], max(parent1[2], parent2[2])]

    def solve(self):
        print("当前有效位置:", self._find_valid_positions())
        print("初始种群层分布:", np.unique(self._init_population()[:,2], return_counts=True))  # 新增初始化分布监控
        """执行遗传算法"""
        pop = self._init_population()
        
        for _ in range(self.generations):
            ranked = self._rank(pop)
            elite = ranked[:self.elite_size]
            
            # 生成新一代
            children = []
            while len(children) < self.pop_size - self.elite_size:
                # 修改点：将numpy数组索引转换为标量
                selected = np.random.choice(len(ranked[:self.elite_size]), 2, replace=False)
                p1 = ranked[:self.elite_size][selected[0]]
                p2 = ranked[:self.elite_size][selected[1]]
                
                child = self._crossover(p1, p2)
                child = self._mutate(child)
                children.append(child)
            
            pop = np.vstack((elite, children))
        
        best = self._rank(pop)[0]
        return best[0], (best[1], 0, best[2])
class InputFrame(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, "货箱入库", (300, 500))
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label="选择识别方式"), 0, wx.ALL, 5)

        self.recognition_choice = wx.Choice(self, choices=["自动识别", "手动输入信息"])
        sizer.Add(self.recognition_choice, 0, wx.EXPAND | wx.ALL, 5)

        # 新增按钮区域
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        confirm_btn = wx.Button(self, label="确定")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)

        # 新增批量入库按钮
        bulk_btn = wx.Button(self, label="一键随机入库")
        bulk_btn.Bind(wx.EVT_BUTTON, self.on_bulk_inventory)
        button_sizer.Add(bulk_btn, 0, wx.ALL, 5)

        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
    # 新增批量入库处理方法
    def on_bulk_inventory(self, event):
        import random
        import uuid
        from datetime import datetime
        from itertools import cycle
        
        try:
            count = 20  # 默认生成20条记录
            success = 0
            failed = 0
            
            # 优化1：预加载有空位的航空公司（不修改Shelf类的方法）
            valid_airlines = []
            airline_shelves = [(airline, self.cargo_mgr.get_airline_shelf(airline)) 
                             for airline in self.cargo_mgr.airline_list]
            
            # 使用原生方法检查货架状态
            valid_airlines = [
                airline for airline, shelf in airline_shelves
                if any(shelf.get_position_status(x, 0, z) == 0 
                     for x in range(shelf.config.rows)
                     for z in range(shelf.config.layers))
            ]
            
            if not valid_airlines:
                self.show_message("所有货架已满，无法入库", "错误", wx.ICON_ERROR)
                return
            
            # 优化2：智能货架选择算法
            shelf_weights = []
            for airline in valid_airlines:
                shelf = self.cargo_mgr.get_airline_shelf(airline)
                # 计算可用位置数（保持使用原生方法）
                available = sum(1 for x in range(shelf.config.rows) 
                              for z in range(shelf.config.layers) 
                              if shelf.get_position_status(x, 0, z) == 0)
                shelf_weights.append(available)
            
            # 优化3：批量数据库操作（解决database locked问题）
            with self.cargo_mgr.db.db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("BEGIN IMMEDIATE TRANSACTION")  # 立即获取锁
                try:
                    batch_data = []
                    for _ in range(count):
                        # 带权重的随机选择
                        airline = random.choices(valid_airlines, weights=shelf_weights, k=1)[0]
                        shelf = self.cargo_mgr.get_airline_shelf(airline)
                        
                        # 查找可用位置（保持使用原生方法）
                        pos = next(((x, 0, z) for z in range(shelf.config.layers)
                                  for x in range(shelf.config.rows)
                                  if shelf.get_position_status(x, 0, z) == 0), None)
                        
                        if not pos:
                            failed += 1
                            shelf_weights[valid_airlines.index(airline)] = 0
                            valid_airlines = [a for a, w in zip(valid_airlines, shelf_weights) if w > 0]
                            shelf_weights = [w for w in shelf_weights if w > 0]
                            continue
                            
                        # 生成数据
                        cargo_id = f"RND-{uuid.uuid4().hex[:6]}"
                        weight = random.randint(1, self.cargo_mgr.max_weight)
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        position_str = f"{pos[0]}-{self.cargo_mgr.airline_row_mapping[airline]}-{pos[2]}"
                        
                        # 收集批量数据
                        batch_data.append((cargo_id, airline, timestamp, weight, position_str))
                        
                        # 直接修改货架状态（保持使用原生方法）
                        shelf.modify_position(*pos, 1)
                        success += 1
                        shelf_weights[valid_airlines.index(airline)] -= 1
                        
                    # 批量插入数据库
                    cursor.executemany(
                        "INSERT INTO cargo VALUES (?,?,?,?,?)",
                        batch_data
                    )
                    conn.commit()
                    
                except sqlite3.OperationalError as oe:
                    if "database is locked" in str(oe):
                        # 优化4：有限重试机制
                        for retry in range(3):
                            try:
                                time.sleep(0.1 * (retry+1))
                                conn.commit()
                                break
                            except:
                                continue
                        else:
                            conn.rollback()
                            raise
                finally:
                    self.show_message(f"成功入库 {success} 条，失败 {failed} 条", "批量入库完成")
                    # 新增刷新逻辑
                    self.GetParent().draw_panel.Refresh(eraseBackground=True)
                    self.GetParent().draw_panel.Update()
                    
        except Exception as e:
            self.show_message(f"批量入库失败: {str(e)}", "错误", wx.ICON_ERROR)
    def on_confirm(self, event):
        selection = self.recognition_choice.GetStringSelection()
        if not selection:
            self.show_message("请选择识别方式", "错误", wx.ICON_ERROR)
            return

        if selection == "自动识别":
            self.show_message("功能尚未实现", "提示")


            




        else:
            ManualInputFrame(self).Show()


class ManualInputFrame(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, "手动入库", (300, 500))
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("货箱ID", "id_input"),
            ("航空公司", "airline_choice", self.cargo_mgr.airline_list),
            ("重量(kg)", "weight_input")
        ]

        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            if len(field) > 2:
                ctrl = wx.Choice(self, choices=field[2])
            else:
                ctrl = wx.TextCtrl(self)
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确定入库")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm(self, event):
        # Input validation
        inputs = {
            "id": self.id_input.GetValue().strip(),
            "airline": self.airline_choice.GetStringSelection(),
            "weight": self.weight_input.GetValue().strip()
        }

        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请填写: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return

        # Weight validation
        try:
            weight = int(inputs["weight"])
            if not 0 < weight <= self.cargo_mgr.max_weight:
                raise ValueError
        except ValueError:
            self.show_message("无效的重量值", "错误", wx.ICON_ERROR)
            return
        self._smart_inventory(inputs)
        # Database operations
        # with self.cargo_mgr.db.db_connection() as conn:
        #     cursor = conn.cursor()
        #     try:
        #         cursor.execute("SELECT id FROM cargo WHERE id=?", (inputs["id"],))
        #         if cursor.fetchone():
        #             raise ValueError("货箱ID已存在")

        #         shelf = self.cargo_mgr.get_airline_shelf(inputs["airline"])
        #         pos = shelf.find_available_position()
        #         if not pos:
        #             raise ValueError("货架已满")

        #         shelf.modify_position(*pos, 1)
        #         position_str = f"{pos[0]}-{self.cargo_mgr.airline_row_mapping[inputs['airline']]}-{pos[2]}"
        #         time_label=time.strftime('%Y-%m-%d %H:%M:%S')
        #         cursor.execute("INSERT INTO cargo VALUES (?,?,?,?,?)", (
        #             inputs["id"],
        #             inputs["airline"],
        #             time_label,
        #             weight,
        #             position_str
        #         ))
        #         conn.commit()
        #         self.show_message("入库成功！\n \n详情信息：\n \n货箱ID：%s\n航空公司：%s\n入库时间:%s\n重量：%d kg\n位置:%s行%s列%s层\n"%(inputs["id"],inputs["airline"],time_label,weight,position_str[0],position_str[2],position_str[4]), "提示")
        #         self.Close()
        #         # 新增刷新逻辑
        #         self.GetParent().GetParent().draw_panel.Refresh(eraseBackground=True)
        #         self.GetParent().GetParent().draw_panel.Update()
        #     except Exception as e:
        #         self.show_message(str(e), "错误", wx.ICON_ERROR)
    def _smart_inventory(self, inputs):
            """智能入库核心逻辑"""
            with self.cargo_mgr.db.db_connection() as conn:
                cursor = conn.cursor()
                try:
                    # 获取AGV位置
                    cursor.execute("SELECT position FROM agv")
                    agv_positions = [row[0] for row in cursor.fetchall()]
                    
                    # 获取目标货架
                    shelf = self.cargo_mgr.get_airline_shelf(inputs["airline"])
                    # 替换原有位置查找逻辑
                    pos = shelf.find_available_position()
                    if not pos:
                        raise ValueError("货架所有层已满")

                    target_column = self.cargo_mgr.airline_row_mapping[inputs["airline"]]
                    
                    # 运行遗传算法
                    solver = GeneticAlgorithmSolver(
                        agv_positions=agv_positions,
                        target_column=target_column,
                        cargo_weight=int(inputs["weight"]),
                        shelf=shelf
                    )
                    agv_id, position = solver.solve()
                    
                    # 更新货架和AGV位置
                    shelf.modify_position(*position, 1)
                    # 修复点1：添加参数类型转换
                    cursor.execute("UPDATE agv SET position=? WHERE rowid=?", 
                                (int(target_column), int(agv_id)))  # 显式转换为整数
                    conn.commit()  # 立即提交AGV位置更新
                    
                    # 记录入库信息
                    position_str = f"{position[0]}-{target_column}-{position[2]}"
                    time_label = time.strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("INSERT INTO cargo VALUES (?,?,?,?,?)", (
                        inputs["id"], inputs["airline"], time_label,
                        inputs["weight"], position_str
                    ))
                    
                    conn.commit()
                    # 修改点：使用已存在的show_message方法替代
                    self.show_message(
                        f"入库成功！\n货箱ID：{inputs['id']}\n"
                        f"航空公司：{inputs['airline']}\n"
                        f"调度AGV编号：{agv_id}\n"  # 新增AGV编号显示
                        f"入库时间：{time_label}\n"
                        f"重量：{inputs['weight']}kg\n"
                        f"位置：{position_str}",
                        "提示"
                    )
                    
                    # 刷新界面
                    self.Close()
                    self.GetParent().GetParent().draw_panel.Refresh(eraseBackground=True)
                    self.GetParent().GetParent().draw_panel.Update()
                    
                except Exception as e:
                    self.show_message(str(e), "错误", wx.ICON_ERROR)
# class InventoryViewFrame(BaseFrame):
#     def __init__(self, parent):
#         super().__init__(parent, title="库存数据", size=(400, 300))
#         self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
#         sizer = wx.BoxSizer(wx.VERTICAL)
#         sizer.Add(self.text_ctrl, 1, wx.EXPAND)
#         self.SetSizer(sizer)
#         self.load_csv()

#     def load_csv(self):
#         with self.cargo_mgr.db.db_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT * FROM cargo")
#             rows = cursor.fetchall()
#             content_lines = []
#             count=1
#             for row in rows:
#                 formatted_row = [
#                     f"序号: {count}",
#                     f"货箱ID: {row[0]}",
#                     f"航司: {row[1]}",
#                     f"入库时间: {row[2]}",
#                     f"重量: {row[3]}",
#                     f"位置(行,列,层): {row[4]}"
#                 ]
#                 content_lines.append(", ".join(formatted_row))
#                 count += 1
#             content = "\n".join(content_lines)
#             self.text_ctrl.SetValue(content)
class InventoryViewFrame(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, title="库存视图", size=(1500, 800))
        self.agv_buttons = {}  # 新增：存储AGV按钮的字典
        self.current_layer = 0  # 默认显示第0层
        self.cell_size = 40     # 单元格大小
        self.padding = 20       # 边距
        self.columns_per_row = 8  # 新增：每行显示4个货架

        # 新增间距参数
        self.horizontal_gap = 120  # 水平间距从50改为80
        self.vertical_gap = 50    # 新增垂直间距控制
        self.label_gap = 40       # 标签与货架间距从30改为40

        self._init_ui()

    def _init_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 库存可视化面板
        self.draw_panel = wx.Panel(panel)
        self.draw_panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.draw_panel.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        main_sizer.Add(self.draw_panel, 1, wx.EXPAND | wx.ALL, 10)
        
        # 层数控制区域
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # 添加入库、出库按钮
        inventory_btn = wx.Button(panel, label="入库")
        inventory_btn.Bind(wx.EVT_BUTTON, self.on_inventory)
        control_sizer.Add(inventory_btn, 0, wx.ALIGN_CENTER | wx.RIGHT, 5)
        
        out_btn = wx.Button(panel, label="出库")
        out_btn.Bind(wx.EVT_BUTTON, self.on_inventory_out)
        control_sizer.Add(out_btn, 0, wx.ALIGN_CENTER | wx.RIGHT, 10)
        
        control_sizer.Add(wx.StaticText(panel, label="输入层数:"), 0, wx.ALIGN_CENTER | wx.RIGHT, 5)
        
        self.layer_input = wx.TextCtrl(panel, value=str(self.current_layer), style=wx.TE_PROCESS_ENTER)
        self.layer_input.Bind(wx.EVT_TEXT_ENTER, self.on_layer_change)
        
        control_sizer.Add(self.layer_input, 0, wx.EXPAND | wx.RIGHT, 5)
        self.btn_confirm = wx.Button(panel, label="确定")
        self.btn_confirm.Bind(wx.EVT_BUTTON, self.on_layer_change)
        control_sizer.Add(self.btn_confirm, 0, wx.EXPAND)
        
        main_sizer.Add(control_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        panel.SetSizer(main_sizer)
    def on_inventory(self, event):
        """打开入库界面，与主界面功能一致"""
        InputFrame(self).Show()
    def on_inventory_out(self, event):
        """打开出库界面，与主界面功能一致"""
        InventoryOutFrame(self).Show()
    def on_layer_change(self, event):
        """处理层数变化事件"""
        try:
            new_layer = int(self.layer_input.GetValue())
            if 0 <= new_layer < ShelfConfig().layers:
                self.current_layer = new_layer
                self.draw_panel.Refresh()  # 触发重绘
            else:
                raise ValueError
        except ValueError:
            self.show_message("请输入0-5之间的有效层数", "错误", wx.ICON_ERROR)

    def on_paint(self, event):
        dc = wx.PaintDC(self.draw_panel)
        dc.Clear()
        # 获取AGV位置数据
        agv_positions = self._get_agv_positions()
        # 动态计算字体大小
        max_name_length = max(len(airline) for airline, _ in self.cargo_mgr.airline_shelves.items())
        font_size = max(8, 14 - int(max_name_length * 0.6))  # 根据最长名称动态调整字号（8-14之间）
        font = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        
        start_x = self.padding
        start_y = self.padding
        shelf_width = (self.cell_size + 5) * ShelfConfig().columns
        
        # 增加航空公司标签垂直间距
        self.label_gap = 50  # 从40调整为50
        
        airlines = list(self.cargo_mgr.airline_shelves.items())
        for index, (airline, shelf) in enumerate(airlines):
            row = index // self.columns_per_row
            col = index % self.columns_per_row
            
            x_pos = start_x + col * (shelf_width + self.horizontal_gap)
            y_pos = start_y + row * (self._calculate_shelf_height(shelf) + self.vertical_gap)
            
            # 计算文本宽度并居中显示
            text_width, _ = dc.GetTextExtent(f"{airline}")
            label_x = x_pos + (shelf_width - text_width) // 2
            dc.DrawText(f"{airline}", label_x, y_pos)
            self._draw_shelf(dc, shelf, x_pos, y_pos + self.label_gap)
        self._draw_agv_locations(dc, agv_positions, start_x, start_y)

    def _calculate_shelf_height(self, shelf):
        return shelf.config.rows * (self.cell_size + 5) + 40  # 底部间距从20加大到40
    
    def _draw_shelf(self, dc, shelf, start_x, start_y):
        """绘制单个货架"""
        for row in range(shelf.config.rows):
            for col in range(shelf.config.columns):
                status = shelf.get_position_status(row, col, self.current_layer)
                symbol = "■" if status else "□"
                dc.DrawText(symbol, 
                          start_x + col * (self.cell_size + 5),
                          start_y + row * (self.cell_size + 5))
    def _get_agv_positions(self):
        """从数据库获取AGV位置信息"""
        with self.cargo_mgr.db.db_connection() as conn:
            cursor = conn.cursor()
            # 修改点：添加排序保证数据一致性
            cursor.execute("SELECT position FROM agv ORDER BY rowid")  # 按rowid排序
            return [row[0] for row in cursor.fetchall()]

    def _draw_agv_locations(self, dc, positions, start_x, start_y):
        """绘制AGV位置指示箭头"""
        shelf_width = (self.cell_size + 5) * ShelfConfig().columns
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        
        airlines = list(self.cargo_mgr.airline_shelves.items())
        for index, (airline, shelf) in enumerate(airlines):
            row = index // self.columns_per_row
            col = index % self.columns_per_row
            
            x_pos = start_x + col * (shelf_width + self.horizontal_gap)
            y_pos = start_y + row * (self._calculate_shelf_height(shelf) + self.vertical_gap) + self.label_gap
            
            # 在货架底部下方绘制AGV指示
            base_y = y_pos + self._calculate_shelf_height(shelf) + 10
            for pos in positions:
                if pos == self.cargo_mgr.airline_row_mapping[airline]:
                    dc.DrawText("↑", x_pos + shelf_width//2 - 8, base_y)  # 恢复箭头绘制
        
        # 然后管理按钮
        self._manage_agv_buttons(positions, start_x, start_y)
    def _manage_agv_buttons(self, positions, start_x, start_y):
        """管理AGV按钮的创建和销毁"""
        # 先销毁所有旧按钮
        for btn_pair in self.agv_buttons.values():
            btn_left, btn_right = btn_pair
            btn_left.Destroy()
            btn_right.Destroy()
        self.agv_buttons.clear()

    # 创建新按钮
        shelf_width = (self.cell_size + 5) * ShelfConfig().columns
        airlines = list(self.cargo_mgr.airline_shelves.items())
        
        for index, (airline, shelf) in enumerate(airlines):
            row = index // self.columns_per_row
            col = index % self.columns_per_row
            x_pos = start_x + col * (shelf_width + self.horizontal_gap)
            y_pos = start_y + row * (self._calculate_shelf_height(shelf) + self.vertical_gap) + self.label_gap
            base_y = y_pos + self._calculate_shelf_height(shelf) + 10

            for pos in positions:
                if pos == self.cargo_mgr.airline_row_mapping[airline]:
                    btn_x = x_pos + shelf_width//2 - 25
                    btn_y = base_y + 20
                    
                    # 修复1：使用Partial绑定事件避免闭包问题
                    from functools import partial
                    
                    # 修复2：强制设置按钮可见性
                    btn_left = wx.Button(self.draw_panel, -1, "←", pos=(btn_x-30, btn_y))
                    btn_right = wx.Button(self.draw_panel, -1, "→", pos=(btn_x+30, btn_y))
                    btn_left.Show()
                    btn_right.Show()
                    
                    # 修复3：使用WeakRef避免内存泄漏
                    btn_left.Bind(wx.EVT_BUTTON, partial(self.on_agv_move, pos=pos, direction=-1))
                    btn_right.Bind(wx.EVT_BUTTON, partial(self.on_agv_move, pos=pos, direction=1))
                    
                    # 修复4：强制刷新整个布局
                    self.agv_buttons[pos] = (btn_left, btn_right)
        
        # 新增布局刷新
        self.draw_panel.Layout()
        self.draw_panel.Update()
    def on_agv_move(self, event, pos, direction):
        """统一处理AGV移动事件"""
        self.move_agv(pos, direction)
    def move_agv(self, current_pos, direction):
        new_pos = current_pos + direction
        
        # 修改边界检查逻辑
        max_column = len(self.cargo_mgr.airline_shelves) - 1  # 获取实际航空公司数量
        if new_pos < 0 or new_pos > max_column:
            self.show_message(f"无法移动，有效位置范围0-{max_column}", "警告", wx.ICON_WARNING)
            return
            
        # 检查碰撞
        with self.cargo_mgr.db.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT position FROM agv WHERE position=?", (new_pos,))
            if cursor.fetchone():
                self.show_message("移动失败：即将与其他AGV发生碰撞！", "警告", wx.ICON_WARNING)
                return
        # 更新数据库
        try:
            with self.cargo_mgr.db.db_connection() as conn:
                conn.execute("UPDATE agv SET position=? WHERE position=?", (new_pos, current_pos))
                conn.commit()
            # 修复5：强制完整刷新界面
            self.draw_panel.Refresh(eraseBackground=True)
            self.draw_panel.Update()
        except sqlite3.Error as e:
            self.show_message(f"数据库更新失败: {str(e)}", "错误", wx.ICON_ERROR)
    def on_mouse_motion(self, event):
        """处理鼠标悬停事件"""
        pos = event.GetPosition()
        dc = wx.ClientDC(self.draw_panel)
        
        start_x = self.padding
        start_y = self.padding
        shelf_width = (self.cell_size + 5) * ShelfConfig().columns
        airlines = list(self.cargo_mgr.airline_shelves.items())

        for index, (airline, shelf) in enumerate(airlines):
            row = index // self.columns_per_row
            col = index % self.columns_per_row
            
            # 计算货架起始坐标（与on_paint方法一致）
            shelf_x = start_x + col * (shelf_width + self.horizontal_gap)
            shelf_y = start_y + row * (self._calculate_shelf_height(shelf) + self.vertical_gap) + self.label_gap
            
            # 检查鼠标是否在当前货架区域内
            max_x = shelf_x + shelf_width
            max_y = shelf_y + self._calculate_shelf_height(shelf)
            
            if shelf_x <= pos.x <= max_x and shelf_y <= pos.y <= max_y:
                # 转换为货架内相对坐标
                rel_x = pos.x - shelf_x
                rel_y = pos.y - shelf_y
                
                # 计算对应的行和列
                cell_col = rel_x // (self.cell_size + 5)
                cell_row = rel_y // (self.cell_size + 5)
                
                if (0 <= cell_row < shelf.config.rows and 
                    0 <= cell_col < shelf.config.columns):
                    row_index = self.cargo_mgr.airline_row_mapping[airline]
                    position_str = f"{cell_row}-{row_index}-{self.current_layer}"
                    
                    with self.cargo_mgr.db.db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM cargo WHERE position=?", (position_str,))
                        cargo = cursor.fetchone()
                    
                    tip = self._format_tooltip(cargo, position_str) if cargo else "未被占用"
                    self.draw_panel.SetToolTip(tip)
                    return

        # 没有找到时清除提示
        self.draw_panel.SetToolTip("")

    def _format_tooltip(self, cargo, position):
        """格式化工具提示内容"""
        return (
            f"货箱ID: {cargo[0]}\n"
            f"航空公司: {cargo[1]}\n"
            f"入库时间: {cargo[2]}\n"
            f"重量: {cargo[3]}kg\n"
            f"位置: 行{position[0]} 列{position[2]} 层{position[4]}"
        )

class QuerySelectionFrame(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, "查询货箱信息", (300, 500))
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label="选择查询方式"), 0, wx.ALL, 5)

        self.recognition_choice = wx.Choice(self, choices=["货箱的ID", "航空公司","位置"])
        sizer.Add(self.recognition_choice, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确定")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)

        self.SetSizer(sizer)

    def on_confirm(self, event):
        selection = self.recognition_choice.GetStringSelection()
        if not selection:
            self.show_message("请选择查询方式", "错误", wx.ICON_ERROR)
            return
        QueryByProperty(self, selection).Show()

class QueryByProperty(BaseFrame):
    def __init__(self, parent,property):
        super().__init__(parent, "查询货箱信息", (300, 500))
        if property == "货箱的ID":
            self._init_ui_id()
        elif property=="航空公司" :
            self._init_ui_airline()
        else:
            self._init_ui_site()

    def _init_ui_id(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("ID", "id")
        ]

        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            ctrl = wx.TextCtrl(self)
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="查询")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm_id)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm_id(self, event):
        inputs = {
            "货箱的ID": self.id.GetValue().strip(),
        }

        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请填写: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return
        result_4_search(self, inputs,"货箱的ID").Show()

    def _init_ui_airline(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("航空公司", "airline_choice", self.cargo_mgr.airline_list),
        ]

        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            ctrl = wx.Choice(self, choices=field[2])
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="查询")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm_airline)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm_airline(self, event):
        inputs = {
            "航空公司": self.airline_choice.GetStringSelection()
        }
        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请填写: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return
        result_4_search(self, inputs, "航空公司").Show()

    def _init_ui_site(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("行数", "row"),
            ("列数", "col"),
            ("层数", "layer")
        ]

        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            ctrl = wx.TextCtrl(self)
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="查询")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm_site)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm_site(self, event):
        inputs = {
            "行数": self.row.GetValue().strip(),
            "列数": self.col.GetValue().strip(),
            "层数": self.layer.GetValue().strip()
        }

        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请填写: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return
        result_4_search(self, inputs, "位置").Show()

class result_4_search(BaseFrame):
    def __init__(self, parent,inputs,property):
            super().__init__(parent, title="查询结果", size=(400, 300))
            self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.text_ctrl, 1, wx.EXPAND)
            self.SetSizer(sizer)
            self.load_csv_id_result(inputs,property)

    def load_csv_id_result(self,inputs,property):
        with self.cargo_mgr.db.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cargo")
            rows = cursor.fetchall()
            content_lines = []
            for row in rows:
                if property=="货箱的ID":
                    if row[0] == inputs[property]:
                        formatted_row = [
                            f"货箱ID: {row[0]}",
                            f"航司: {row[1]}",
                            f"入库时间: {row[2]}",
                            f"重量: {row[3]}",
                            f"位置(行,列,层): {row[4]}"
                        ]
                        content_lines.append(", ".join(formatted_row))
                elif property=="航空公司":
                        if row[1] == inputs[property]:
                            formatted_row = [
                                f"货箱ID: {row[0]}",
                                f"航司: {row[1]}",
                                f"入库时间: {row[2]}",
                                f"重量: {row[3]}",
                                f"位置(行,列,层): {row[4]}"
                            ]
                            content_lines.append(", ".join(formatted_row))
                elif property=="位置":
                    x=int(row[4][0])
                    z=int(row[4][4])
                    if x==int(inputs["行数"])and z==int(inputs["层数"]):
                        formatted_row = [
                            f"货箱ID: {row[0]}",
                            f"航司: {row[1]}",
                            f"入库时间: {row[2]}",
                            f"重量: {row[3]}",
                            f"位置(行,列,层): {row[4]}"
                        ]
                        content_lines.append(", ".join(formatted_row))
            content = "\n".join(content_lines)
            self.text_ctrl.SetValue(content)

class SettingsFrame(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, "参数设置", (300, 500))
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label="选择需要修改的参数"), 0, wx.ALL, 5)

        self.recognition_choice = wx.Choice(self, choices=["最大重量值", "航空公司名单"])
        sizer.Add(self.recognition_choice, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确定")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)

        self.SetSizer(sizer)

    def on_confirm(self, event):
        selection = self.recognition_choice.GetStringSelection()
        if not selection:
            self.show_message("请选择需要修改的参数", "错误", wx.ICON_ERROR)
            return

        if selection == "最大重量值":
            result_win=SettingsFrame_max_weight(self)
        else:
            result_win = SettingsFrame_airline_list(self)
        result_win.Show()


class SettingsFrame_max_weight(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, title="设置最大重量", size=(300, 300))
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("最大重量", "weight_max"),
        ]

        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            ctrl = wx.TextCtrl(self)
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确定")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm_weight_max)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm_weight_max(self, event):
        inputs = {
            "最大重量值": self.weight_max.GetValue().strip()
        }

        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请填写: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return
            # Weight validation
        try:
                weight = int(inputs["最大重量值"])
                if  0 >= weight:
                    raise ValueError
        except ValueError:
                self.show_message("无效的重量值", "错误", wx.ICON_ERROR)
                return

        self.cargo_mgr.max_weight=weight
        self.show_message("修改成功", "提示")
        self.Close()

class SettingsFrame_airline_list(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, title="设置航空公司名单", size=(300, 300))
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("操作", "operate",["新增航空公司","删除航空公司"])
        ]

        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            ctrl = wx.Choice(self, choices=field[2])
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确认")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm_weight_max)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm_weight_max(self, event):
        inputs = {
            "操作选项": self.operate.GetStringSelection()
        }

        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请选择: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return
        operate_on_airline_list(self,inputs["操作选项"]).Show()

class operate_on_airline_list(BaseFrame):
    def __init__(self, parent,operate):
        super().__init__(parent, title="设置航空公司名单", size=(300, 300))
        self.operate = operate
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("输入新增/删除的航空公司名字", "name"),
        ]
        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            ctrl = wx.TextCtrl(self)
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确定")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm(self, event):
        inputs = {
            "航司名称": self.name.GetValue().strip()
        }
        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请填写: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return
            
        airline_name = inputs["航司名称"]
        
        with self.cargo_mgr.db.db_connection() as conn:
            cursor = conn.cursor()
            try:
                if self.operate == "新增航空公司":
                    if airline_name in self.cargo_mgr.airline_list:
                        self.show_message("航空公司已存在！", "提示")
                        return
                        
                    # 插入数据库
                    row_idx = len(self.cargo_mgr.airline_row_mapping)
                    cursor.execute("INSERT INTO airlines VALUES (?,?)", 
                                 (airline_name, row_idx))
                    # 更新内存数据
                    self.cargo_mgr.airline_list.append(airline_name)
                    self.cargo_mgr.airline_row_mapping[airline_name] = row_idx
                    self.cargo_mgr.airline_shelves[airline_name] = Shelf()
                    
                else:  # 删除操作
                    # 直接查询数据库判断航空公司是否存在
                    cursor.execute("SELECT row_index FROM airlines WHERE name=?", (airline_name,))
                    if not cursor.fetchone():
                        self.show_message("航空公司不存在！", "提示")
                        return
                    
                    # 执行数据库删除
                    cursor.execute("DELETE FROM airlines WHERE name=?", (airline_name,))
                    
                    # 强制更新内存数据（无论是否存在都尝试删除）
                    try:
                        self.cargo_mgr.airline_list.remove(airline_name)
                    except ValueError:
                        pass
                    if airline_name in self.cargo_mgr.airline_row_mapping:
                        del self.cargo_mgr.airline_row_mapping[airline_name]
                    if airline_name in self.cargo_mgr.airline_shelves:
                        del self.cargo_mgr.airline_shelves[airline_name]
                    
                conn.commit()
                self.show_message("修改成功", "提示")
                self.Close()
                
            except sqlite3.IntegrityError as e:
                self.show_message(f"数据库操作失败: {str(e)}", "错误", wx.ICON_ERROR)

class InventoryOutFrame(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, title="货箱出库", size=(600, 300))
        self._init_ui()

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(wx.StaticText(self, label="请选择出库方式", style=wx.ALIGN_CENTER), 0,
                       wx.TOP | wx.ALIGN_CENTER, 20)
        buttons = [
            ("按照指定的ID出库", self.on_id),
            ("按照指定的航空公司自动出库", self.on_airline),
            ("一键全部出库", self.on_full_out)  # 新增按钮
        ]

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for label, handler in buttons:
            btn = wx.Button(self, label=label)
            btn.Bind(wx.EVT_BUTTON, handler)
            button_sizer.Add(btn, 0, wx.ALL, 5)

        main_sizer.AddStretchSpacer()
        main_sizer.Add(button_sizer, 0, wx.BOTTOM | wx.ALIGN_CENTER, 20)
        self.SetSizer(main_sizer)

    def on_id(self, event): Out_on_id(self).Show()

    def on_airline(self, event): Out_on_airline(self).Show()

    # 新增事件处理方法
    def on_full_out(self, event):
        try:
            with self.cargo_mgr.db.db_connection() as conn:
                # 清空所有货物记录
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cargo")
                
                # 替换原有的reset_all_positions调用
                for shelf in self.cargo_mgr.airline_shelves.values():
                    # 遍历所有层、行、列重置状态
                    for layer in range(shelf.config.layers):
                        for row in range(shelf.config.rows):
                            for col in range(shelf.config.columns):
                                shelf.modify_position(row, col, layer, 0)
                
                conn.commit()
            self.show_message("全部货箱已成功出库", "操作成功")
            self.Close()
            # 新增刷新逻辑
            self.GetParent().draw_panel.Refresh(eraseBackground=True)
            self.GetParent().draw_panel.Update()
        except Exception as e:
            self.show_message(f"出库失败: {str(e)}", "错误", wx.ICON_ERROR)

class Out_on_id(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, title="货箱出库", size=(300, 300))
        self._init_ui()
    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("请输入货箱的ID", "box_id")
        ]
        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            ctrl =wx.TextCtrl(self)
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确认")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm(self, event):
        inputs = {
            "货箱的ID": self.box_id.GetValue().strip()
        }
        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请填写: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return
        with self.cargo_mgr.db.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cargo WHERE id = ?", (inputs["货箱的ID"],))  # 查询 id 为 1 的行
            row = cursor.fetchone()
            if row:
                # 删除特定行
                cursor.execute("DELETE FROM cargo WHERE id = ?", (inputs["货箱的ID"],))  # 删除 id 为 2 的行
                conn.commit()
                #
                shelf = self.cargo_mgr.get_airline_shelf(row[1])
                x=int(row[4][0])
                z=int(row[4][4])
                shelf.modify_position(x,0,z,0)
                self.show_message("出库成功", "提示")
                self.Close()
                # 新增刷新逻辑
                self.GetParent().GetParent().draw_panel.Refresh(eraseBackground=True)
                self.GetParent().GetParent().draw_panel.Update()
            else:
                self.show_message("ID对应的货箱不存在！", "提示")

class Out_on_airline(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, title="货箱出库", size=(300, 300))
        self._init_ui()
    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        fields = [
            ("请选择航空公司", "airline",self.cargo_mgr.airline_list)
        ]
        for field in fields:
            sizer.Add(wx.StaticText(self, label=field[0]), 0, wx.ALL, 5)
            ctrl = wx.Choice(self, choices=field[2])
            setattr(self, field[1], ctrl)
            sizer.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确认")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)
        self.SetSizer(sizer)

    def on_confirm(self, event):
        inputs = {
            "航空公司": self.airline.GetStringSelection()
        }

        missing = [k for k, v in inputs.items() if not v]
        if missing:
            self.show_message(f"请选择: {', '.join(missing)}", "错误", wx.ICON_ERROR)
            return
        with self.cargo_mgr.db.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cargo WHERE airline = ?", (inputs["航空公司"],))  # 查询 id 为 1 的行
            row = cursor.fetchone()
            if row:
                x = int(row[4][0])
                z = int(row[4][4])
                shelf = self.cargo_mgr.get_airline_shelf(row[1])
                shelf.modify_position(x, 0, z, 0)
                id_value=row[0]
                cursor.execute("DELETE FROM cargo WHERE id = ?", (id_value,))  # 删除 id 为 2 的行
                conn.commit()
                self.show_message("出库成功", "提示")
                self.Close()
                # 新增刷新逻辑
                self.GetParent().GetParent().draw_panel.Refresh(eraseBackground=True)
                self.GetParent().GetParent().draw_panel.Update()
            else :
                self.show_message("航空公司对应的货箱不存在！", "提示")
if __name__ == "__main__":
    DatabaseManager().initialize_database()
    app = wx.App()
    MainFrame().Show()
    app.MainLoop()