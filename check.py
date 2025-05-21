import pandas as pd
import json
import ast

# --- 配置 ---
TARGET_COMPANY_NAME = "中基宁波集团股份有限公司"
CSV_FILE_PATH = "三层股权穿透输出数据_1.csv" # 确保路径正确
ENCODINGS_TO_TRY = ['gbk', 'utf-8-sig', 'utf-8', 'gb18030', 'gb2312'] # 优先尝试gbk，根据之前日志
OUTPUT_TXT_FILE = "check_output.txt" # 新增：定义输出文件名

# 全局文件句柄
output_file_handle = None

# --- 辅助函数：记录并打印 ---
def log_and_print(message):
    """将消息打印到控制台并写入到全局文件句柄"""
    print(message)
    if output_file_handle:
        output_file_handle.write(str(message) + "\\n")

# --- 辅助函数：解析 children 字符串 ---
def parse_children_string(children_str, company_name_for_error_msg):
    """
    解析 'children' 字段的字符串，该字符串可能是一个JSON列表或类似Python列表的字符串。
    参考 graph_builder.py 中的解析逻辑。
    """
    if not children_str or pd.isna(children_str) or children_str in ['[]', '']:
        return []

    children_list = None
    # 1. 尝试 ast.literal_eval
    try:
        children_list = ast.literal_eval(children_str)
        if not isinstance(children_list, list):
            # log_and_print(f"调试: ast.literal_eval for {company_name_for_error_msg} did not return a list. Type: {type(children_list)}. Data: {children_str[:100]}")
            raise ValueError("ast.literal_eval did not result in a list.")
        # log_and_print(f"调试: ast.literal_eval successful for {company_name_for_error_msg}")
        return children_list
    except (ValueError, SyntaxError) as e_ast:
        # log_and_print(f"调试: ast.literal_eval failed for {company_name_for_error_msg}. Error: {e_ast}. Falling back to JSON parsing. Data: {children_str[:100]}")
        pass

    # 2. 尝试复杂的JSON解析 (处理内部单引号)
    try:
        processed_str = children_str.replace("\\\\'", "__TEMP_SINGLE_QUOTE__")
        processed_str = processed_str.replace("'", '"')
        processed_str = processed_str.replace("__TEMP_SINGLE_QUOTE__", "'")
        children_list = json.loads(processed_str)
        # log_and_print(f"调试: Complex JSON parsing successful for {company_name_for_error_msg}")
        return children_list
    except json.JSONDecodeError as e_json_primary:
        # log_and_print(f"调试: Complex JSON parsing failed for {company_name_for_error_msg}. Error: {e_json_primary}. Falling back to simple replace. Data: {children_str[:100]}")
        pass

    # 3. 尝试简单的JSON替换
    try:
        children_list = json.loads(children_str.replace("'", '"'))
        # log_and_print(f"调试: Simple JSON replace parsing successful for {company_name_for_error_msg}")
        return children_list
    except json.JSONDecodeError as e_json_fallback:
        log_and_print(f"警告: 无法解析公司 '{company_name_for_error_msg}' 的 children 字段。错误: {e_json_fallback}。字段内容 (前100字符): {children_str[:100]}")
        return []
    except Exception as e_general:
        log_and_print(f"警告: 解析公司 '{company_name_for_error_msg}' 的 children 字段时发生未知错误。错误: {e_general}。字段内容 (前100字符): {children_str[:100]}")
        return []


