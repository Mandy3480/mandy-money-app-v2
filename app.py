import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

CSV_FILE = "mandy_ledger.csv"

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
    
    if any(x in user_input for x in ["運動", "休閒", "瑜珈", "健身", "跑步", "馬拉松", "羽球", "球", "網球", "游泳", "打", "爬山", "登山", "露營", "按摩", "跳舞", "舞蹈", "路跑"]):
        category = "運動休閒"
    elif any(x in user_input for x in ["交通", "車", "捷運", "公車", "計程車", "油錢", "高鐵", "火車", "悠遊卡"]):
        category = "交通運輸"
    elif any(x in user_input for x in ["保養品", "化妝品", "衣服", "玩", "看電影", "買", "娛樂", "包包", "鞋子", "美甲", "美睫", "逛街"]):
        category = "美妝娛樂"
    elif any(x in user_input for x in ["吃", "飯", "喝", "晚餐", "午餐", "早餐", "食品", "點心", "飲料", "咖啡", "餅乾", "零食", "蛋糕", "麵包", "水果", "手搖"]):
        category = "餐飲食品"
    elif any(x in user_input for x in ["房租", "水電", "瓦斯", "網路", "生活用品", "衛生紙", "日常", "家"]):
        category = "居家生活"
    elif any(x in user_input for x in ["看醫生", "醫", "藥", "保健食品", "診所", "口罩"]):
        category = "醫療保健"

    new_data = pd.DataFrame([{'日期': today_str, '月份': month_str, '品項': user_input, '金額': int(amount), '分類': category}])
    st.session_state.ledger = pd.concat([st.session_state.ledger, new_data], ignore_index=True)
    st.session_state.ledger['分類'] = st.session_state.ledger['分類'].replace('運動修行', '運動休閒')
    st.session_file = st.session_state.ledger.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    st.success(f"🎉 記帳成功！已自動歸類到【{category}】，金額：{amount} 元")

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
        
        # 💡 【全新大升級：改用下拉選單刪除，防止打錯字】
        st.markdown("⚙️ **資料管理（刪除打錯的紀錄）**")
        
        # 建立選項清單，格式為："[序號] 品項名稱"
        delete_options = {f"[{idx}] {row['日期']} - {row['品項']}": idx for idx, row in month_df.iterrows()}
        
        if delete_options:
            selected_delete_label = st.selectbox("請選擇你想刪除的紀錄：", list(delete_options.keys()))
            actual_delete_index = delete_options[selected_delete_label]
            
            if st.button("🗑️ 確認刪除所選紀錄"):
                st.session_state.ledger = st.session_state.ledger.drop(actual_delete_index)
                st.session_state.ledger.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
                st.warning(f"已成功刪除：{selected_delete_label}！")
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
