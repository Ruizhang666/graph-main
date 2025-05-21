import pandas as pd

INPUT_CSV_PATH = '三层股权穿透输出数据.csv'
OUTPUT_CSV_PATH = '三层股权穿透输出数据_level0_only.csv'

def filter_and_save_level0(input_path, output_path):
    """
    读取指定的CSV文件，筛选出 'level' 为 0 的行，并保存到新的CSV文件。
    尝试使用多种常见的中文编码读取文件。
    """
    encodings_to_try = ['gbk', 'gb18030', 'gb2312', 'utf-8', 'utf-8-sig']
    df = None

    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(input_path, encoding=encoding, dtype=str) # 读取所有列为字符串以保留原始格式
            print(f"Successfully read CSV with encoding: {encoding}")
            break # 成功读取后即跳出循环
        except UnicodeDecodeError:
            print(f"Failed to decode CSV with encoding: {encoding}")
        except Exception as e:
            print(f"An unexpected error occurred while reading with {encoding}: {e}")
            # 如果是pd.errors.EmptyDataError等其他错误，也继续尝试下一种编码
            if isinstance(e, pd.errors.EmptyDataError):
                 print(f"Empty data error with {encoding}, trying next.")
            elif "Error tokenizing data" in str(e):
                 print(f"Tokenizing error with {encoding}, trying next.")
            else: # 对于未知错误，可以选择中断或记录并继续
                pass # 这里选择继续尝试

    if df is None:
        print(f"Error: Could not read CSV file '{input_path}' with any of the attempted encodings.")
        return

    # 筛选 level 为 '0' 的行。注意CSV中level可能是字符串'0'或数字0。
    # 为了安全起见，我们将其转换为字符串进行比较。
    if 'level' not in df.columns:
        print(f"Error: 'level' column not found in {input_path}.")
        return

    df_level0 = df[df['level'].astype(str) == '0']

    try:
        df_level0.to_csv(output_path, index=False, encoding='utf-8-sig') # 保存为utf-8-sig以更好兼容Excel打开中文
        print(f"Successfully filtered and saved level 0 data to: {output_path}")
        print(f"Original rows: {len(df)}, Level 0 rows: {len(df_level0)}")
    except Exception as e:
        print(f"Error saving filtered CSV to '{output_path}': {e}")

if __name__ == '__main__':
    filter_and_save_level0(INPUT_CSV_PATH, OUTPUT_CSV_PATH) 