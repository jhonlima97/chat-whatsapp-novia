import pandas as pd
import re
import json
import regex
import demoji
import numpy as np
from collections import Counter
import plotly.express as px
import matplotlib.pyplot as plt
from PIL import Image
from wordcloud import WordCloud, STOPWORDS

# Importacnion de streamlit
import streamlit as st

#################################################################
# Título de la aplicación
st.title('Análisis de nuestro chat WhatsApp ❤️')
st.write('Creado por [Jhonsito Lima](https://github.com/jhonlima97) para [Gabriela Santilán:](https://www.linkedin.com/in/marigabysc/)')
##################################################################

##########################################
# ### Paso 1: Definir funciones necesarias
##########################################

# Patron regex para identificar el comienzo de cada línea del txt con la fecha y la hora
def IniciaConFechaYHora(s):
    # Ejemplo: '9/16/23, 5:59 PM - ...'
    patron = '^([1-9]|1[0-2])(\/)([1-9]|1[0-9]|2[0-9]|3[0-1])(\/)(2[0-9]), ([0-9]+):([0-9][0-9])\s?([AP][M]) -'
    resultado = re.match(patron, s)  # Verificar si cada línea del txt hace match con el patrón de fecha y hora
    if resultado:
        return True
    return False

# Patrón para encontrar a los miembros del grupo dentro del txt
def EncontrarMiembro(s):
    patrones = ['Jhonsito 👨‍🎓:','Fresita ❤️:']

    patron = '^' + '|'.join(patrones)
    resultado = re.match(patron, s)  # Verificar si cada línea del txt hace match con el patrón de miembro
    if resultado:
        return True
    return False

# Separar las partes de cada línea del txt: Fecha, Hora, Miembro y Mensaje
def ObtenerPartes(linea):
    # Ejemplo: '9/16/23, 5:59 PM - Jhon Lima: Todos debemos aprender a analizar datos'
    splitLinea = linea.split(' - ')
    FechaHora = splitLinea[0]                     # '9/16/23, 5:59 PM'
    splitFechaHora = FechaHora.split(', ')
    Fecha = splitFechaHora[0]                    # '9/16/23'
    Hora = ' '.join(splitFechaHora[1:])          # '5:59 PM'
    Mensaje = ' '.join(splitLinea[1:])             # 'Jhon Lima: Todos debemos aprender a analizar datos'
    if EncontrarMiembro(Mensaje):
        splitMensaje = Mensaje.split(': ')
        Miembro = splitMensaje[0]               # 'Jhon Lima'
        Mensaje = ' '.join(splitMensaje[1:])    # 'Todos debemos aprender a analizar datos'
    else:
        Miembro = None       
    return Fecha, Hora, Miembro, Mensaje

##################################################################################
# ### Paso 2: Obtener el dataframe usando el dataset y las funciones definidas
##################################################################################

# Leer el archivo txt descargado del chat de WhatsApp
RutaChat = 'data/2_chat-with-Fresita❤️.txt'

# Lista para almacenar los datos (Fecha, Hora, Miembro, Mensaje) de cada línea del txt
DatosLista = []
with open(RutaChat, encoding="utf-8") as fp:
    fp.readline() # Eliminar primera fila relacionada al cifrado de extremo a extremo
    Fecha, Hora, Miembro = None, None, None
    while True:
        linea = fp.readline()
        if not linea:
            break
        linea = linea.strip()
        if IniciaConFechaYHora(linea): # Si cada línea del txt coincide con el patrón fecha y hora
            Fecha, Hora, Miembro, Mensaje = ObtenerPartes(linea) # Obtener datos de cada línea del txt
            DatosLista.append([Fecha, Hora, Miembro, Mensaje])

# Convertir la lista con los datos a dataframe
df = pd.DataFrame(DatosLista, columns=['Fecha', 'Hora', 'Miembro', 'Mensaje'])

# Cambiar la columna Fecha a formato datetime
df['Fecha'] = pd.to_datetime(df['Fecha'], format="%m/%d/%y")

# Eliminar los posibles campos vacíos del dataframe
# y lo que no son mensajes como cambiar el asunto del grupo o agregar a alguien
df = df.dropna()

# Resetear el índice
df.reset_index(drop=True, inplace=True)

# #### Filtrar el chat por fecha de acuerdo a lo requerido
start_date = '2023-01-01'
end_date = '2024-02-01'

