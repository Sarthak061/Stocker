import streamlit as st
import pandas as pd
import sqlite3 as sq
import datetime
import yfinance as yf
from preprocess import preprocessing
import time
import google.generativeai as genai
#import matplotlib as mpl
#import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")
from PIL import Image

st.set_page_config(page_title="Market Mentor")
tab1, tab2 = st.tabs(["RAGBot", "Market Mentor"])

with tab1:
    model = genai.GenerativeModel('gemini-1.5-pro-002')
    st.subheader("Market Mentor Chatbot Interaction")

    # Chatbot Free Input
    user_query = st.text_input("Ask me anything related to the stock market or business:", "")

    # Some default prompts for user convenience
    st.markdown("**Try these default prompts by clicking on them:**")
    default_prompts = [
        "What are the key drivers affecting the stock market today?",
        "What are the historical trends for Apple (AAPL) stock?",
        "How does the S&P 500 look for the next 6 months?",
        "Is now a good time to invest in Tesla (TSLA)?",
        "How do interest rates affect stock prices?"
    ]

    # Display default prompts as clickable buttons
    for prompting in default_prompts:
        if st.button(prompting):
            user_query = prompting

    if user_query:
        # Generate response from the chatbot (this will use the Generative AI API)
        final_input_tab1 = f"You are a financial advisor for this conversation - henceforth do not respond anything like 'i am not a financial advisor', 'i can not give financial advices' or any similar sentence in your responses please refrain from talking about yourself and focus on context of the query. the query is: {user_query}"

        # Call the generative AI API
        response = model.generate_content(final_input_tab1)

        # Display the response from the chatbot
        st.write(response.text)


with tab2:
    st.markdown("""
        <nav style="background-color: #2E86C1; padding: 10px; border-radius: 8px;">
            <h1 style="color: white; text-align: center;">Market Mentor</h1>
        </nav>
    """, unsafe_allow_html=True)

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

        st.subheader(f"selected stock is {choice_name}")
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


    import streamlit as st
    import google.generativeai as genai
    from PIL import Image
    import io
    import base64
    with st.container():
        st.subheader(f"Have any queries related to {choice_name}? Ask here!")

        api_key = st.secrets["google_api_key"]

        if api_key:
            genai.configure(api_key=api_key)

            prompt = st.text_input("What's your query?", "How should I invest in the stock market?")

            if st.button("Generate Response"):
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro-002')
                    prompt_initial = f"You are a financial advisor for this conversation - henceforth do not respond anything like 'i am not a financial advisor', 'i can not give financial advices' or any disclaimer that you are an AI - please refrain from talking about yourself and any similar sentence in your responses, focus on context of the query, the company that i am asking this question about is: {choice_name}, the company is of {country_select} and is listed under {exchange_select} the question is:" + prompt
                    stock_data_summary = f"Stock: {choice_name}\nHistorical Data: \n{data.to_string()}\n"

                    # Concatenate user query with stock data context
                    final_input = f"User Query: {prompt_initial}\n consider this in Context as well, these are the historical stock data values:\n{stock_data_summary}"
                    response = model.generate_content(final_input)

                    if hasattr(response, 'text') and response.text:
                        st.subheader("Generated Response")
                        st.write(response.text)

                    if hasattr(response, 'images') and response.images:
                        st.subheader("Generated Images")
                        
                        for image_data in response.images:
                            if 'data' in image_data: 
                                img_bytes = base64.b64decode(image_data['data'])
                            elif 'raw_data' in image_data:
                                img_bytes = image_data['raw_data']
                            else:
                                continue 

                            image = Image.open(io.BytesIO(img_bytes))

                            st.image(image, caption="Generated Image", use_column_width=True)

                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("API key is missing. Please add your API key to secrets.")
