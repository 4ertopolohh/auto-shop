import math
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from shop.models import Category, Product, ProductImage, SiteSettings, Integration

def illustration(kind, variant=0):
    # Original, locally generated technical product illustrations; no external hotlinks.
    metal='#c4c8bf'; dark='#424a40'; light='#e4e7de'; red='#b74634'
    drawing=''
    if kind=='brakes':
        drawing=f'<ellipse cx="170" cy="232" rx="103" ry="12" fill="#dcded6"/>'
        drawing+=f'<g transform="translate(153 135) rotate(-18) skewX(-7)"><circle r="92" fill="{dark}"/><circle cy="-6" r="90" fill="{metal}" stroke="#a4aa9c" stroke-width="2"/><circle cy="-6" r="76" fill="none" stroke="{light}" stroke-width="2"/><circle cy="-6" r="62" fill="none" stroke="#a5ab9e"/><circle cy="-6" r="35" fill="#929b89"/><circle cy="-6" r="22" fill="{dark}"/>'
        for j in range(24):
            a=j*math.pi/12
            x=math.cos(a)*68;y=math.sin(a)*68-6
            drawing+=f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.5" fill="#7b8473"/>'
        for j in range(5):
            a=j*math.pi/2.5
            drawing+=f'<circle cx="{math.cos(a)*28:.2f}" cy="{math.sin(a)*28-6:.2f}" r="4" fill="{dark}"/>'
        drawing+='</g><g transform="translate(220 133) rotate(15)"><path d="M-21-42h32q22 0 24 20v55q-3 15-19 15h-37z" fill="#41493e"/><path d="M-17-36h28q15 0 17 15v50q-1 12-14 13h-31z" fill="#626c57"/><path d="M-8-19h27v39H-8z" fill="#30382c"/><path d="M-14-31h15v5h-15m0 58h15v5h-15" stroke="#939c88" stroke-width="2"/></g>'
    elif kind=='filters':
        drawing=f'<ellipse cx="171" cy="232" rx="89" ry="12" fill="#dcded6"/><g transform="rotate(-14 150 140)"><path d="M92 69h106v130q-5 25-53 25t-53-25z" fill="#c59e55"/>'
        for j in range(19):
            x=96+j*5.5
            drawing+=f'<path d="M{x}74v126" stroke="{["#d7bb7e","#a4823f","#e7cc91"][j%3]}" stroke-width="3"/>'
        drawing+=f'<ellipse cx="145" cy="72" rx="53" ry="17" fill="{dark}"/><ellipse cx="145" cy="68" rx="53" ry="17" fill="#7b8470"/><ellipse cx="145" cy="68" rx="24" ry="9" fill="#333c2b"/><path d="M92 194q0 22 53 22t53-22v14q-5 25-53 25t-53-25z" fill="#3b4431"/></g><g transform="rotate(12 220 150)"><rect x="194" y="104" width="58" height="105" rx="14" fill="#6b775d"/><ellipse cx="223" cy="105" rx="29" ry="9" fill="#b2baa6"/><ellipse cx="223" cy="105" rx="10" ry="4" fill="#3d4932"/><text x="204" y="153" font-size="8" font-family="Arial" fill="white" transform="rotate(90 204 153)">OIL FILTER</text></g>'
    elif kind=='suspension':
        drawing='<ellipse cx="171" cy="238" rx="80" ry="10" fill="#dcded6"/><g transform="translate(169 142) rotate(28)">'
        drawing+=f'<rect x="-5" y="-101" width="10" height="183" rx="3" fill="{metal}"/><rect x="-16" y="-10" width="32" height="103" rx="5" fill="{dark}"/><rect x="-24" y="-69" width="48" height="8" rx="4" fill="#434c39"/><rect x="-27" y="8" width="54" height="8" rx="4" fill="#434c39"/>'
        for j in range(7):
            y=-60+j*10
            drawing+=f'<path d="M-22 {y}q44-12 44 0t-44 10" fill="none" stroke="#879578" stroke-width="6"/><path d="M-22 {y}q44-12 44 0" fill="none" stroke="#b4bea8" stroke-width="2"/>'
        drawing+=f'<circle cy="101" r="14" fill="{dark}"/><circle cy="101" r="6" fill="#d5dacd"/><path d="M-18-107h36l-4 12h-28z" fill="{dark}"/></g>'
    elif kind=='engine':
        drawing='<ellipse cx="168" cy="235" rx="98" ry="11" fill="#dcded6"/><g transform="translate(162 143) rotate(-22)">'
        drawing+=f'<path d="M-53-74h106v80q0 26-53 26T-53 6z" fill="#939c88"/><ellipse cy="-74" rx="53" ry="20" fill="#d6dbce" stroke="#8d9881"/><ellipse cy="-74" rx="40" ry="12" fill="#b4bda9"/><path d="M-54-57q54 22 108 0M-54-48q54 22 108 0m-108 9q54 22 108 0" stroke="#3f4936" stroke-width="4"/><path d="M-15 5h30l14 89q0 25-29 25t-29-25z" fill="#aab49d" stroke="#748368" stroke-width="2"/><circle cy="93" r="16" fill="#3d4933"/><circle cx="-34" cy="-3" r="13" fill="#57664a"/><path d="M-40-7h12v8h-12" stroke="#d0d7c7" stroke-width="2"/></g>'
    elif kind=='electrics':
        drawing='<ellipse cx="174" cy="230" rx="96" ry="11" fill="#dcded6"/>'
        for x,y,ang in [(125,124,-25),(209,150,15)]:
            drawing+=f'<g transform="translate({x} {y}) rotate({ang})"><rect x="-6" y="-80" width="12" height="30" rx="4" fill="#7c8772"/><rect x="-14" y="-54" width="28" height="63" rx="8" fill="#e6e9e1" stroke="#b7c0ae"/>'
            for j in range(6): drawing+=f'<path d="M-15 {-44+j*6}h30" stroke="#c9d0c1" stroke-width="3"/>'
            drawing+=f'<path d="m-21 10 10-8h22l10 8v18l-10 8h-22l-10-8z" fill="#9da892" stroke="#6f7d62"/><rect x="-12" y="36" width="24" height="42" fill="#acb79f"/>'
            for j in range(7): drawing+=f'<path d="m-12 {40+j*5}24-3" stroke="#647359" stroke-width="2"/>'
            drawing+='<path d="M-7 80v10H3V78" stroke="#68795b" stroke-width="4" fill="none"/></g>'
    else:
        drawing=f'<ellipse cx="170" cy="235" rx="83" ry="11" fill="#dcded6"/><g transform="rotate(-6 170 145)"><path d="M113 87q0-12 13-12h20V44h46v31h21l24 44v104q0 10-10 10H123q-10 0-10-10z" fill="#66745b" stroke="#4e5e43" stroke-width="2"/><path d="M197 91h9l14 25v23h-23z" fill="#eef0e7"/><path d="M146 43h46v18h-46z" fill="#343f2d"/><path d="M119 134h111v73H119z" fill="#ecebdc"/><path d="M119 134h111v18H119z" fill="{red}"/><text x="130" y="174" font-family="Arial" font-size="22" font-weight="700" fill="#34402d">5W-30</text><text x="130" y="194" font-family="Arial" font-size="9" fill="#647056">ENGINE OIL · 4L</text><path d="M123 220h102" stroke="#94a184" stroke-width="2"/></g>'
    transform = 'translate(320 0) scale(-1 1)' if variant else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 270"><rect width="320" height="270" fill="#f8f8f5"/><g transform="{transform}">{drawing}</g></svg>'

