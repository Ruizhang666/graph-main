# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager

def get_font_properties():
    """
    Set up matplotlib to support Chinese fonts and return a FontProperties object.
    This function will also set plt.rcParams for sans-serif fonts and axes.unicode_minus.
    """
    font_prop = None
    # Attempt to use matplotlib's built-in Chinese fonts as fallbacks
    plt.rcParams['font.sans-serif'] = [
        'SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong', 
        'Arial Unicode MS', 'DejaVu Sans'
    ]
    plt.rcParams['axes.unicode_minus'] = False  # Fix for displaying the minus sign

    try:
        font_names = [f.name for f in fontManager.ttflist]
        
        preferred_fonts = [
            'SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong', 
            'STHeiti', 'STKaiti', 'STSong', 'STFangsong', 
            'PingFang SC', 'Heiti SC', 'Songti SC', 'Arial Unicode MS'
        ]
        
        chinese_font_family = None
        for font_name in preferred_fonts:
            if font_name in font_names:
                chinese_font_family = font_name
                break
        
        if chinese_font_family:
            font_prop = FontProperties(family=chinese_font_family)
            print(f"Font Config: Using font family '{chinese_font_family}'")
        else:
            print("Font Config Warning: Specified Chinese fonts not found. Will attempt to use system default or matplotlib fallback.")
            font_prop = FontProperties() # Use matplotlib's fallback
    except Exception as e:
        print(f"Font Config Error: {e}")
        print("Font Config Warning: Error during font setup. Will attempt to use system default or matplotlib fallback.")
        font_prop = FontProperties() # Fallback on error

    return font_prop

if __name__ == '__main__':
    # Test function
    fp = get_font_properties()
    plt.figure()
    # Test with Chinese characters directly in the code
    plt.title("测试中文字体标题", fontproperties=fp)
    plt.xlabel("测试X轴", fontproperties=fp)
    plt.ylabel("测试Y轴", fontproperties=fp)
    plt.text(0.5, 0.5, "文本测试", fontproperties=fp)
    # plt.show() # Uncomment for visual test when running as script
    print(f"Test complete. Font family used: {fp.get_family()}") 