SELECT *, avg(TG) OVER (partition by station_id) FROM daily_weather

-- Rank each day by temperature within each station (highest = rank 1)
SELECT *, Rank() OVER (partition BY station_id order by TG desc) from daily_weather

-- Show each day's temperature alongside the previous day's temperature
select date, TG, lag(TG) over (partition by station_id order by date) as pre_temp from daily_weather

-- Calculate the daily temperature change (today minus yesterday)
with cte as (select date, TG, lag(TG) over (partition by station_id order by date) as pre_temp from daily_weather)
select date, TG - pre_temp as temp_change from cte 

-- Show each day's temperature and the station's overall average in the same row
select *, avg(TG) over (partition by station_id) from daily_weather

--  7-day rolling average temperature per station
select avg(TG) over (partition by station_id order by date rows between 6 preceding and current row) from daily_weather
