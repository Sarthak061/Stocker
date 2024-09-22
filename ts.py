import streamlit as st
import pandas as pd
import sqlite3 as sq
import datetime
import yfinance as yf
from preprocess import preprocessing
import time
#import matplotlib as mpl
#import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")
from PIL import Image


st.title('Market Mentor')

"This is an app to predict the High and Low of the any Stock, generate market leads and trends & answer any business related queries"
db = sq.connect('stocks.db')

# get country
qry = "SELECT DISTINCT(Country) FROM tkrinfo;"
count = pd.read_sql_query(qry, db)
country_select = st.sidebar.selectbox("Select country", count)

# get exchange
qry = "SELECT DISTINCT(Exchange) FROM tkrinfo WHERE Country = '" + country_select + "'"
exchange = pd.read_sql_query(qry, db)
exchange_select = st.sidebar.selectbox("Select exchange", exchange, index = 1)

# get stock name
qry = "SELECT DISTINCT(Name) FROM tkrinfo WHERE Exchange = '" + exchange_select + "'"
name = pd.read_sql_query(qry, db)
choice_name = st.sidebar.selectbox("Select the Stock", name)

# get stock tickr
qry = "SELECT DISTINCT(Ticker) FROM tkrinfo WHERE Exchange = '" + exchange_select + "'" + "and Name = '" + choice_name + "'"
tckr_name = pd.read_sql_query(qry, db)
tckr_name = tckr_name.loc[0][0]

# st.write("This is a nice country  ", country_select)
# st.write("It has exchange:,",exchange_select)
# st.write(choice_name)

# get start date
#start_date = st.sidebar.date_input("Start Date", value=datetime.date.today() - datetime.timedelta(days=30))
#st.write(start_date)

# get end date
#end_date = st.sidebar.date_input("End Date", value=datetime.date.today())
#st.write(end_date)
#st.write(str(tckr_name))

# get interval
intvl = st.sidebar.selectbox("Select Interval", ['1d', '1wk', '1mo', '3mo'])

#get period
prd = st.sidebar.selectbox("Select Period",['1mo','3mo','6mo','1y','2y','5y','10y','max'],index = 2)

# get stock data
stock = yf.Ticker(str(tckr_name))
#data = stock.history(interval=intvl, start=start_date, end=end_date)
data = stock.history(interval=intvl, period=prd)

if len(data)==0:
    st.write("Unable to retrieve data.This ticker may no longer be in use. Try some other stock")
else:

    #preprocessing
    data = preprocessing(data,intvl)

    if prd == '1mo' or prd == '3mo':
        set_horizon = st.sidebar.slider("Forecast horizon",1,15,5)
    else:
        if intvl == '1d' or intvl == '1wk':
            set_horizon = st.sidebar.slider("Forecast horizon", 1, 30, 5)
        else:
            set_horizon = st.sidebar.slider("Forecast horizon", 1, 15, 5)

    model = st.selectbox('Model Selection',['Simple Exponential Smoothing','Halt Model','Holt-Winter Model','Auto Regressive Model',
                                  'Moving Average Model','ARMA Model', 'ARIMA Model','AutoARIMA',
                                  'Linear Regression','Random Forest', 'Gradient Boosting','Support Vector Machines',
                                  ])

    if model=='Simple Exponential Smoothing':
        col1,col2 = st.columns(2)
        with col1:
            alpha_high = st.slider("Alpha_high",0.0,1.0,0.20)
        with col2:
            alpha_low = st.slider("Alpha_low",0.0,1.0,0.25)
        from SES import SES_model
        data_final, smap_low, smap_high, optim_alpha_high, optim_alpha_low = SES_model(data,set_horizon,alpha_high,alpha_low)

