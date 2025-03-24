import wx
import sqlite3
import time
import numpy as np
from contextlib import contextmanager
from dataclasses import dataclass

DATABASE_NAME = "cargo.db"
MAX_WEIGHT = 500
AIRLINE_LIST = ["东方航空", "南方航空", "春秋航空", "中国国际航空"]


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
    def __init__(self, config=ShelfConfig()):
        self.config = config
        self.storage = np.zeros((config.rows, config.columns, config.layers), dtype=int)

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
        for z in range(self.config.layers):
            for x in range(self.config.rows):
                if self.storage[x, 0, z] == 0:
                    return (x, 0, z)
        return None


class CargoManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.airline_shelves = {}
        self.airline_row_mapping = {}
        self.max_weight = MAX_WEIGHT
        self.airline_list = AIRLINE_LIST.copy()
        self.load_initial_data()

    def load_initial_data(self):
        with self.db.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, row_index FROM airlines")
            for airline, row_idx in cursor.fetchall():
                self.airline_row_mapping[airline] = row_idx
                self.airline_shelves[airline] = Shelf()

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


class InputFrame(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, "货箱入库", (300, 500))
        self._init_ui()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, label="选择识别方式"), 0, wx.ALL, 5)

        self.recognition_choice = wx.Choice(self, choices=["自动识别", "手动输入信息"])
        sizer.Add(self.recognition_choice, 0, wx.EXPAND | wx.ALL, 5)

        confirm_btn = wx.Button(self, label="确定")
        confirm_btn.Bind(wx.EVT_BUTTON, self.on_confirm)
        sizer.Add(confirm_btn, 0, wx.ALL, 5)

        self.SetSizer(sizer)

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

        # Database operations
        with self.cargo_mgr.db.db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM cargo WHERE id=?", (inputs["id"],))
                if cursor.fetchone():
                    raise ValueError("货箱ID已存在")

                shelf = self.cargo_mgr.get_airline_shelf(inputs["airline"])
                pos = shelf.find_available_position()
                if not pos:
                    raise ValueError("货架已满")

                shelf.modify_position(*pos, 1)
                position_str = f"{pos[0]}-{self.cargo_mgr.airline_row_mapping[inputs['airline']]}-{pos[2]}"
                time_label=time.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("INSERT INTO cargo VALUES (?,?,?,?,?)", (
                    inputs["id"],
                    inputs["airline"],
                    time_label,
                    weight,
                    position_str
                ))
                conn.commit()
                self.show_message("入库成功！\n \n详情信息：\n \n货箱ID：%s\n航空公司：%s\n入库时间:%s\n重量：%d kg\n位置:%s行%s列%s层\n"%(inputs["id"],inputs["airline"],time_label,weight,position_str[0],position_str[2],position_str[4]), "提示")
                self.Close()

            except Exception as e:
                self.show_message(str(e), "错误", wx.ICON_ERROR)

class InventoryViewFrame(BaseFrame):
    def __init__(self, parent):
        super().__init__(parent, title="库存数据", size=(400, 300))
        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.load_csv()

    def load_csv(self):
        with self.cargo_mgr.db.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cargo")
            rows = cursor.fetchall()
            content_lines = []
            count=1
            for row in rows:
                formatted_row = [
                    f"序号: {count}",
                    f"货箱ID: {row[0]}",
                    f"航司: {row[1]}",
                    f"入库时间: {row[2]}",
                    f"重量: {row[3]}",
                    f"位置(行,列,层): {row[4]}"
                ]
                content_lines.append(", ".join(formatted_row))
                count += 1
            content = "\n".join(content_lines)
            self.text_ctrl.SetValue(content)

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
        if self.operate=="新增航空公司":
            if inputs["航司名称"] not in self.cargo_mgr.airline_list:
                self.cargo_mgr.airline_list.append(inputs["航司名称"])
                self.show_message("修改成功", "提示")
                self.Close()
            else :
                self.show_message("航空公司已存在！", "提示")
        else:
            if inputs["航司名称"] not in self.cargo_mgr.airline_list:
                self.show_message("航空公司不存在！", "提示")
            else :
                self.cargo_mgr.airline_list.remove(inputs["航司名称"])
                self.show_message("修改成功", "提示")
                self.Close()

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
            else :
                self.show_message("航空公司对应的货箱不存在！", "提示")
if __name__ == "__main__":
    DatabaseManager().initialize_database()
    app = wx.App()
    MainFrame().Show()
    app.MainLoop()