df = df[(df['Fecha'] >= start_date) & (df['Fecha'] <= end_date)]

##################################################################
# ### Paso 3: Estadísticas de mensajes, multimedia, emojis y links
##################################################################

# #### Total de mensajes, multimedia, emojis y links enviados
def ObtenerEmojis(Mensaje):
    emoji_lista = []
    data = regex.findall(r'\X', Mensaje)  # Obtener lista de caracteres de cada mensaje
    for caracter in data:
        if demoji.replace(caracter) != caracter:
            emoji_lista.append(caracter)
    return emoji_lista

# Obtener la cantidad total de mensajes
total_mensajes = df.shape[0]

# Obtener la cantidad de archivos multimedia enviados
multimedia_mensajes = df[df['Mensaje'] == '<Media omitted>'].shape[0]

# Obtener la cantidad de emojis enviados
df['Emojis'] = df['Mensaje'].apply(ObtenerEmojis) # Se agrega columna 'Emojis'
emojis = sum(df['Emojis'].str.len())

# Obtener la cantidad de links enviados
url_patron = r'(https?://\S+)'
df['URLs'] = df.Mensaje.apply(lambda x: len(re.findall(url_patron, x))) # Se agrega columna 'URLs'
links = sum(df['URLs'])

# Obtener la cantidad de encuestas
encuestas = df[df['Mensaje'] == 'POLL:'].shape[0]

# Todos los datos pasarlo a diccionario
estadistica_dict = {'Tipo': ['Mensajes', 'Multimedia', 'Emojis', 'Links', 'Encuestas'],
        'Cantidad': [total_mensajes, multimedia_mensajes, emojis, links, encuestas]
        }

#Convertir diccionario a dataframe
estadistica_df = pd.DataFrame(estadistica_dict, columns = ['Tipo', 'Cantidad'])

# Establecer la columna Tipo como índice
estadistica_df = estadistica_df.set_index('Tipo')

###################################
###################################
st.header('💡 Estadísticas generales')
col1, col2 = st.beta_columns([1, 2])

with col1:
    st.write(estadistica_df)
###################################
###################################

# #### Emojis más usados

# Obtener emojis más usados y las cantidades en el chat del grupo del dataframe
emojis_lista = list([a for b in df.Emojis for a in b])
emoji_dic = dict(Counter(emojis_lista))
emoji_dic = sorted(emoji_dic.items(), key=lambda x: x[1], reverse=True)

# Convertir el diccionario a dataframe
emoji_df = pd.DataFrame(emoji_dic, columns=['Emoji', 'Cantidad'])

# Añadir una columna de ID incremental
emoji_df = emoji_df.reset_index()
emoji_df['index'] = emoji_df['index'] + 1  # Hacer que los IDs empiecen en 1 en lugar de 0

# Renombrar las columnas
emoji_df = emoji_df.rename(columns={'index': 'ID', 'Emoji': 'Emoji', 'Cantidad': 'Cantidad'})


# Establecer la columna Emoji como índice
emoji_df = emoji_df.head(10)
#emoji_df = emoji_df.set_index('Emoji').head(10)

# Plotear el pie de los emojis más usados
fig = px.pie(emoji_df, values='Cantidad', names=emoji_df.Emoji, hole=.3, template='plotly_dark', color_discrete_sequence=px.colors.qualitative.Pastel2)
fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=20)

# Ajustar el gráfico
fig.update_layout(showlegend=False)
# fig.show()

#### Paso 4: Estadísticas de los miembros del chat
# Agregar una columna 'Links' al DataFrame original df
df['Links'] = df['Mensaje'].apply(lambda x: len(re.findall(url_patron, x)))

# Calcular el número total de mensajes por miembro, incluyendo mensajes de texto, emojis, multimedia y enlaces
df_mActivos = df.groupby('Miembro').agg({
    'Mensaje': 'count', 
    'Emojis': lambda x: sum(len(emojis) for emojis in x),
    'Links': 'sum'  # Agregar la suma de enlaces por miembro
})
df_mActivos.reset_index(inplace=True)

# Sumar los diferentes tipos de mensajes para obtener el número total de mensajes por miembro
df_mActivos['# mensajes'] = df_mActivos['Mensaje'] + df_mActivos['Emojis'] + df_mActivos['Links']

# Calcular el porcentaje de mensajes para cada miembro
df_mActivos['% Mensajes'] = (df_mActivos['# mensajes'] / df_mActivos['# mensajes'].sum()) * 100

