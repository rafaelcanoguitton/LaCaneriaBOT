from logging import PlaceHolder
import os
import threading
import time
import psycopg2
from geopy.geocoders import Nominatim
from telebot import TeleBot, types
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
app = TeleBot(os.getenv('TELEGRAMKEY'))  # Telegram Bot
chat_aidi = []  # Where we'll store our authorized chats
con = psycopg2.connect(os.getenv('DATABASEURI'))
global stlen
stlen = 0
geolocator = Nominatim(user_agent="la rosquita")
# Menu Principal
main_markup = types.ReplyKeyboardMarkup(row_width=3)
menu1 = types.KeyboardButton('Ordenes activas')
menu2 = types.KeyboardButton('Confirmar orden')
menu3 = types.KeyboardButton('Cancelar orden')
main_markup.add(menu1, menu2, menu3)


@app.message_handler(commands=['start'])
def start(message):
    benvenuti = "Bienvenido al administrador de la app" + "\n" + "Pizzería - la Cañería" + \
        "\n" + "\n" + "Por favor ingrese la contraseña de seguridad:"
    msg = app.send_message(message.chat.id, benvenuti)
    app.register_next_step_handler(msg, paso_passwd)


def paso_passwd(message):
    if(message.text == os.getenv('CONTRASEÑA')):
        chat_aidi.append(message.chat.id)
        app.send_message(message.chat.id, "Acceso concedido",
                         reply_markup=main_markup)
        print(chat_aidi)
    else:
        app.send_message(message.chat.id, "Acceso Denegado")


@app.message_handler(content_types=['text'])
def flujo_principal(message):
    # VALIDACION
    if message.chat.id in chat_aidi:
        if message.text == "Confirmar orden":
            cur = con.cursor()
            cur.execute("SELECT * from pedido where estado='activo'")
            rows = cur.fetchall()
            if(len(rows) == 0):
                app.send_message(message.chat.id, "No hay ordenes activas")
            # Armar ordenes a la verga
            else:
                markup = types.ReplyKeyboardMarkup(row_width=3)
                cont = 1
                mes = "**¿Qué orden desea confirmar?**\n\n"
                for row in rows:
                    cur.execute(
                        "SELECT * from pedido where id_usuario="+row[7])
                    nombre = cur.fetchall()
                    mes += str(cont)+". "+"Nombre: "+nombre[0][4]+"\n"
                    markup.add(types.KeyboardButton(str(cont)))
                    cont += 1
                markup.add(types.KeyboardButton('Salir'))
                msg = app.send_message(
                    message.chat.id, mes, reply_markup=markup)
                app.register_next_step_handler(msg, confirmar)
            # continuar flujo
        elif message.text == "Ordenes activas":
            cur = con.cursor()
            cur.execute("SELECT * from pedido where estado='activo'")
            rows = cur.fetchall()
            if(len(rows) == 0):
                app.send_message(message.chat.id, "No hay ordenes activas")
            else:
                for row in reversed(rows):
                    cur.execute(
                        "SELECT * from pedido where id_usuario="+row[7])
                    nombre = cur.fetchall()
                    men = "Nuevo pedido\n\n"
                    men += "Nombre: "+nombre[0][4]+"\n"
                    direc = get_address(row[3], row[4])
                    men += "[Direccion: "+direc + \
                        "](https://www.google.com/maps/@" + \
                           row[3]+","+row[4]+"\n\n"
                    items = query(row[0])
                    for item in items:
                        men += "**"+item[0]+":**\n"
                        men += +item[1]+"\n"
                        men += +item[2]+"\n"
                        men += +item[3]+"\n"
                        men += +item[4]+"\n"
                        men += +item[5]+"\n\n"
                app.send_message(message.chat.id, men,
                                 reply_markup=main_markup)
        elif message.text == "Cancelar orden":
            cur = con.cursor()
            cur.execute("SELECT * from pedido where estado='activo'")
            rows = cur.fetchall()
            if(len(rows) == 0):
                app.send_message(message.chat.id, "No hay ordenes activas")
            else:
                markup = types.ReplyKeyboardMarkup(row_width=3)
                cont = 1
                mes = "**¿Qué orden desea cancelar?**\n\n"
                for row in rows:
                    cur.execute(
                        "SELECT * from pedido where id_usuario="+row[7])
                    nombre = cur.fetchall()
                    mes += str(cont)+". "+"Nombre: "+nombre[0][4]+"\n"
                    markup.add(types.KeyboardButton(str(cont)))
                    cont += 1
                markup.add(types.KeyboardButton('Salir'))
                msg = app.send_message(
                    message.chat.id, mes, reply_markup=main_markup)
                app.register_next_step_handler(msg, confirmar)
    else:
        app.send_message(
            message.chat.id, 'Lo siento, este bot sólo está disponible para administradores de la pizzería la cañería')


