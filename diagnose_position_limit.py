"""
檢查程式運行狀態和持倉限制
用於診斷為何顯示"已達總持倉上限"
"""
import shioaji as sj
from tabulate import tabulate
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# 與 SinoPac-new.py 相同的設定
g_bolTestMode = True  # 測試模式
API_KEY = os.getenv("SINOPAC_API_KEY", "")
SECRET_KEY = os.getenv("SINOPAC_SECRET_KEY", "")
CA_PATH = os.getenv("SINOPAC_CA_PATH", "C:/ekey/551/J120420374/S/Sinopac.pfx")
CA_PASSWORD = os.getenv("SINOPAC_CA_PASSWORD", "J120420374")

MAX_TOTAL_POSITION = 300  # 與 SinoPac-new.py 相同

def check_positions_status(api, mode_name: str):
    """檢查持倉狀態"""
    print("\n" + "="*100)
    print(f"📊 {mode_name} - 持倉狀態檢查")
    print("="*100)
    
    try:
        all_positions = api.list_positions(api.futopt_account)
        
        if not all_positions:
            print("✓ 目前無持倉")
            print(f"距離上限: {MAX_TOTAL_POSITION} 口可用")
            return 0
        
        # 計算總持倉
        total_position = sum(abs(pos.quantity) for pos in all_positions)
        
        # 依商品分組
        grouped = {}
        for pos in all_positions:
            prefix = pos.code[:2]
            if prefix not in grouped:
                try:
                    name = api.Contracts.Futures[pos.code].name
                except:
                    name = pos.code
                grouped[prefix] = {
                    'name': name,
                    'quantity': 0
                }
            grouped[prefix]['quantity'] += abs(pos.quantity)
        
        # 顯示彙總
        summary_data = []
        for prefix in sorted(grouped.keys()):
            data = grouped[prefix]
            summary_data.append([
                prefix,
                data['name'],
                data['quantity'],
                f"{(data['quantity']/MAX_TOTAL_POSITION)*100:.1f}%"
            ])
        
        headers = ['代碼', '商品名稱', '口數', '佔比']
        table = tabulate(summary_data, headers=headers, tablefmt='grid')
        print(table)
        
        # 顯示總計
        print("\n" + "-"*100)
        print(f"📈 總持倉: {total_position} 口 / {MAX_TOTAL_POSITION} 口上限")
        print(f"   使用率: {(total_position/MAX_TOTAL_POSITION)*100:.1f}%")
        print(f"   剩餘可用: {MAX_TOTAL_POSITION - total_position} 口")
        
        if total_position >= MAX_TOTAL_POSITION:
            print(f"   ⚠️  已達上限！")
        elif total_position >= MAX_TOTAL_POSITION * 0.9:
            print(f"   ⚠️  接近上限！")
        else:
            print(f"   ✅ 仍有額度")
        
        print("="*100)
        
        return total_position
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    print("\n" + "="*100)
    print("🔍 SinoPac-new 持倉狀態診斷工具")
    print("="*100)
    print(f"\n設定:")
    print(f"  測試模式: {'✓ 模擬環境' if g_bolTestMode else '✗ 正式環境'}")
    print(f"  總持倉上限: {MAX_TOTAL_POSITION} 口")
    
    # 檢查模擬環境
    print("\n" + "="*100)
    print("1️⃣  檢查模擬環境（與 SinoPac-new.py 相同設定）")
    print("="*100)
    
    api_sim = sj.Shioaji(simulation=True)
    try:
        if API_KEY and SECRET_KEY and API_KEY != "YOUR_API_KEY":
            accounts = api_sim.login(
                api_key=API_KEY,
                secret_key=SECRET_KEY,
                contracts_cb=lambda security_type: None
            )
        else:
            accounts = api_sim.login("PAPIUSER07", "2317")
        
        print("✅ 模擬環境登入成功")
        sim_total = check_positions_status(api_sim, "模擬環境")
        
        api_sim.logout()
        
    except Exception as e:
        print(f"❌ 模擬環境錯誤: {e}")
        sim_total = 0
    
    # 檢查正式環境
    print("\n" + "="*100)
    print("2️⃣  檢查正式環境（實際帳戶）")
    print("="*100)
    
    if not API_KEY or not SECRET_KEY or API_KEY == "YOUR_API_KEY":
        print("⚠️  未設定 API Key，跳過正式環境檢查")
        real_total = 0
    else:
        api_real = sj.Shioaji(simulation=False)
        try:
            accounts = api_real.login(
                api_key=API_KEY,
                secret_key=SECRET_KEY,
                contracts_cb=lambda security_type: None
            )
            print("✅ 正式環境登入成功")
            
            if os.path.exists(CA_PATH):
                try:
                    api_real.activate_ca(ca_path=CA_PATH, ca_passwd=CA_PASSWORD)
                    print("✅ 憑證啟動成功")
                except:
                    print("⚠️  憑證啟動失敗")
            
            real_total = check_positions_status(api_real, "正式環境")
            
            api_real.logout()
            
        except Exception as e:
            print(f"❌ 正式環境錯誤: {e}")
            real_total = 0
    
    # 總結
    print("\n" + "="*100)
    print("📋 診斷總結")
    print("="*100)
    print(f"模擬環境持倉: {sim_total} 口")
    print(f"正式環境持倉: {real_total} 口")
    print(f"總持倉上限: {MAX_TOTAL_POSITION} 口")
    
    if sim_total >= MAX_TOTAL_POSITION:
        print(f"\n⚠️  模擬環境已達上限 - 這就是 SinoPac-new 顯示訊息的原因！")
    elif real_total >= MAX_TOTAL_POSITION:
        print(f"\n⚠️  正式環境已達上限")
    else:
        print(f"\n✅ 兩個環境都未達上限")
    
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
