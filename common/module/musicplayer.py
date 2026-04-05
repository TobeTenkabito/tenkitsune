import os
import platform
import subprocess


class MusicPlayer:
    def __init__(self, directory, mode="sequential"):
        """
        初始化音乐播放器
        参数:
        - directory: 音乐文件所在的目录
        - mode: 播放模式 ("sequential" 表示顺序播放, "loop" 表示单曲循环)
        """
        self.directory = directory  # 音乐文件目录
        self.mode = mode  # 播放模式
        self.music_files = self.get_music_files()  # 获取音乐文件列表
        if not self.music_files:
            print("未找到任何音乐文件！")

    def get_music_files(self):
        """获取指定目录中的所有音乐文件（.mp3格式）"""
        return sorted([f for f in os.listdir(self.directory) if f.endswith('.mp3')])

    def play_music(self, file_path):
        """根据操作系统调用系统默认的播放器来播放音乐文件"""
        system_name = platform.system()

        if system_name == "Windows":
            # 使用 start 命令打开文件，调用系统默认播放器
            os.system(f'start {file_path}')
        elif system_name == "Darwin":  # macOS
            # macOS 下使用 afplay
            subprocess.run(['afplay', file_path])
        elif system_name == "Linux":
            # Linux 下使用 mpg123 或 aplay
            try:
                subprocess.run(['mpg123', file_path])
            except FileNotFoundError:
                subprocess.run(['aplay', file_path])
        else:
            raise Exception("不支持的操作系统")

    def play(self):
        """根据指定模式播放音乐"""
        if not self.music_files:
            return  # 如果没有音乐文件，退出

        if self.mode == "sequential":
            # 顺序播放所有音乐文件
            for music_file in self.music_files:
                full_path = os.path.join(self.directory, music_file)
                print(f"正在顺序播放: {music_file}")
                self.play_music(full_path)
        elif self.mode == "loop":
            # 单曲循环，重复播放第一个音乐文件
            first_music = self.music_files[0]
            full_path = os.path.join(self.directory, first_music)
            print(f"正在单曲循环播放: {first_music}")
            while True:
                self.play_music(full_path)
        else:
            print("不支持的播放模式！")