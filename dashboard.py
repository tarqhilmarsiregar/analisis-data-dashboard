import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

rfm_data_df = pd.read_csv("rfm_data.csv")
category_data_df = pd.read_csv("category_data.csv")
payments_data_df = pd.read_csv("payments_data.csv")

datetime_columns = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]

for column in datetime_columns:
    rfm_data_df[column] = pd.to_datetime(rfm_data_df[column])

for column in datetime_columns:
    category_data_df[column] = pd.to_datetime(category_data_df[column])

for column in datetime_columns:
    payments_data_df[column] = pd.to_datetime(payments_data_df[column])

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

rfm_data_df["order_purchase_date_only"] = rfm_data_df["order_purchase_timestamp"].dt.date
rfm_data_df["order_purchase_date_only"] = pd.to_datetime(rfm_data_df["order_purchase_date_only"])

rfm_data_df.sort_values(by="order_purchase_date_only", inplace=True)
rfm_data_df.reset_index(inplace=True)

min_date = rfm_data_df["order_purchase_date_only"].min()
max_date = rfm_data_df["order_purchase_date_only"].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://gdm-catalog-fmapi-prod.imgix.net/ProductLogo/7fa56dfd-9a71-4486-9633-e531e0725f69.jpeg?w=100&q=50")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

rfm_data_filtered_df = rfm_data_df[(rfm_data_df["order_purchase_timestamp"] >= str(start_date)) & 
                (rfm_data_df["order_purchase_timestamp"] <= str(end_date))]

category_data_filtered_df = category_data_df[(category_data_df["order_purchase_timestamp"] >= str(start_date)) & 
                (category_data_df["order_purchase_timestamp"] <= str(end_date))]

payments_data_filtered_df = payments_data_df[(payments_data_df["order_purchase_timestamp"] >= str(start_date)) & 
                (payments_data_df["order_purchase_timestamp"] <= str(end_date))]

rfm_df = create_rfm_df(rfm_data_filtered_df)

st.header('Brazilian E-Commerce Dashboard :sparkles:')

st.subheader('Top 5 Product Categories with the Most Orders')

top_5_byproduct_df = category_data_filtered_df.groupby(by="product_category_name").order_id.nunique().reset_index()
top_5_byproduct_df.rename(columns={
    "order_id": "product_category_count"
}, inplace=True)

fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12, 6))

sns.barplot(
    y="product_category_count", 
    x="product_category_name",
    data=top_5_byproduct_df.sort_values(by="product_category_count", ascending=False).head(5),
    color='blue'
)
plt.title("Top 5 Product Categories with the Most Orders", loc="center", fontsize=14)
plt.ylabel("Number of Orders", fontsize=12)
plt.xlabel("Product Categories", fontsize=12)
st.pyplot(fig)

st.subheader('Distribution of Payment Methods Based on Number of Orders')
orders_payments_counts = payments_data_filtered_df.groupby(by="payment_type").order_id.nunique().sort_values(ascending=False)

fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12, 6))

sns.barplot(
    x=orders_payments_counts.values, 
    y=orders_payments_counts.index, 
    orient="h", 
    color="blue"
)

plt.title("Distribution of Payment Methods Based on Number of Orders", fontsize=14)
plt.xlabel("Number of Orders", fontsize=12)
plt.ylabel("Payment Methods", fontsize=12)

plt.grid(axis="x", linestyle="-", alpha=0.5)
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)
ax[0].set_xticklabels(ax[0].get_xticklabels(), rotation=45, ha="right")

sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)
ax[1].set_xticklabels(ax[0].get_xticklabels(), rotation=45, ha="right")

sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)
ax[2].set_xticklabels(ax[0].get_xticklabels(), rotation=45, ha="right")

st.pyplot(fig)

st.caption('Copyright (c) Brazilian E-Commerce 2025')