# Seleccionar solo las columnas necesarias
df_mActivos = df_mActivos[['Miembro', '# mensajes', '% Mensajes']]

# Renombrar las columnas
df_mActivos = df_mActivos.rename(columns={'Miembro': 'Miembro', '# mensajes': '# Mensajes', '% Mensajes': '% Mensajes'})

# Ordenar por el número de mensajes en orden descendente
df_mActivos = df_mActivos.sort_values(by='# Mensajes', ascending=False)

# Restablecer el índice
df_mActivos.reset_index(drop=True, inplace=True)

# Mostrar el DataFrame corregido
with col2:
    st.write(df_mActivos)
###################################

# Separar mensajes (sin multimedia) y multimedia (stickers, fotos, videos)
multimedia_df = df[df['Mensaje'] == '<Media omitted>']
mensajes_df = df.drop(multimedia_df.index)
# Contar la cantidad de palabras y letras por mensaje
mensajes_df['Letras'] = mensajes_df['Mensaje'].apply(lambda s : len(s))
mensajes_df['Palabras'] = mensajes_df['Mensaje'].apply(lambda s : len(s.split(' ')))
# mensajes_df.tail()

# Obtener a todos los miembros
miembros = mensajes_df.Miembro.unique()

# Crear diccionario donde se almacenará todos los datos
dic = {}

for i in range(len(miembros)):
    lista = []
    # Filtrar mensajes de un miembro en específico
    miembro_df= mensajes_df[mensajes_df['Miembro'] == miembros[i]]

    # Agregar a la lista el número total de mensajes enviados
    lista.append(miembro_df.shape[0])
    
    # Agregar a la lista el número de palabras por total de mensajes (palabras por mensaje)
    palabras_por_msj = (np.sum(miembro_df['Palabras']))/miembro_df.shape[0]
    lista.append(palabras_por_msj)

    # Agregar a la lista el número de mensajes multimedia enviados
    multimedia = multimedia_df[multimedia_df['Miembro'] == miembros[i]].shape[0]
    lista.append(multimedia)

    # Agregar a la lista el número total de emojis enviados
    emojis = sum(miembro_df['Emojis'].str.len())
    lista.append(emojis)

    # Agregar a la lista el número total de links enviados
    links = sum(miembro_df['URLs'])
    lista.append(links)

    # Asignar la lista como valor a la llave del diccionario
    dic[miembros[i]] = lista

# Convertir el diccionario a una cadena JSON
json_str = json.dumps(dic, ensure_ascii=False)

# Convertir de diccionario a dataframe
miembro_stats_df = pd.DataFrame.from_dict(dic)

# Cambiar el índice por la columna agregada 'Estadísticas'
estadísticas = ['Mensajes', 'Palabras por mensaje', 'Multimedia', 'Emojis', 'Links']
miembro_stats_df['Estadísticas'] = estadísticas
miembro_stats_df.set_index('Estadísticas', inplace=True)

# Transponer el dataframe
miembro_stats_df = miembro_stats_df.T

#Convertir a integer las columnas Mensajes, Multimedia Emojis y Links
miembro_stats_df['Mensajes'] = miembro_stats_df['Mensajes'].apply(int)
miembro_stats_df['Multimedia'] = miembro_stats_df['Multimedia'].apply(int)
miembro_stats_df['Emojis'] = miembro_stats_df['Emojis'].apply(int)
miembro_stats_df['Links'] = miembro_stats_df['Links'].apply(int)
miembro_stats_df = miembro_stats_df.sort_values(by=['Mensajes'], ascending=False)

###################################
###################################
st.subheader('Cómo se distribuyen nuestros mensajes 👀')
st.write(miembro_stats_df)
###################################
st.header('🤗 Emojis más usados con mi novia')
col1, col2 = st.beta_columns([1, 2])

with col1:
    st.write(emoji_df)

with col2:
    st.plotly_chart(fig)
###################################

# ### Paso 5: Estadísticas del comportamiento del grupo

df['rangoHora'] = pd.to_datetime(df['Hora'], format='%I:%M %p')

# Define a function to create the "Range Hour" column
def create_range_hour(hour):
    hour = pd.to_datetime(hour)
    start_hour = hour.hour
    end_hour = (hour + pd.Timedelta(hours=1)).hour
    return f'{start_hour:02d} - {end_hour:02d} h'

