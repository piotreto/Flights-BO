from typing_extensions import final
import streamlit as st
import datetime
import reader


# TODO
#get airports
NETWORK = reader.Reader.read_flights("../../data/flights.csv")
AIRPORTS = NETWORK.airports

st.title("Flights Finder")
start_airport = st.selectbox("Choose starting airport", AIRPORTS)
destination_airport = st.selectbox("Choose destination airport", AIRPORTS)

def handle_find():
    start_date_time = datetime.datetime.combine(start_date, start_time)
    final_date_time = datetime.datetime.combine(final_date, final_time)

    if(start_airport == destination_airport):
        st.warning("Wrong airports")

    if(final_date_time <= start_date_time):
        st.warning("Wrong time!")


col1, col2 = st.columns(2)
start_date = col1.date_input("Date From")
print(type(start_date))
start_time = col2.time_input("Hour From")
print(type(start_time))
col1, col2 = st.columns(2)
final_date = col1.date_input("Date To")
final_time = col2.time_input("Hour To")

st.button("Find", on_click= handle_find)