class Command(BaseCommand):
    help = 'Идемпотентное наполнение демонстрационного каталога'
    def handle(self, *args, **kwargs):
        SiteSettings.objects.get_or_create(pk=1)
        for name in ('cdek','yookassa'): Integration.objects.get_or_create(provider=name)
        cats=[('brakes','Тормозная система','Тормозные диски, колодки и компоненты'),('filters','Фильтры','Масляные, воздушные и салонные фильтры'),('suspension','Подвеска и рулевое','Амортизаторы, рычаги и опоры'),('engine','Двигатель','Компоненты двигателя и приводные ремни'),('electrics','Электрика','Свечи зажигания, катушки и датчики'),('oil','Масла и жидкости','Моторные масла и технические жидкости')]
        categories={}
        frontend=settings.BASE_DIR.parent/'frontend'/'public'/'images'; frontend.mkdir(parents=True,exist_ok=True)
        for position,(slug,name,description) in enumerate(cats):
            categories[slug],_=Category.objects.get_or_create(slug=slug, defaults={'name':name,'description':description,'illustration':slug,'position':position})
            (frontend/(slug+'.svg')).write_text(illustration(slug),encoding='utf-8')
        entries=[
            ('brakes','brembo-disc','Диск тормозной передний','BREMBO','09.7011.11',4250,5100,24,'Выбор для города',{'Диаметр':'256 мм','Толщина':'22 мм','Тип':'Вентилируемый','Комплект':'1 шт.','Покрытие':'Антикоррозионное'},'Тормозной диск с вентиляционными каналами для стабильного отвода тепла. Точная геометрия обеспечивает ровное торможение и предсказуемый отклик педали.'),
            ('filters','mann-oil','Фильтр масляный HU 719/7 x','MANN-FILTER','HU 719/7 x',890,1050,68,'Для вашего ТО',{'Высота':'141 мм','Наружный диаметр':'71 мм','Тип':'Фильтрующий элемент','Комплект':'С уплотнением'},'Сменный фильтрующий элемент задерживает частицы загрязнений и помогает поддерживать чистоту масла. В комплекте уплотнительное кольцо.'),
            ('electrics','ngk-spark','Свеча зажигания Iridium IX','NGK','BKR6EIX-11',1650,None,42,'',{'Материал электрода':'Иридий','Зазор':'1,1 мм','Резьба':'M14 × 1,25','Размер ключа':'16 мм'},'Тонкий иридиевый электрод обеспечивает стабильное искрообразование. Для уверенного запуска и ровной работы двигателя. Цена за одну свечу.'),
            ('suspension','kyb-shock','Амортизатор передний Excel-G','KYB','333741',6480,7200,16,'',{'Сторона':'Передний правый','Тип':'Газомасляный','Конструкция':'Двухтрубный','Серия':'Excel-G'},'Газомасляный амортизатор для повседневной эксплуатации. Помогает сохранять контакт колёс с дорогой и контролировать колебания кузова.'),
            ('oil','motul-oil','Масло моторное 8100 X-clean 5W-30','MOTUL','102782',5790,6400,35,'',{'Вязкость':'5W-30','Объём':'4 л','Основа':'Синтетическая','Класс':'ACEA C3'},'Синтетическое моторное масло для современных бензиновых и дизельных двигателей. Перед применением проверьте требуемые допуски производителя автомобиля.'),
            ('engine','mahle-piston','Поршень двигателя в комплекте','MAHLE','030 82 00',8750,None,8,'',{'Диаметр':'76,5 мм','Материал':'Алюминиевый сплав','Комплект':'Поршень, палец, кольца'},'Поршневой комплект для ремонта двигателя. Геометрию, размерную группу и применимость необходимо сверять по технической документации.'),
            ('filters','bosch-air','Фильтр воздушный двигателя','BOSCH','1 457 433 532',1290,None,55,'',{'Высота':'57 мм','Длина':'270 мм','Ширина':'188 мм'},'Фильтр для очистки поступающего в двигатель воздуха. Поддерживает достаточный поток и задерживает пыль при повседневной эксплуатации.'),
            ('brakes','ate-pads','Колодки тормозные передние','ATE','13.0460-7117.2',3890,4500,28,'',{'Сторона':'Передняя ось','Комплект':'4 шт.','Датчик износа':'В комплекте'},'Комплект колодок передней оси. Сбалансированный состав фрикционной смеси для предсказуемого торможения в городском цикле.'),
            ('electrics','bosch-plug','Свеча зажигания Double Platinum','BOSCH','0 242 236 571',1150,None,31,'',{'Электрод':'Платина','Резьба':'M14 × 1,25','Зазор':'1,0 мм'},'Свеча с платиновыми электродами. Подбирайте по коду двигателя, требуемому калильному числу и каталожной применимости.'),
            ('suspension','sachs-shock','Амортизатор задний Super Touring','SACHS','313 029',5290,None,12,'',{'Сторона':'Задняя ось','Тип':'Газовый','Серия':'Super Touring'},'Задний амортизатор с настройкой для ежедневных поездок. Для равномерной работы подвески рекомендуем замену парами на одной оси.'),
            ('filters','mann-cabin','Фильтр салонный угольный','MANN-FILTER','CUK 26 009',1890,2150,0,'',{'Тип':'Угольный','Длина':'254 мм','Ширина':'235 мм'},'Салонный фильтр с активированным углём задерживает пыль и помогает уменьшить проникновение запахов. Сверьте размеры и направление установки.'),
            ('oil','liquimoly-oil','Масло моторное Top Tec 4200','LIQUI MOLY','8973',7490,None,22,'',{'Вязкость':'5W-30','Объём':'5 л','Основа':'HC-синтетическая','Класс':'ACEA C3'},'Моторное масло для межсервисного обслуживания. Интервал замены и допуски определяются производителем автомобиля и условиями эксплуатации.'),
            ('engine','mahle-piston-pro','Поршневой комплект Original','MAHLE','028 91 00',9250,None,6,'',{'Диаметр':'82,5 мм','Комплект':'С поршневыми кольцами'},'Комплект для восстановления цилиндропоршневой группы. Установку выполняют после измерения цилиндров и проверки ремонтного размера.'),
            ('brakes','brembo-rear-disc','Диск тормозной задний','BREMBO','08.9502.11',3650,None,18,'',{'Диаметр':'253 мм','Тип':'Сплошной','Комплект':'1 шт.'},'Диск задней оси с защитным покрытием. Подбирайте по тормозной системе и комплектации автомобиля, а не только по модели.'),
            ('suspension','kyb-shock-rear','Амортизатор задний Excel-G','KYB','343328',4150,None,21,'',{'Сторона':'Задняя ось','Тип':'Газомасляный','Серия':'Excel-G'},'Амортизатор для сбалансированной работы задней подвески. Проверьте совместимость по году выпуска и типу кузова.'),
            ('electrics','ngk-plug-standard','Свеча зажигания V-Line','NGK','BKR6EK',650,None,90,'',{'Материал электрода':'Никель','Электроды массы':'2','Размер ключа':'16 мм'},'Свеча с двумя электродами массы для регламентного обслуживания. Перед установкой сверяйте момент затяжки по руководству производителя.'),
            ('filters','mahle-oil','Фильтр масляный Original','MAHLE','OX 188 D',790,None,44,'',{'Высота':'105 мм','Тип':'Картридж','Комплект':'С уплотнением'},'Масляный фильтрующий элемент для плановой замены. Уплотнительные элементы входят в комплект.'),
            ('oil','motul-coolant','Жидкость охлаждающая Inugel','MOTUL','102924',1850,None,27,'',{'Объём':'5 л','Тип':'Готовый состав','Температура':'До −35 °C'},'Охлаждающая жидкость для поддержания рабочего температурного режима. Не смешивайте составы без проверки совместимости допусков.'),
        ]
        vehicles=[{'make':'Volkswagen','model':'Polo','years':'2015–2022'},{'make':'Škoda','model':'Rapid','years':'2014–2022'},{'make':'Hyundai','model':'Solaris','years':'2017–2023'},{'make':'Kia','model':'Rio','years':'2017–2023'},{'make':'Renault','model':'Logan','years':'2014–2022'},{'make':'Toyota','model':'Corolla','years':'2013–2019'}]
        for i,(cat,slug,name,brand,sku,price,old,stock,badge,specs,description) in enumerate(entries):
            p,created=Product.objects.get_or_create(sku=sku,defaults={'slug':slug,'name':name,'brand':brand,'category':categories[cat],'price':price,'old_price':old,'stock':stock,'badge':badge,'specs':specs,'description':description,'compatibility':vehicles[:2] if i%3==0 else vehicles[2:4] if i%3==1 else vehicles[4:], 'oem':['1J0615301M','03C115561H','101905617C'][i%3], 'weight':850 if cat!='brakes' else 4500,'featured':i<4})
            if created:
                for n in range(3):
                    image=ProductImage(product=p,position=n,alt=f'{name} — {"общий вид" if n==0 else "детали и конструкция"}')
                    image.image.save(f'{slug}-{n}.svg',ContentFile(illustration(cat,n%2).encode()))
        self.stdout.write(self.style.SUCCESS(f'Каталог готов: {Category.objects.count()} категорий, {Product.objects.count()} товаров.'))
