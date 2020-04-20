
### crawler for <https://rent.591.com.tw/>

### RESTful API
request:
    {
        "regionid": "1",
        "lessor_sex":"0",
        "sex": 0,
        "role_must_be_owner": 0,
        "linkman": "林先生",
        "tel": "09XXXXXXXX"
    }

response:
    {
        "message": "got X result.",
        "data": "{'_id': ObjectId('5e9c5f53e6eb1ed272a2c16c'), 'url': 'https://rent.591.com.tw/rent-detail-9019232.html', 'name': '新北市-中和區-中山路二段中和遠東捷運電梯全新優質套房', 'regionid': '3', 'linkman_role': '1', 'linkman': '曾小姐', 'tel': '0903177291', 'kind': '3', 'shape': '2', 'sex_requirement': '0', 'id': '2560230-9019232', 'price': '6,800 元/月', 'area': '6 坪', 'layout': '', 'update_time': 'Sun Apr 19 22:19:32 2020'}\n{'_id': ObjectId('5e9c5f53e6eb1ed272a2c16c'), 'url': 'https://rent.591.com.tw/rent-detail-9019232.html', 'name': '新北市-中和區-中山路二段中和遠東捷運電梯全新優質套房', 'regionid': '3', 'linkman_role': '1', 'linkman': '曾小姐', 'tel': '0903177291', 'kind': '3', 'shape': '2', 'sex_requirement': '0', 'id': '2560230-9019232', 'price': '6,800 元/月', 'area': '6 坪', 'layout': '', 'update_time': 'Sun Apr 19 22:19:32 2020'}"
    }
    
### usage

```
FLASK_ENV=development FLASK_APP=app.py pipenv run flask run -h "0.0.0.0" -p "8000" --debugger --reload
```


