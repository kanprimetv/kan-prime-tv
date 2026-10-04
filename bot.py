import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# Mini servidor web falso para o Render ficar feliz com a porta
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Inicia o mini servidor em segundo plano
threading.Thread(target=run_server, daemon=True).start()

# Token atualizado do BotFather e WhatsApp
TOKEN = "7963363319:AAEzRz60gqE04K3g8gX4q2JzI"
bot = telebot.TeleBot(TOKEN)

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Botões do menu principal com URL direta corrigida
    btn_planos = types.InlineKeyboardButton("📦 Ver Planos / Assinar", callback_data="planos")
    btn_suporte = types.InlineKeyboardButton("💬 Falar com Suporte", url="https://wa.me/5565999023982")
    
    markup.add(btn_planos, btn_suporte)
    
    texto_b_vindas = (
        "Seja muito bem-vindo ao **KAN PRIME TV**! 📺✨\n\n"
        "Escolha uma das opções abaixo para continuar:"
    )
    
    bot.send_message(message.chat.id, texto_b_vindas, parse_mode="Markdown", reply_markup=markup)

# Ação dos botões em linha
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "planos":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id, 
            "📦 **Nossos Planos:**\n\nEntre em contato pelo suporte para garantir sua assinatura de TV via streaming com acesso imediato!\n\n👉 [Clique aqui para falar no WhatsApp](https://wa.me/5565999023982)", 
            parse_mode="Markdown"
        )

# Mantém o bot rodando 24 horas
print("Bot e servidor web iniciados com sucesso!")
bot.infinity_polling()