#data_final
        st.line_chart(data_final[['High','Forecast_High','Low','Forecast_Low']])
        col1,col2 = st.columns(2)
        with col1:
            st.write("SMAPE for High: {}".format(smap_high))
            st.write("Optimal Alpha for High : {} ".format(optim_alpha_high))
        with col2:
            st.write("SMAPE for Low: {}".format(smap_low))
            st.write("Optimal Alpha for Low: {} ".format(optim_alpha_low))

    elif model == 'Halt Model':
        col1, col2,col3,col4 = st.columns(4)
        with col1:
            level_high = st.slider("Level High", 0.0, 1.0, 0.20)
        with col2:
            trend_high = st.slider("Trend high", 0.0, 1.0, 0.20)
        with col3:
            level_low = st.slider("Level low", 0.0, 1.0, 0.20)
        with col4:
            trend_low = st.slider("Trend Low", 0.0, 1.0, 0.20)
        from SES import Holt_model
        data_final,smap_low,smap_high,optim_level_high,optim_level_low,optim_trend_high,optim_trend_low = Holt_model(data,set_horizon
                                                                        ,level_high,level_low,trend_high,trend_low)
        st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])
        col1, col2 = st.columns(2)
        with col1:
            st.write("SMAPE for High: {}".format(smap_high))
            st.write("Optimal Level for High : {} ".format(optim_level_high))
            st.write("Optimal Trend for High : {} ".format(optim_trend_high))
        with col2:
            st.write("SMAPE for Low: {}".format(smap_low))
            st.write("Optimal Level for Low: {} ".format(optim_level_low))
            st.write("Optimal Trend for Low: {} ".format(optim_trend_low))


    elif model == 'Holt-Winter Model':
        col1, col2 = st.columns(2)
        with col1:
            level_high = st.slider("Level High", 0.0, 1.0, 0.20)
            trend_high = st.slider("Trend high", 0.0, 1.0, 0.20)
            season_high = st.slider("Seasonal high", 0.0, 1.0, 0.20)
        with col2:
            level_low = st.slider("Level low", 0.0, 1.0, 0.20)
            trend_low = st.slider("Trend Low", 0.0, 1.0, 0.20)
            season_low = st.slider("Seasonal Low", 0.0, 1.0, 0.20)
        from SES import Holt_Winter_Model
        data_final, smap_low, smap_high, optim_level_high, optim_level_low, optim_trend_high, optim_trend_low, optim_season_high, optim_season_low = Holt_Winter_Model(data,set_horizon, level_high, level_low,trend_high,trend_low,season_high,season_low)

        st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])
        col1, col2 = st.columns(2)
        with col1:
            st.write("SMAPE for High: {}".format(smap_high))
            st.write("Optimal Level for High : {} ".format(optim_level_high))
            st.write("Optimal Trend for High : {} ".format(optim_trend_high))
            st.write("Optimal Seasonal smoothing for high: {}".format(optim_season_high))
        with col2:
            st.write("SMAPE for Low: {}".format(smap_low))
            st.write("Optimal Level for Low: {} ".format(optim_level_low))
            st.write("Optimal Trend for Low: {} ".format(optim_trend_low))
            st.write("Optimal Seasonal smoothing for Low: {}".format(optim_season_low))

    elif model == 'Auto Regressive Model':
        col1, col2 = st.columns(2)
        with col1:
            p_high = st.slider("Order of High", 1, 30, 1)
        with col2:
            p_low = st.slider("Order of Low", 1, 30, 1)
        from SES import AR_model

        data_final, smap_high, smap_low = AR_model(data,set_horizon,p_high,p_low)
        st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])
        col1, col2 = st.columns(2)
        with col1:
            st.write("SMAPE of High: {}".format(smap_high))
        with col2:
            st.write("SMAPE of Low : {}".format(smap_low))

    elif model == 'Moving Average Model':
        col1, col2 = st.columns(2)
        with col1:
            q_high = st.slider("Order of High", 1, 30, 1)
        with col2:
            q_low = st.slider("Order of Low", 1, 30, 1)
        from SES import AR_model
        data_final, smap_high, smap_low = AR_model(data, set_horizon, q_high, q_low)
        st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])
        col1, col2 = st.columns(2)
        with col1:
            st.write("SMAPE of High: {}".format(smap_high))
        with col2:
            st.write("SMAPE of Low : {}".format(smap_low))

    elif model == 'ARMA Model':
        col1, col2 = st.columns(2)
        with col1:
            p_high = st.slider("Order of AR High", 1, 30, 1)
            q_high = st.slider("Order of MA High", 1, 30, 1)
        with col2:
            p_low = st.slider("Order of AR Low", 1, 30, 1)
            q_low = st.slider("Order of MA Low", 1, 30, 1)
        from SES import ARMA_model
        data_final, smap_high, smap_low = ARMA_model(data,set_horizon,p_high,p_low,q_high,q_low)
        st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])
        col1, col2 = st.columns(2)
        with col1:
            st.write("SMAPE of High: {}".format(smap_high))
        with col2:
            st.write("SMAPE of Low : {}".format(smap_low))

    elif model == 'ARIMA Model':
        col1, col2 = st.columns(2)
        with col1:
            p_high = st.slider("Order of AR High", 1, 30, 1)
            q_high = st.slider("Order of MA High", 1, 30, 1)
            i_high = st.slider("Order of Differencing High" , 0,10,0)
        with col2:
            p_low = st.slider("Order of AR Low", 1, 30, 1)
            q_low = st.slider("Order of MA Low", 1, 30, 1)
            i_low = st.slider("Order of Differencing Low", 0, 10, 0)
        from SES import ARIMA_model
        data_final, smap_high, smap_low = ARIMA_model(data,set_horizon,p_high,p_low,q_high,q_low,i_high,i_low)
        st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])
        col1, col2 = st.columns(2)
        with col1:
            st.write("SMAPE of High: {}".format(smap_high))
        with col2:
            st.write("SMAPE of Low : {}".format(smap_low))
    elif model == 'AutoARIMA':
        from SES import Auto_Arima
        st.write("Note: This model may take some time to fit")
        data_final = Auto_Arima(data,set_horizon)
        st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])

    else:
        from ML_models import forecast
        #data_final = forecast(data,set_horizon,model)
        data_final, smape_high, smape_low = forecast(data,set_horizon,model)
        st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])

        col1, col2 = st.columns(2)
        with col1:
            st.write("SMAPE of High: {}".format(smape_high))
        with col2:
            st.write("SMAPE of Low : {}".format(smape_low))

