### crawler for <https://rent.591.com.tw/>

### RESTful API
request:
    {
        "regionid": "1",
        "lessor_sex":"0",
        "sex": 0,
        "role_type": 0,
        "linkman": "林先生",
        "tel": "09XXXXXXXX"
    }

response:
    { 
        "message": "got X result.",
        "data": "{'_id': ObjectId('5e9c6a1fe6eb1ed272a2c3e6'), 'url': 'https://rent.591.com.tw/rent-detail-9041798.html', 'name': '台北市-萬華區-長順街107巷全新裝潢、近捷運站、近河濱運動公園', 'regionid': '1', 'linkman_role': '1', 'linkman': '林先生', 'tel': '0933706556', 'kind': '3', 'shape': '1', 'sex_requirement': '2', 'id': '1665946-9041798', 'price': '9,500 元/月', 'area': '8 坪', 'layout': '', 'update_time': 'Mon Apr 20 16:45:02 2020'}\n{'_id': ObjectId('5e9c6a5de6eb1ed272a2cbcf'), 'url': 'https://rent.591.com.tw/rent-detail-9078080.html', 'name': '台北市-中山區-民生東路二段115巷捷運行天宮舒適精緻套房', 'regionid': '1', 'linkman_role': '1', 'linkman': '林先生', 'tel': '0922391867', 'kind': '2', 'shape': '1', 'sex_requirement': '0', 'id': '462656-9078080', 'price': '9,000 元/月', 'area': '6 坪', 'layout': '', 'update_time': 'Sun Apr 19 22:10:02 2020'}"
    }
    
### usage

```
FLASK_ENV=development FLASK_APP=app.py pipenv run flask run -h "0.0.0.0" -p "8000" --debugger --reload
```
