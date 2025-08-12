import importlib
import os


class DLCManager:
    def __init__(self):
        self.dlc_modules = []
        self.loaded_dlc_names = []

    def load_all_dlcs(self):
        """自动扫描并加载DLC模块（支持单个.py文件和子包），尝试三种路径方案。"""
        dlc_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dlc')),  # 方案1：相对于当前脚本路径
            os.path.abspath(os.path.join(os.getcwd(), 'dlc')),  # 方案2：相对于工作目录
            'F:/天狐修炼纪/dlc'  # 方案3：替换为 DLC 文件夹的绝对路径（如适用）
        ]
        dlc_dir = None
        for path in dlc_paths:
            if os.path.exists(path):
                dlc_dir = path
                break
        if not dlc_dir:
            print("未找到 DLC 目录，请检查路径配置。")
            return []
        print(f"使用 DLC 目录路径: {dlc_dir}")

        for filename in os.listdir(dlc_dir):
            dlc_path = os.path.join(dlc_dir, filename)
            dlc_name = None

            # 处理单个 .py 文件
            if filename.endswith(".py") and filename != "__init__.py":
                dlc_name = f"dlc.{filename[:-3]}"

            # 处理文件夹（子包）
            elif os.path.isdir(dlc_path) and "__init__.py" in os.listdir(dlc_path):
                dlc_name = f"dlc.{filename}"

            # 如果识别出了 DLC 名称，尝试加载模块
            if dlc_name:
                try:
                    print(f"尝试加载模块: {dlc_name}")
                    dlc_module = importlib.import_module(dlc_name)
                    dlc_class_name = [name for name in dir(dlc_module) if name.startswith("DLC")][0]
                    dlc_instance = getattr(dlc_module, dlc_class_name)()  # 实例化DLC
                    self.dlc_modules.append(dlc_instance)
                    # 记录加载成功的DLC名称
                    self.loaded_dlc_names.append(dlc_name)
                    print(f"DLC {dlc_name} 加载成功!")
                except (ModuleNotFoundError, IndexError):
                    print(f"DLC {dlc_name} 未找到或加载失败，跳过...")
        return self.dlc_modules

    def is_dlc_loaded(self, dlc_name):
        """检查特定的DLC是否已经加载"""
        return dlc_name in self.loaded_dlc_names

    def apply_dlcs_to_player(self, player):
        """将所有加载的DLC应用到玩家"""
        for dlc in self.dlc_modules:
            dlc.apply_to_player(player)
