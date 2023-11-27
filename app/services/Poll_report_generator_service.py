import pandas as pd
from sqlalchemy import create_engine
from app.config import settings

def map_status(status):
        return 1.0 if status == "active" else 0.0

def empty_output(store_id):
    return pd.DataFrame([{
        'store_id': store_id,
        'uptime_last_hour': 0,
        'uptime_last_day': 0, 
        'uptime_last_week': 0, 
        'downtime_last_hour': 60,
        'downtime_last_day': 24,
        'downtime_last_week': 168
    }])

class Poll_report_generator:
    def __init__(self) -> None:
        self.report_cols = ['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week', 'downtime_last_hour', 'downtime_last_day', 'downtime_last_week']
        pass

    def load_data(self):
        engine = create_engine(settings.psql_url)
        self.poll_data_df = pd.read_sql_query('select * from "poll_data_table"',con=engine).sort_values(by='timestamp_utc')
        self.store_timing_data_df = pd.read_sql_query('select * from "store_timing_data_table"',con=engine)
        self.tz_data_df = pd.read_sql_query('select * from "tz_data_table"',con=engine)
        pass

    def get_store_timing_df(self, store_timing_data_df, tz_data_df):

        store_timing_data_df['start_time_local'] = pd.to_datetime(store_timing_data_df['start_time_local'], format='%H:%M:%S')
        store_timing_data_df['end_time_local'] = pd.to_datetime(store_timing_data_df['end_time_local'], format='%H:%M:%S')

        merged_df = pd.merge(store_timing_data_df, tz_data_df, on='store_id')

        merged_df['start_time_utc'] = merged_df.apply(lambda row: row['start_time_local'].tz_localize(row['timezone_str']).tz_convert('UTC'), axis=1)
        merged_df['end_time_utc'] = merged_df.apply(lambda row: row['end_time_local'].tz_localize(row['timezone_str']).tz_convert('UTC'), axis=1)

        merged_df['start_time_local'] = merged_df['start_time_local'].dt.tz_localize('UTC')
        merged_df['end_time_local'] = merged_df['end_time_local'].dt.tz_localize('UTC')

        merged_df['delta'] = (merged_df['start_time_utc'] - merged_df['start_time_local']).dt.days

        merged_df['day_utc'] = merged_df['day'] + merged_df['delta']

        result_df = merged_df.drop(['start_time_local', 'end_time_local', 'timezone_str', 'delta', 'day'], axis=1)

        result_df['start_time_utc'] = result_df['start_time_utc'].dt.time
        result_df['end_time_utc'] = result_df['end_time_utc'].dt.time

        return result_df
    

    def generate_status_summary(self, df, store_id):
        last_hour = df['status'].iloc[-1]

        last_day = df['status'].loc[df.index.normalize() == df.index[-1].normalize()].values

        last_week = df['status'].loc[df.index >= (df.index[-1] - pd.DateOffset(weeks=1))].values

        return pd.DataFrame([{
            'store_id': store_id,
            'uptime_last_hour': last_hour,
            'uptime_last_day': sum(last_day == 1), 
            'uptime_last_week': sum(last_week == 1), 
            'downtime_last_hour': 60 - last_hour,
            'downtime_last_day': sum(last_day == 0),
            'downtime_last_week': sum(last_week == 0)
        }])
    
    def filter_timings(self, df, store_id, store_timing_df):
        store_info = store_timing_df[store_timing_df['store_id'] == store_id][['start_time_utc', 'end_time_utc', 'day_utc']]
        skip_flag = 0
        if(store_info.empty):
            return df
        
        df["day_utc"] = df["timestamp_utc"].dt.dayofweek
        return df[
                (df["day_utc"].isin(store_info['day_utc'].values)) &
                (df["timestamp_utc"].dt.time >= store_info['start_time_utc'].values[0]) &
                (df["timestamp_utc"].dt.time <= store_info['end_time_utc'].values[0])
            ]
    

    def fill_missing(self, df, df_resampled):
        def majority_status(series):
            return series.mode().iloc[0] if not series.empty else None

        result = df_resampled['status'].rolling(window=2).apply(majority_status)
        result_df = pd.DataFrame({'status': result})

        result_df = result_df.iloc[1:]

        if result_df.empty:
            raise Exception('empty')  
        
        result_df['status'].iloc[0] = map_status(df['status'].iloc[0])
        return result_df


    def resample(self, df):
        df.set_index('timestamp_utc', inplace=True)

        df_resampled = df.resample('H').ffill()

        df_resampled["status"] = df_resampled["status"].apply(map_status)

        return df_resampled

    def process_subset(self, df, store_id, store_timing_df):
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], format="%Y-%m-%d %H:%M:%S.%f %Z", errors="coerce").fillna(pd.to_datetime(df["timestamp_utc"], format="%Y-%m-%d %H:%M:%S %Z", errors="coerce"))    

        df = self.filter_timings(df, store_id, store_timing_df)
        
        if df.empty:
            return empty_output(store_id)

        df_resampled = self.resample(df)

        if df.empty:
            return empty_output(store_id)

        df_final = self.fill_missing(df, df_resampled)

        if df.empty:
            return empty_output(store_id)
        
        return self.generate_status_summary(df_final, store_id)


    def compute_report(self, store_id, store_timing_df):
        try:
            tmpdf = self.poll_data_df[self.poll_data_df["store_id"] == store_id].drop("store_id", axis=1)
            return self.process_subset(tmpdf, store_id, store_timing_df)
        except Exception:
            pass

    def generate_csv(self, filename):
        
        result_df = pd.DataFrame(columns=self.report_cols)

        self.load_data()
        store_timing_df = self.get_store_timing_df(self.store_timing_data_df, self.tz_data_df)

        for store_id in self.poll_data_df['store_id'].unique():
            summary = self.compute_report(store_id, store_timing_df)
            result_df =  pd.concat([summary, result_df], ignore_index=True)
        
        print(result_df.size)

        result_df.to_csv(filename, encoding='utf-8', index=False)