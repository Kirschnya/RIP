from django.shortcuts import render
from test_data import technikaS
from test_data import ZAKAZ_DATA

def index(request):
    zakaz_name = request.GET.get('technika')
    items = ZAKAZ_DATA[0]
    count_technikas = len(items['technikas'])
    if zakaz_name:
        technikas=[]
        for technika in technikaS:
            if zakaz_name.lower() in technika['name'].lower():
                technikas.append(technika)
        return render(request, 'index.html', {
            "technikas": technikas,
            'query': zakaz_name,
            "zakaz": 1,
            "count": count_technikas
            })
    
    else:
        return render(request, 'index.html', {"technikas": technikaS, "zakaz": 1, "count": count_technikas})

def technika(request, technika_id):
    for item in technikaS:
        if item['id'] == technika_id:
            technika = item
            break
    return render(request, 'technika.html', {"technika": technika})

def get_technikas_by_ids(technika_ids):
    return [technika for technika in technikaS if technika['id'] in technika_ids]

def zakaz(request, zakaz_id):
    technika_data = next((zakaz for zakaz in ZAKAZ_DATA if zakaz['id'] == zakaz_id), None)
    
    if technika_data:
        zakaz_items = get_technikas_by_ids([i[0] for i in technika_data['technikas']])
        for i in range(len(zakaz_items)):
            zakaz_items[i]["get"] = technika_data['technikas'][i][1]

        context = {
            'zakaz_name': technika_data['zakaz'],
            'zakaz_items':  zakaz_items,
            'zakaz_author': technika_data['author'],
            'zakaz_date': technika_data['date'],
        }
        return render(request, 'zakaz.html', context)
