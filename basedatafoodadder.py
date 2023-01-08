print('running')
import sqlite3

def estab_conn(db_name):
    conn = sqlite3.connect(f'{db_name}.db')
    return conn

def basedatafoodadder():
    client = myfitnesspal.Client()

    conn = estab_conn('basedata')
    cur = conn.cursor()
    x = True
    foods = []
    while x:
        food = input('food: ')
        if food == '':
            food2 = input('food2: ')
            if food2 == '':
                x = False
            elif str(food):
                foods.append(str(food))
        elif str(food):
            foods.append(str(food))
        else:
            pass

    for search in foods:
        try:
            items = client.get_food_search_results(search)
            for item in items:
                name = item.name
                if item.brand != ', ':
                    name += ', ' + item.brand
                i = input(f'{name} input?: ')
                if i == 'y':
                    name = 'food, ' + name
                    if '\'' in name:
                        name = name.replace('\'', '')
                    quantity, quantityunit = str(item.servings[0]).split(' x ')
                    if quantityunit == 'oz':
                        quantity = str(round(int(float(quantity) * 28.35),2))
                        quantityunit = 'g'

                    def retrieve_ccpf(item):
                        try:
                            cals = item.calories
                        except:
                            cals = '0.0'

                        try:
                            carbs = item.carbohydrates
                        except:
                            carbs = '0.0'

                        try:
                            protein = item.protein
                        except:
                            protein = '0.0'

                        try:
                            fat = item.fat
                        except:
                            fat = '0.0'

                        return cals, carbs, protein, fat
                    cals, carbs, protein, fat = retrieve_ccpf(item)
                    cpf = f'C: {carbs}g, P: {protein}g, F:{fat}g'
                    sql = 'INSERT INTO alldata VALUES(?,?,?,?,?)'
                    try:
                        cur.execute(sql,(name, quantity, quantityunit, cals, cpf))
                        print('succesful insert')
                        conn.commit()
                        results = cur.execute(f'SELECT * FROM alldata WHERE name LIKE \'%{name}%\'').fetchall()
                        print('results: ', results)
                        print('*' * 80)
                    except Exception as e:
                        print(e)
                elif i == 's':
                    break
        except Exception as e:
            print(e)
            print(f'no item with item id: {search}')