# --- 主逻辑 ---
def main():
    global output_file_handle
    try:
        # 打开文件用于写入
        output_file_handle = open(OUTPUT_TXT_FILE, 'w', encoding='utf-8')
        
        df = None
        read_successful = False
        for encoding in ENCODINGS_TO_TRY:
            try:
                log_and_print(f"尝试使用编码 {encoding} 读取CSV文件...")
                df = pd.read_csv(CSV_FILE_PATH, encoding=encoding, dtype=str, keep_default_na=False)
                log_and_print(f"成功使用编码 {encoding} 读取CSV文件。")
                read_successful = True
                break
            except UnicodeDecodeError:
                log_and_print(f"使用编码 {encoding} 读取失败。")
            except FileNotFoundError:
                log_and_print(f"错误: CSV文件未找到于路径 {CSV_FILE_PATH}")
                return
            except Exception as e:
                log_and_print(f"读取CSV时发生其他错误 (编码 {encoding}): {e}")

        if not read_successful or df is None:
            log_and_print(f"错误: 无法使用任何尝试的编码读取CSV文件。")
            return

        if df.empty:
            log_and_print(f"警告: CSV文件已读取但为空。")
            return

        log_and_print(f"\\n正在查找公司: '{TARGET_COMPANY_NAME}'...")

        if 'name' not in df.columns:
            log_and_print(f"错误: CSV文件中未找到 'name' 列。可用的列: {df.columns.tolist()}")
            return

        target_company_row = df[df['name'] == TARGET_COMPANY_NAME]

        if target_company_row.empty:
            log_and_print(f"在CSV文件中未找到名为 '{TARGET_COMPANY_NAME}' 的公司记录。")
            log_and_print(f"\\n正在检查 '{TARGET_COMPANY_NAME}' 是否作为其他公司的股东出现在 'children' 字段中...")
            found_as_child_in = []
            for index, row in df.iterrows():
                parent_company_name = row.get('name', f"行 {index} (无名称)")
                children_str = row.get('children', '')
                if children_str:
                    children_data = parse_children_string(children_str, parent_company_name)
                    for child in children_data:
                        if isinstance(child, dict) and child.get('name') == TARGET_COMPANY_NAME:
                            found_as_child_in.append({
                                "parent_company": parent_company_name,
                                "parent_eid": row.get('eid', '未知EID'),
                                "details_in_children": child
                            })
            if found_as_child_in:
                log_and_print(f"'{TARGET_COMPANY_NAME}' 被发现在以下公司的 'children' 字段中（即这些公司投资了它）：")
                for entry in found_as_child_in:
                    log_and_print(f"  - 作为股东被列于公司 '{entry['parent_company']}' (EID: {entry['parent_eid']}) 的记录中。")
                    log_and_print(f"    股东详情: {entry['details_in_children']}")
            else:
                log_and_print(f"'{TARGET_COMPANY_NAME}' 也未作为股东出现在任何其他公司的 'children' 字段中。")
            return

        if len(target_company_row) > 1:
            log_and_print(f"警告: 找到多个名为 '{TARGET_COMPANY_NAME}' 的记录。将使用第一条记录。")

        company_data = target_company_row.iloc[0]
        company_eid = company_data.get('eid', '未知EID')
        log_and_print(f"\\n找到公司: '{TARGET_COMPANY_NAME}' (EID: {company_eid})")

        children_str = company_data.get('children')
        if not children_str or children_str == 'nan' or children_str == '':
            log_and_print(f"公司 '{TARGET_COMPANY_NAME}' 的 'children' 字段为空或不存在。无法确定其直接股东。")
            return

        log_and_print(f"\\n解析其 'children' 字段以查找其直接股东...")
        shareholders = parse_children_string(children_str, TARGET_COMPANY_NAME)

        if not shareholders:
            log_and_print(f"解析后，公司 '{TARGET_COMPANY_NAME}' 的股东列表为空。")
        else:
            log_and_print(f"\\n'{TARGET_COMPANY_NAME}' (EID: {company_eid}) 的直接股东 (来自其 'children' 字段):")
            for i, shareholder in enumerate(shareholders):
                log_and_print(f"  股东 {i+1}:")
                if isinstance(shareholder, dict):
                    name = shareholder.get('name', '未知名称')
                    eid = shareholder.get('eid', '未知EID')
                    stype = shareholder.get('type', '未知类型')
                    percent = shareholder.get('percent', '未知比例')
                    sh_type = shareholder.get('sh_type', '未知股东类型')

                    log_and_print(f"    名称: {name}")
                    log_and_print(f"    EID : {eid}")
                    log_and_print(f"    类型: {stype}")
                    log_and_print(f"    持股比例: {percent}")
                    log_and_print(f"    股东类型(sh_type): {sh_type}")
                else:
                    log_and_print(f"    未知格式的股东数据: {shareholder}")
            log_and_print(f"\\n共找到 {len(shareholders)} 位直接股东。")

    finally:
        if output_file_handle:
            output_file_handle.close()
            log_and_print(f"\\n输出已保存到文件: {OUTPUT_TXT_FILE}") # 这个会打印到控制台，但文件已关闭

if __name__ == '__main__':
    main()