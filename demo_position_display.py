"""
顯示模擬庫存的漂亮表格 - 示範版本
無需實際登入，使用模擬數據展示表格格式
"""
from tabulate import tabulate
from datetime import datetime
from typing import List, Dict


def generate_sample_positions() -> List[Dict]:
    """生成模擬持倉數據"""
    sample_data = [
        {
            '序號': 1,
            '商品代碼': 'HSFL2',
            '商品名稱': '長榮航',
            '方向': '買進',
            '數量': 3,
            '成本價': '45.20',
            '現價': '46.50',
            '損益': '+390.00',
            '損益%': '+2.87%'
        },
        {
            '序號': 2,
            '商品代碼': 'HCFA3',
            '商品名稱': '宏達電',
            '方向': '賣出',
            '數量': 2,
            '成本價': '85.60',
            '現價': '84.20',
            '損益': '+280.00',
            '損益%': '+1.64%'
        },
        {
            '序號': 3,
            '商品代碼': 'CSFL2',
            '商品名稱': '華新',
            '方向': '買進',
            '數量': 5,
            '成本價': '32.80',
            '現價': '31.50',
            '損益': '-650.00',
            '損益%': '-3.96%'
        },
        {
            '序號': 4,
            '商品代碼': 'CDFL2',
            '商品名稱': '台積電',
            '方向': '買進',
            '數量': 1,
            '成本價': '580.00',
            '現價': '595.00',
            '損益': '+1500.00',
            '損益%': '+2.59%'
        },
        {
            '序號': 5,
            '商品代碼': 'CHFA3',
            '商品名稱': '友達',
            '方向': '賣出',
            '數量': 4,
            '成本價': '18.50',
            '現價': '18.90',
            '損益': '-160.00',
            '損益%': '-2.16%'
        },
    ]
    return sample_data