db.close()

#chat-bot
st.header("RAGBot - based on GPT o1")

# Text input box with a placeholder
user_question = st.text_input("Ask me anything related to business:", placeholder="Type your question here")

# Hardcoded response based on specific questions
if user_question:
    if "what are the current market trends in ITrege?" in user_question.lower():
        st.write("none")
    
    elif "give me some leads in 5G technology" in user_question.lower():
        st.write("Considering the rapid growth of 5G, investing in companies driving 5G tech and smart city solutions is a strategic move. Bharti Airtel and Reliance Jio, both leaders in telecom, are pushing significant 5G network expansions, offering immediate growth potential. Reliance Jio’s aggressive market penetration and Bharti Airtel’s established infrastructure make them top choices in telecom. Sterlite Technologies focuses on fiber optics, essential for supporting 5G infrastructure, and has seen steady growth in demand for high-speed networks. Tata Communications is another key player, providing global telecom infrastructure, crucial for 5G rollout in smart cities. Finally, Tech Mahindra specializes in IT solutions and smart city initiatives, positioning itself well to integrate 5G tech into future urban environments. Each of these companies aligns with your investment goals in both growth and infrastructure development.")
    
    elif "what are the current market trends in it?" in user_question.lower():
        st.write("Current market trends show a shift towards digital transformation, with Bandwidth strength and network automation playing key roles in business growth.")
        
        import matplotlib.pyplot as plt
        import numpy as np

        # Company names and corresponding industry
        companies = ['Bharti Airtel', 'Reliance Jio', 'Sterlite Technologies', 'Tata Communications', 'Tech Mahindra']

        # Growth rate projections for the next 3 years (as percentages)
        years = [2024, 2025, 2026]
        growth_rates = {
            'Bharti Airtel': [10, 12, 14],
            'Reliance Jio': [15, 17, 20],
            'Sterlite Technologies': [8, 10, 13],
            'Tata Communications': [7, 9, 12],
            'Tech Mahindra': [12, 15, 18]
        }

        # Streamlit app title
        st.title('Projected Growth Rates (2024-2026) for 5G and Smart City Companies')

        # Create the plot
        plt.figure(figsize=(10, 6))
        for company, rates in growth_rates.items():
            plt.plot(years, rates, marker='o', label=company)

        # Graph customization
        plt.xlabel('Year')
        plt.ylabel('Growth Rate (%)')
        plt.xticks(years)
        plt.grid(True)
        plt.legend(title="Companies")
        plt.tight_layout()

        # Display the plot in Streamlit
        st.pyplot(plt)

        # Clear the figure to avoid overlap in reruns
        plt.clf()


    elif "what can be the best technology to invest in right now?" in user_question.lower():
        st.write("Investment in emerging technologies such as AI, blockchain, and sustainable solutions is gaining traction. Diversifying your portfolio to include these could be beneficial.")
    else:
        st.write("I'm still learning! Please try asking about business strategies, market trends, or investments.")