def confirmar(message):
    if (message.text == "Salir"):
        app.send_message(message.chat.id, "Menu principal",
                         reply_markup=main_markup)
    else:
        cur = con.cursor()
        cur.execute("SELECT * from pedido where estado='activo'")
        rows = cur.fetchall()
        index = int(message.text)
        id_pedido = rows[index-1][0]
        cur.execute(
            "UPDATE pedido SET estado='confirmado' WHERE id_pedido="+id_pedido)
        app.send_message(message.chat.id, "Orden confirmada!!!",
                         reply_markup=main_markup)


def cancelar(message):
    if (message.text == "Salir"):
        app.send_message(message.chat.id, "Menu principal",
                         reply_markup=main_markup)
    else:
        cur = con.cursor()
        cur.execute("SELECT * from pedido where estado='activo'")
        rows = cur.fetchall()
        index = int(message.text)
        id_pedido = rows[index-1][0]
        cur.execute(
            "UPDATE pedido SET estado='cancelado' WHERE id_pedido="+id_pedido)
        app.send_message(message.chat.id, "Orden cancelada.",
                         reply_markup=main_markup)


def query(id_pedido):
    cur1 = con.cursor()
    cur1.execute("SELECT * from items where id_pedido="+id_pedido)
    return cur1.fetchall()


def get_address(longitud, latitud):
    coordinates = longitud+","+latitud
    location = geolocator.reverse(coordinates)
    adress = location.adress
    placeh = ""
    countcomas = 0
    for i in adress:
        if(i == ","):
            countcomas += 1
        if(countcomas == 3):
            break
        placeh += i
    return placeh


def refresh():
    global stlen
    while True:
        cur = con.cursor()
        cur.execute("SELECT * from pedido where estado='activo'")
        rows = cur.fetchall()
        if(len(rows) != stlen):
            newpedidos = len(rows)-stlen
            count = 0
            for row in reversed(rows):
                if(count == newpedidos):
                    break
                else:
                    cur.execute("SELECT * from pedido where id_usuario="+row[7])
                    nombre = cur.fetchall()
                    men = "Nuevo pedido\n\n"
                    men += "Nombre: "+nombre[0][4]+"\n"
                    direc = get_address(row[3], row[4])
                    men += "[Direccion: "+direc + \
                        "](https://www.google.com/maps/@"+row[3]+","+row[4]+"\n\n"
                    items = query(row[0])
                    for item in items:
                        men += "**"+item[0]+":**\n"
                        men += +item[1]+"\n"
                        men += +item[2]+"\n"
                        men += +item[3]+"\n"
                        men += +item[4]+"\n"
                        men += +item[5]+"\n\n"
                    count+=1
            for i in range(len(chat_aidi)):
                app.send_message(chat_aidi[i], men)
            stlen = len(rows)
        time.sleep(3)


if __name__ == '__main__':
    t1 = threading.Thread(target=refresh)
    t1.start()
    app.polling(none_stop=True)
