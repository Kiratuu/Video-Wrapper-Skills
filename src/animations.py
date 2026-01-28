"""
Animation functions for video effects
Implements Remotion-style animations in pure Python
"""
import numpy as np


def spring(frame, fps, from_value=0, to_value=1, damping=12, stiffness=200):
    """
    模拟 Remotion 的 spring 物理动画

    参数:
        frame: 当前帧数
        fps: 帧率
        from_value: 起始值
        to_value: 目标值
        damping: 阻尼系数
        stiffness: 刚度系数

    返回:
        当前帧的动画值
    """
    t = frame / fps
    omega = np.sqrt(stiffness)
    zeta = damping / (2 * np.sqrt(stiffness))

    if zeta < 1:  # 欠阻尼
        omega_d = omega * np.sqrt(1 - zeta**2)
        A = 1
        B = zeta * omega / omega_d
        value = (A * np.cos(omega_d * t) + B * np.sin(omega_d * t)) * np.exp(-zeta * omega * t)
    else:  # 临界阻尼或过阻尼
        value = (1 + t) * np.exp(-t)

    return from_value + (to_value - from_value) * (1 - value)


def interpolate(input_value, input_range, output_range, extrapolate='clamp'):
    """
    值映射插值（类似 Remotion 的 interpolate）

    参数:
        input_value: 输入值
        input_range: 输入范围 [min, max]
        output_range: 输出范围 [min, max]
        extrapolate: 'clamp' 或 'extend'
    """
    input_min, input_max = input_range
    output_min, output_max = output_range

    # 归一化输入
    progress = (input_value - input_min) / (input_max - input_min)

    if extrapolate == 'clamp':
        progress = np.clip(progress, 0, 1)

    # 映射到输出范围
    return output_min + progress * (output_max - output_min)


def ease_in_out(t):
    """
    缓入缓出曲线
    """
    return t * t * (3 - 2 * t)
