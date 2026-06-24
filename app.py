import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

CSV_FILE = "mandy_ledger.csv"

# 自動讀取或初始化資料檔案
if os.path.exists(CSV_FILE):
    try:
        df_existing = pd.read_csv(CSV_FILE)
        df_existing['金額'] = pd.to_numeric(df_existing['金額'], errors='coerce').fillna(0).astype(int)
        df_existing['分類'] = df_existing['分類'].fillna('其他').astype(str)
        st.session_state.ledger = df_existing
    except:
        st.session_state.ledger = pd.DataFrame(columns=['日期', '月份', '品項', '金額', '分類'])
else:
    st.session_state.ledger = pd.DataFrame(columns=['日期', '月份', '品項', '金額', '分類'])

# 網頁大標題
st.title("💬 Mandy 的對話記帳 App")
st.write("請在下方輸入你的花費，例如：「買保養品1000」或「500吃」")

user_input = st.text_input("輸入記帳內容...", key="input_text")

if st.button("送出記帳") and user_input:
    amount = 0
    category = "其他"
    today_str = datetime.today().strftime('%Y-%m-%d')
    month_str = datetime.today().strftime('%Y-%m')
    
    numbers = re.findall(r'\d+', user_input)
    if numbers:
        amount = int(numbers[0])
    
    if any(x in user_input for x in ["交通", "車", "捷運", "公車", "計程車", "油錢", "高鐵", "火車", "悠遊卡"]):
        category = "交通運輸"
    elif any(x in user_input for x in ["保養品", "化妝品", "衣服", "玩", "看電影", "買", "娛樂", "包包", "鞋子"]):
        category = "美妝娛樂"
    elif any(x in user_input for x in ["吃", "飯", "喝", "晚餐", "午餐", "早餐", "食品", "點心", "飲料", "咖啡"]):
        category = "餐飲食品"
    elif any(x in user_input for x in ["房租", "水電", "瓦斯", "網路", "生活用品", "衛生紙", "日常", "家"]):
        category = "居家生活"
    elif any(x in user_input for x in ["看醫生", "醫", "藥", "保健食品", "診所", "口罩"]):
        category = "醫療保健"

    new_data = pd.DataFrame([{'日期': today_str, '月份': month_str, '品項': user_input, '金額': int(amount), '分類': category}])
    st.session_state.ledger = pd.concat([st.session_state.ledger, new_data], ignore_index=True)
    st.session_state.ledger.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    st.success(f"🎉 記帳成功！已自動歸類到【{category}】，金額：{amount} 元")

# --- 下半部：分析儀表板 ---
st.markdown("---")
st.header("📊 Mandy 的月結算與趨勢分析")

if not st.session_state.ledger.empty:
    st.session_state.ledger['金額'] = pd.to_numeric(st.session_state.ledger['金額'], errors='coerce').fillna(0).astype(int)
    st.session_state.ledger['分類'] = st.session_state.ledger['分類'].fillna('其他').astype(str)
    
    # 1. 歷史趨勢圖（使用 Streamlit 內建折線圖，免下載套件）
    st.subheader("📈 歷史每月總消費變化趨勢")
    monthly_trend = st.session_state.ledger.groupby('月份')['金額'].sum()
    if not monthly_trend.empty:
        st.line_chart(monthly_trend)
    
    st.markdown("---")
    
    # 2. 月份選擇與結算
    all_months = sorted(st.session_state.ledger['月份'].dropna().unique(), reverse=True)
    if all_months:
        selected_month = st.selectbox("📆 請選擇你想查看的結算月份：", all_months)
        month_df = st.session_state.ledger[st.session_state.ledger['月份'] == selected_month]
        
        st.subheader(f"📋 {selected_month} 月份詳細紀錄")
        st.dataframe(month_df[['日期', '品項', '金額', '分類']], use_container_width=True)
        
        category_totals = month_df.groupby('分類')['金額'].sum()
        
        # 3. 消費比例圖（使用 Streamlit 內建長條圖，完美適應手機排版）
        if category_totals.sum() > 0:
            st.subheader(f"📊 {selected_month} 各類別花費圖表")
            st.bar_chart(category_totals)
        
        # 4. 文字統計
        st.subheader(f"💡 {selected_month} 各分類花費統計")
        st.write(f"💰 **該月總花費：** {category_totals.sum()} 元")
        for cat in ["餐飲食品", "美妝娛樂", "居家生活", "交通運輸", "醫療保健", "其他"]:
            st.write(f"▪️ {cat}：`{category_totals.get(cat, 0)}` 元")
else:
    st.info("目前還沒有任何記帳資料，快在上方輸入第一筆花費吧！")