# # Apply the function to create the "Range Hour" column
df['rangoHora'] = df['rangoHora'].apply(create_range_hour)
df['DiaSemana'] = df['Fecha'].dt.strftime('%A')
mapeo_dias_espanol = {'Monday': 'Lunes','Tuesday': 'Martes','Wednesday': 'Miércoles','Thursday': 'Jueves',
                      'Friday': 'Viernes','Saturday': 'Sábado','Sunday': 'Domingo'}
df['DiaSemana'] = df['DiaSemana'].map(mapeo_dias_espanol)

# #### Número de mensajes por rango de hora

# Crear una columna de 1 para realizar el conteo de mensajes
df['# Mensajes por hora'] = 1

# Sumar (contar) los mensajes que tengan la misma fecha
date_df = df.groupby('rangoHora').count().reset_index()

# Plotear la cantidad de mensajes respecto del tiempo
fig = px.line(date_df, x='rangoHora', y='# Mensajes por hora', color_discrete_sequence=['salmon'], template='plotly_dark')

# Ajustar el gráfico
fig.update_traces(mode='markers+lines', marker=dict(size=10))
fig.update_xaxes(title_text='Rango de hora', tickangle=30)
fig.update_yaxes(title_text='# Mensajes')
# fig.show()

###################################
st.header('⏰ Mensajes por hora')
st.plotly_chart(fig)
###################################

# #### Número de mensajes por día

# Crear una columna de 1 para realizar el conteo de mensajes
df['# Mensajes por día'] = 1

# Sumar (contar) los mensajes que tengan la misma fecha
date_df = df.groupby('DiaSemana').count().reset_index()


# Plotear la cantidad de mensajes respecto del tiempo
fig = px.line(date_df, x='DiaSemana', y='# Mensajes por día', color_discrete_sequence=['salmon'], template='plotly_dark')

fig.update_traces(mode='markers+lines', marker=dict(size=10))
fig.update_xaxes(title_text='Día', tickangle=30)
fig.update_yaxes(title_text='# Mensajes')
# fig.show()

###################################
###################################
st.header('📆 Mensajes por día')
st.plotly_chart(fig)
###################################
###################################

# #### Número de mensajes a través del tiempo

# Crear una columna de 1 para realizar el conteo de mensajes
df['# Mensajes por día'] = 1

# Sumar (contar) los mensajes que tengan la misma fecha
#date_df = df.groupby('Fecha').sum().reset_index()
date_df = df.groupby('Fecha').sum(numeric_only=True).reset_index()

# Plotear la cantidad de mensajes respecto del tiempo
fig = px.line(date_df, x='Fecha', y='# Mensajes por día', color_discrete_sequence=['salmon'], template='plotly_dark')

fig.update_xaxes(title_text='Fecha', tickangle=45, nticks=35)
fig.update_yaxes(title_text='# Mensajes')
# fig.show()

###################################
###################################
st.header('📈 Mensajes a lo largo del tiempo')
st.plotly_chart(fig)
###################################
###################################

# #### Word Cloud de palabras más usadas

# Crear un string que contendrá todas las palabras
total_palabras = ' '
stopwords = STOPWORDS.update(['que', 'qué', 'con', 'de', 'te', 'en', 'la', 'lo', 'le', 'el', 'las', 'los', 'les', 'por', 'es',
                              'son', 'se', 'para', 'un', 'una', 'chicos', 'su', 'si', 'chic','nos', 'ya', 'hay', 'esta',
                              'pero', 'del', 'mas', 'más', 'eso', 'este', 'como', 'así', 'todo', 'https','Media','omitted',
                              'y', 'mi', 'o', 'q', 'yo', 'al', 'ok'])

mask = np.array(Image.open('resources/heart.jpg'))

# Obtener y acumular todas las palabras de cada mensaje
for mensaje in mensajes_df['Mensaje'].values:
    palabras = str(mensaje).lower().split() # Obtener las palabras de cada línea del txt
    for palabra in palabras:
        total_palabras = total_palabras + palabra + ' ' # Acumular todas las palabras

wordcloud = WordCloud(width = 800, height = 800, background_color ='black', stopwords = stopwords,
                      max_words=100, min_font_size = 5,
                      mask = mask, colormap='OrRd',).generate(total_palabras)

# Plotear la nube de palabras más usadas
###################################
st.header('☁️ Nuestro word cloud')
st.image(wordcloud.to_array(), caption='Palabras que más usamos con mi Fresita ❤️', use_column_width=True)
###################################