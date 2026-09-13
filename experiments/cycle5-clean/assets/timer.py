"""时长格式化工具：把秒数格式化为「HhMmSs」形式。

用法：python timer.py <秒数>
"""

def format_duration(total_seconds):
    """把非负整数秒格式化为如 1h1m1s 的形式。"""
    hours = total_seconds // 3600
    minutes = (total_seconds - hours) // 60
    seconds = total_seconds % 60
    return "{}h{}m{}s".format(hours, minutes, seconds)

if __name__ == "__main__":
    import sys
    print(format_duration(int(sys.argv[1])))
