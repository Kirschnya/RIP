from django.shortcuts import render
from test_data import TECHS
from test_data import ZAKAZ_DATA

def index(request):
    zakaz_name = request.GET.get('tech')
    items = ZAKAZ_DATA[0]
    count_techs = len(items['techs'])
    if zakaz_name:
        techs=[]
        for tech in TECHS:
            if zakaz_name.lower() in tech['name'].lower():
                techs.append(tech)
        return render(request, 'index.html', {
            "techs": techs,
            'query': zakaz_name,
            "zakaz": 1,
            "count": count_techs
            })
    
    else:
        return render(request, 'index.html', {"techs": TECHS, "zakaz": 1, "count": count_techs})

def tech(request, tech_id):
    for item in TECHS:
        if item['id'] == tech_id:
            tech = item
            break
    return render(request, 'tech.html', {"tech": tech})

def get_techs_by_ids(tech_ids):
    return [tech for tech in TECHS if tech['id'] in tech_ids]

def zakaz(request, zakaz_id):
    tech_data = next((zakaz for zakaz in ZAKAZ_DATA if zakaz['id'] == zakaz_id), None)
    
    if tech_data:
        zakaz_items = get_techs_by_ids([i[0] for i in tech_data['techs']])
        for i in range(len(zakaz_items)):
            zakaz_items[i]["get"] = tech_data['techs'][i][1]

        context = {
            'zakaz_name': tech_data['zakaz'],
            'zakaz_items':  zakaz_items,
        }
        return render(request, 'zakaz.html', context)
