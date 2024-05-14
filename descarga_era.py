import cdsapi
import netCDF4 as nc
import math
import pandas as pd
from datetime import datetime
from datetime import timedelta

print("Este programa entrega un archivo con la informacion meteorologica para se utilizado en Cell2Fire")
print("La fecha y hora están en uso horario UTC")
print("La ubicación debe ser entregada en coordenadas geográficas")


#Modelo de combustible
print("Qué tipo de de modelo de combustible usara: ")
sc = int(input("Ingrese 1 para kitral o 2 para Scott&Burgan: "))
if sc == 1:
    print("Ha elegido la opción Kitral")
elif sc == 2:
    print("Ha elegido la opción Scott&Burgan")
    FS = int(input("Ingrese el tipo de fireScenario (Live & Dead Fuel Moisture Content Scenario [1=dry..4=moist]): "))
    if FS >= 1 and FS <= 4:
        print("FireScenario= " + str(FS))
    else:
        exit("Opción no valida")
else:
    exit("Opción no valida")


#Fecha, hora y lugar
print("Ingrese la fecha de inicio como se solicita a continuacion")
# fecha
a=int(input("Ingrese el año en formato AAAA (ejem: 2020): "))
m=int(input("Ingrese el mes como número entero (ejem: 10): "))
d=int(input("Ingrese en día del mes: "))
h=int(input("Ingrese la hora como número entero, desde las 0 a las 23 horas: "))
#numero de horas
nh=int(input("Cuantas horas debe durar el scenario: "))
#lat, lon
lat=float(input("ingrese la latitud en coordenadas geograficas (ejem: -33.0): "))
lon=float(input("Ingrese la longitud en coordenas geograficas (ejem: -71.0): "))
#dif=0.25

##########################
#######FUNCIONES##########
##########################

#funcion que calcula el angulo de cell2fire a partir de las componentes
def angulo_c2f(u,v):
    if v<0:
        theta=round(math.degrees( math.atan(u/v))+180,1)
    elif v==0 and u<0:
        theta= 270
    elif v>0 and u<0:
        theta= round(math.degrees(math.atan(u/v))+360,1)
    elif v>0 and u>=0:
        theta= round(math.degrees(math.atan(u/v)),1)
    elif v==0 and u>0:
        theta= 90
    else:
        theta=math.nan
    return theta

def magnitud(u,v):
    m= math.sqrt(u*u+v*v)
    return m

def mps_kmph(mps):
    kmph=mps*3.6
    kmph=round(kmph,1)
    return kmph

def humedad_relativa(t,td):
    hr=(math.exp((17.625*td)/(243.04+td)))/(math.exp((17.625*t)/(243.04+t)))*100
    return round(min(hr,100),0)
################################################################################

# fecha del corte de estaciones
fecha_i=datetime(a,m,d,h,0,0)
fecha_f=fecha_i+timedelta(hours=nh)
dif=fecha_f-fecha_i

fechas=[]
for j in range(int(dif.days)+1):
    fechas.append(datetime(a,m,d)+timedelta(days=j))


c = cdsapi.Client()
for i in range(int(dif.days)+1):
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'area': [
                lat, lon, lat, lon,
            ],
            'variable': [
                '10m_u_component_of_wind', '10m_v_component_of_wind', '2m_dewpoint_temperature',
                '2m_temperature', 'total_precipitation',
            ],
            'year': datetime.strftime(fechas[i],'%Y'),
            'month': datetime.strftime(fechas[i],'%m'),
            'day': datetime.strftime(fechas[i],'%d'),
            'time': [
                '00:00', '01:00', '02:00',
                '03:00', '04:00', '05:00',
                '06:00', '07:00', '08:00',
                '09:00', '10:00', '11:00',
                '12:00', '13:00', '14:00',
                '15:00', '16:00', '17:00',
                '18:00', '19:00', '20:00',
                '21:00', '22:00', '23:00',
            ],
        },
        'download' + str(i)+'.nc')


date=[]
for k in range((int(dif.days)+1)*24):
    date.append(fechas[0]+timedelta(hours=k))

angulo=[]
velocidad=[]
temperatura=[]
HR=[]

for j in range(int(dif.days)+1):
    ds = nc.Dataset('download' + str(0) + '.nc')

    comp_v = ds["v10"][:, :, :]
    comp_u = ds["u10"][:, :, :]
    temp = ds["t2m"][:, :, :] - 273.15
    dew = ds["d2m"][:, :, :] - 273.15

    for i in range(len(comp_v)):
        # angulo
        alfa = angulo_c2f(comp_u[i], comp_v[i])
        angulo.append(alfa)
        # magnitud
        mag = magnitud(comp_u[i], comp_v[i])
        velocidad.append(mps_kmph(mag))
        # temperatura
        temperatura.append(round(float(temp[i]), 1))
        # humedad
        hr = humedad_relativa(temp[i], dew[i])
        HR.append(round(hr, 1))

if  sc==1:
    dato = pd.DataFrame()
    df= pd.DataFrame()
    dato.index = date
    dato["Scenario"]=["ERA 5"]*len(date)
    dato["datetime"]=date
    dato["WS"] = velocidad
    dato["WD"] = angulo
    dato["TMP"] = temperatura
    dato["RH"] = HR
    df=dato.loc[fecha_i:fecha_f]
    df.to_csv("weather.csv",index=False)
    print("Su archivo weather.csv se guardo correctamente")
elif sc==2:
    dato = pd.DataFrame()
    df = pd.DataFrame()
    dato.index = date
    dato["Scenario"] = ["ERA 5"] * len(date)
    dato["datetime"] = date
    dato["WS"] = velocidad
    dato["WD"] = angulo
    dato["FireScenario"] = [FS] * len(date)
    df = dato.loc[fecha_i:fecha_f]
    df.to_csv("weather.csv", index=False)
    print("Su archivo weather.csv se guardo correctamente")