def display_positions_table(positions: List[Dict]):
    """顯示持倉表格"""
    print("\n" + "="*120)
    print(f"📊 持倉一覽表 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120)
    
    if not positions:
        print("\n目前無持倉\n")
        return
    
    # 使用 tabulate 生成漂亮的表格
    headers = positions[0].keys()
    rows = [pos.values() for pos in positions]
    
    # grid 格式 - 有完整邊框
    table = tabulate(rows, headers=headers, tablefmt='grid', stralign='center', numalign='center')
    print(table)
    
    # 計算總損益
    total_pnl = sum(float(pos['損益'].replace('+', '').replace(',', '')) for pos in positions)
    total_quantity = sum(pos['數量'] for pos in positions)
    
    print("\n" + "="*120)
    print(f"📈 統計資訊")
    print(f"   總持倉口數: {total_quantity} 口")
    print(f"   總損益: {total_pnl:+,.2f} 元")
    
    if total_pnl > 0:
        print(f"   狀態: ✅ 獲利中")
    elif total_pnl < 0:
        print(f"   狀態: ⚠️  虧損中")
    else:
        print(f"   狀態: ➖ 持平")
    
    print("="*120 + "\n")


def display_margin_info():
    """顯示模擬保證金資訊"""
    print("\n" + "="*120)
    print("💰 保證金資訊")
    print("="*120)
    
    # 模擬數據
    info_data = [
        ['可用保證金', '1,250,000.00', '元'],
        ['權益總值', '1,850,000.00', '元'],
        ['未平倉損益', '+1,360.00', '元'],
        ['佔用保證金', '600,000.00', '元'],
        ['維持保證金', '480,000.00', '元'],
    ]
    
    table = tabulate(info_data, headers=['項目', '金額', '單位'], tablefmt='grid', stralign='left', numalign='right')
    print(table)
    print("="*120 + "\n")


def display_by_product(positions: List[Dict]):
    """依商品分組顯示"""
    print("\n" + "="*120)
    print(f"📋 依商品分組顯示 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120)
    
    # 依商品代碼前兩碼分組
    grouped = {}
    for pos in positions:
        code_prefix = pos['商品代碼'][:2]
        if code_prefix not in grouped:
            grouped[code_prefix] = []
        grouped[code_prefix].append(pos)
    
    # 顯示各組
    for prefix, group in grouped.items():
        print(f"\n📌 {prefix} 系列 ({group[0]['商品名稱']})")
        print("-" * 120)
        
        headers = group[0].keys()
        rows = [pos.values() for pos in group]
        
        table = tabulate(rows, headers=headers, tablefmt='simple', stralign='center', numalign='center')
        print(table)
        
        # 小計
        group_pnl = sum(float(pos['損益'].replace('+', '').replace(',', '')) for pos in group)
        group_qty = sum(pos['數量'] for pos in group)
        print(f"\n   小計: {group_qty} 口 | 損益: {group_pnl:+,.2f} 元")
    
    print("\n" + "="*120 + "\n")


def display_simple_format(positions: List[Dict]):
    """簡單格式顯示"""
    print("\n" + "="*120)
    print(f"📝 簡易格式 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120 + "\n")
    
    headers = positions[0].keys()
    rows = [pos.values() for pos in positions]
    
    # simple 格式 - 簡潔
    table = tabulate(rows, headers=headers, tablefmt='simple')
    print(table)
    print("\n" + "="*120 + "\n")


def display_fancy_format(positions: List[Dict]):
    """精美格式顯示"""
    print("\n" + "="*120)
    print(f"✨ 精美格式 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120 + "\n")
    
    headers = positions[0].keys()
    rows = [pos.values() for pos in positions]
    
    # fancy_grid 格式 - 使用雙線框
    table = tabulate(rows, headers=headers, tablefmt='fancy_grid', stralign='center', numalign='center')
    print(table)
    print("\n" + "="*120 + "\n")


def display_markdown_format(positions: List[Dict]):
    """Markdown 格式顯示（方便複製到文件）"""
    print("\n" + "="*120)
    print(f"📄 Markdown 格式 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120 + "\n")
    
    headers = positions[0].keys()
    rows = [pos.values() for pos in positions]
    
    # pipe 格式 - Markdown 表格
    table = tabulate(rows, headers=headers, tablefmt='pipe', stralign='center', numalign='center')
    print(table)
    print("\n" + "="*120 + "\n")


def main():
    """主程式"""
    print("\n" + "="*120)
    print("🎨 模擬庫存表格顯示 - 示範程式")
    print("="*120)
    print("\n本程式展示多種表格格式，使用模擬數據")
    
    # 生成模擬數據
    positions = generate_sample_positions()
    
    # 顯示選單
    while True:
        print("\n" + "="*120)
        print("📋 選單")
        print("="*120)
        print("1. 標準格式 (Grid)")
        print("2. 簡易格式 (Simple)")
        print("3. 精美格式 (Fancy Grid)")
        print("4. Markdown 格式")
        print("5. 顯示保證金資訊")
        print("6. 依商品分組顯示")
        print("7. 全部顯示")
        print("0. 離開")
        print("="*120)
        
        choice = input("\n請選擇功能 (0-7): ").strip()
        
        if choice == '1':
            display_positions_table(positions)
        elif choice == '2':
            display_simple_format(positions)
        elif choice == '3':
            display_fancy_format(positions)
        elif choice == '4':
            display_markdown_format(positions)
        elif choice == '5':
            display_margin_info()
        elif choice == '6':
            display_by_product(positions)
        elif choice == '7':
            # 全部顯示
            display_positions_table(positions)
            display_margin_info()
            display_by_product(positions)
            print("\n其他格式：")
            display_simple_format(positions)
            display_fancy_format(positions)
            display_markdown_format(positions)
        elif choice == '0':
            print("\n👋 再見！")
            break
        else:
            print("\n❌ 無效的選擇，請重新輸入")


if __name__ == "__main__":
    main()
