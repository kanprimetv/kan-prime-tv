import telebot
from telebot import types

# Token atualizado do BotFather
TOKEN = "7963363319:AAEzRz60gqE04K3g8gX4q2JzI"
bot = telebot.TeleBot(TOKEN)

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Botão de planos e suporte direto para o WhatsApp 5565999023982
    btn_planos = types.InlineKeyboardButton("📦 Ver Planos / Assinar", callback_data="planos")
    btn_suporte = types.InlineKeyboardButton("💬 Falar com Suporte", url="https://wa.me/5565999023982")
    
    markup.add(btn_planos, btn_suporte)
    
    texto_boas_vindas = (
        "Seja muito bem-vindo ao **KAN PRIME TV**! 📺✨\n\n"
        "Escolha uma das opções abaixo para continuar:"
    )
    
    bot.send_message(message.chat.id, texto_boas_vindas, parse_mode="Markdown", reply_markup=markup)

# Ação dos botões em linha
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "planos":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id, 
            "📦 **Nossos Planos:**\n\nEntre em contato pelo suporte para garantir sua assinatura de TV via streaming com acesso imediato!\n\n👉 [Falar no WhatsApp com o Suporte](https://wa.me/5565999023982)", 
            parse_mode="Markdown"
        )

# Mantém o bot rodando 24 horas
print("Bot iniciado com sucesso!")
bot.infinity_polling()
