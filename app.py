import streamlit as st
import pandas as pd
import re
import os
import requests
import base64
from datetime import datetime

CSV_FILE = "mandy_ledger.csv"
REPO_OWNER = "Mandy3480"
REPO_NAME = "mandy-money-app-v2"

# 嘗試從 Streamlit Secrets 讀取鑰匙
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")

# 💡 從 GitHub 自動同步下載最新檔案，防止雲端睡眠導致資料遺失
def fetch_csv_from_github():
    if not GITHUB_TOKEN:
        return
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{CSV_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()
        file_content = base64.b64decode(content['content'])
        with open(CSV_FILE, "wb") as f:
            f.write(file_content)

# 💡 記帳完畢後，自動把最新的 CSV 檔案用力推回 GitHub 永久保存
def upload_csv_to_github():
    if not GITHUB_TOKEN or not os.path.exists(CSV_FILE):
        return
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{CSV_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # 必須先拿到舊檔案的 sha 識別碼才能更新
    res_get = requests.get(url, headers=headers)
    sha = res_get.json().get('sha', '') if res_get.status_code == 200 else None
    
    with open(CSV_FILE, "rb") as f:
        encoded_content = base64.b64encode(f.read()).decode('utf-8')
        
    data = {
        "message": f"🤖 自動同步記帳資料: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": encoded_content
    }
    if sha:
        data["sha"] = sha
        
    requests.put(url, headers=headers, json=data)

# 初始化：開網頁時先去 GitHub 撈最新正確的檔案下來
if 'initialized' not in st.session_state:
    fetch_csv_from_github()
    st.session_state.initialized = True

if os.path.exists(CSV_FILE):
    try:
        df_existing = pd.read_csv(CSV_FILE)
        df_existing['金額'] = pd.to_numeric(df_existing['金額'], errors='coerce').fillna(0).astype(int)
        df_existing['分類'] = df_existing['分類'].fillna('其他').astype(str)
        df_existing['分類'] = df_existing['分類'].replace('運動修行', '運動休閒')
        st.session_state.ledger = df_existing
    except:
        st.session_state.ledger = pd.DataFrame(columns=['日期', '月份', '品項', '金額', '分類'])
else:
    st.session_state.ledger = pd.DataFrame(columns=['日期', '月份', '品項', '金額', '分類'])

st.title("💬 Mandy 的對話記帳 App")
st.write("請在下方輸入你的花費，例如：「買保養品1000」或「500吃」")

def clear_text():
    st.session_state.user_text = st.session_state.widget_text
    st.session_state.widget_text = ""

st.text_input("輸入記帳內容...", key="widget_text", on_change=clear_text)

if "user_text" in st.session_state and st.session_state.user_text:
    user_input = st.session_state.user_text
    st.session_state.user_text = ""
    
    amount = 0
    category = "其他"
    today_str = datetime.today().strftime('%Y-%m-%d')
    month_str = datetime.today().strftime('%Y-%m')
    
    numbers = re.findall(r'\d+', user_input)
    if numbers:
        amount = int(numbers[0])
    
    # 💡 終極生活智慧分類規則（吃喝大補帖：新增水、星巴克、手搖飲）
    if any(x in user_input for x in ["運動", "休閒", "瑜珈", "健身", "跑步", "馬拉松", "羽球", "球", "网球", "網球", "游泳", "打", "爬山", "登山", "露營", "按摩", "跳舞", "舞蹈", "路跑", "皮拉提斯"]):
        category = "運動休閒"
    elif any(x in user_input for x in ["交通", "車", "捷運", "公車", "計程車", "油錢", "高鐵", "火車", "悠遊卡"]):
        category = "交通運輸"
    elif any(x in user_input for x in ["保養品", "化妝品", "衣服", "玩", "看電影", "買", "娛樂", "包包", "鞋子", "美甲", "美睫", "逛街", "洗頭", "剪頭髮", "護髮", "染髮", "燙髮", "洗髮", "剪髮", "燙頭", "染頭", "屈臣氏", "康是美"]):
        category = "美妝娛樂"
    elif any(x in user_input for x in ["吃", "飯", "喝", "晚餐", "午餐", "早餐", "中餐", "大餐", "宵夜", "聚餐", "買菜", "食材", "食品", "點心", "飲料", "咖啡", "餅乾", "零食", "蛋糕", "麵包", "水果", "手搖", "手搖飲", "星巴克", "水"]):
        category = "餐飲食品"
    elif any(x in user_input for x in ["房租", "水電", "瓦斯", "網路", "生活用品", "衛生紙", "日常", "家"]):
        category = "居家生活"
    elif any(x in user_input for x in ["看醫生", "醫", "藥", "保健食品", "診所", "口罩", "醫美", "肉毒", "雷射", "皮秒"]):
        category = "醫療保健"

    new_data = pd.DataFrame([{'日期': today_str, '月份': month_str, '品項': user_input, '金額': int(amount), '分類': category}])
    st.session_state.ledger = pd.concat([st.session_state.ledger, new_data], ignore_index=True)
    st.session_state.ledger['分類'] = st.session_state.ledger['分類'].replace('運動修行', '運動休閒')
    st.session_state.ledger.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    
    # 🚀 自動即時上傳回 GitHub 保險箱
    upload_csv_to_github()
    st.success(f"🎉 記帳成功且已安全備份至 GitHub！已歸類到【{category}】，金額：{amount} 元")

st.markdown("---")
st.header("📊 Mandy 的月結算與趨勢分析")

if not st.session_state.ledger.empty:
    st.session_state.ledger['金額'] = pd.to_numeric(st.session_state.ledger['金額'], errors='coerce').fillna(0).astype(int)
    st.session_state.ledger['分類'] = st.session_state.ledger['分類'].fillna('其他').astype(str)
    
    st.subheader("📈 歷史每月總消費變化趨勢")
    monthly_trend = st.session_state.ledger.groupby('月份')['金額'].sum()
    if not monthly_trend.empty:
        st.line_chart(monthly_trend)
    
    st.markdown("---")
    
    all_months = sorted(st.session_state.ledger['月份'].dropna().unique(), reverse=True)
    if all_months:
        selected_month = st.selectbox("📆 請選擇你想查看的結算月份：", all_months)
        month_df = st.session_state.ledger[st.session_state.ledger['月份'] == selected_month]
        
        st.subheader(f"📋 {selected_month} 月份詳細紀錄")
        st.dataframe(month_df[['日期', '品項', '金額', '分類']], use_container_width=True)
        
        # 下拉選單刪除功能
        st.markdown("⚙️ **資料管理（刪除打錯的紀錄）**")
        delete_options = {f"[{idx}] {row['日期']} - {row['品項']}": idx for idx, row in month_df.iterrows()}
        if delete_options:
            selected_delete_label = st.selectbox("請選擇你想刪除的紀錄：", list(delete_options.keys()))
            actual_delete_index = delete_options[selected_delete_label]
            if st.button("🗑️ 確認刪除所選紀錄"):
                st.session_state.ledger = st.session_state.ledger.drop(actual_delete_index)
                st.session_state.ledger.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                
                # 🚀 刪除資料也要即時同步回 GitHub
                upload_csv_to_github()
                st.warning(f"已成功刪除並同步：{selected_delete_label}！")
                st.rerun()
        else:
            st.info("該月份目前沒有可以刪除的紀錄。")

        st.markdown("---")
        category_totals = month_df.groupby('分類')['金額'].sum()
        
        if category_totals.sum() > 0:
            st.subheader(f"📊 {selected_month} 各類別花費圖表")
            st.bar_chart(category_totals)
        
        st.subheader(f"💡 {selected_month} 各分類花費統計")
        st.write(f"💰 **該月總花費：** {category_totals.sum()} 元")
        
        for cat in ["餐飲食品", "美妝娛樂", "居家生活", "交通運輸", "醫療保健", "運動休閒", "其他"]:
            st.write(f"▪️ {cat}：`{category_totals.get(cat, 0)}` 元")
else:
    st.info("目前還沒有任何記帳資料，快在上方輸入第一筆花費吧！")
