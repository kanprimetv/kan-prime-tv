# ==============================================================================
# ROBÔ KAN PRIME TV - CÓDIGO OFICIAL CONFIGURADO COM PAINEL ADMIN E MENU
# ==============================================================================

import logging
import sqlite3
import urllib.parse
from datetime import datetime
import telebot
from telebot import types

TELEGRAM_TOKEN = "8978752644:AAEM7WVauyyhfk1mfUt6Oqy3y4_ca4hjJhk"
ADMIN_CHAT_ID = 8340417920
BOT_USERNAME = "KanPrimetvOficial_Bot"
PRECO_MENSALIDADE = 35.00
CHAVE_PIX_OFICIAL = "5fd7dc9f-fd1b-4f55-8eb6-7d0026654860"

BONUS_NIVEIS = {
    1: 8.00,
    2: 2.00,
    3: 1.50,
    4: 1.00,
    5: 0.50
}

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    me = bot.get_me()
    BOT_USERNAME = me.username
    print(f"✅ Conectado com sucesso ao bot: @{BOT_USERNAME}")
except Exception as err:
    BOT_USERNAME = "KanPrimetvOficial_Bot"
    print(f"Conexão inicial: {err}")

try:
    bot.set_my_commands([
        types.BotCommand("start", "👑 Iniciar / Menu Principal"),
        types.BotCommand("painel", "💼 Meu Painel de Afiliado e Saldo"),
        types.BotCommand("admin", "👑 Painel Master (Exclusivo Admin)")
    ])
    print("✅ Menu de comandos configurado com sucesso!")
except Exception as e:
    print(f"Erro ao configurar menu: {e}")

DB_NAME = "kan_prime_tv.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            phone TEXT,
            device TEXT,
            sponsor_id INTEGER,
            balance REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 0,
            joined_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            device TEXT,
            phone TEXT,
            status TEXT DEFAULT 'PENDENTE_PAGAMENTO',
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            pix_key TEXT,
            status TEXT DEFAULT 'PENDENTE',
            requested_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, first_name, username, phone, device, sponsor_id, balance, is_active FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "first_name": row[1],
            "username": row[2],
            "phone": row[3],
            "device": row[4],
            "sponsor_id": row[5],
            "balance": row[6],
            "is_active": row[7]
        }
    return None

def register_user(user_id: int, first_name: str, username: str, sponsor_id: int = None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, first_name, username, sponsor_id, joined_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, first_name, username or "", sponsor_id, now))
    conn.commit()
    conn.close()

def distribute_commissions(buyer_user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT sponsor_id, first_name FROM users WHERE user_id = ?", (buyer_user_id,))
    buyer = cursor.fetchone()
    if not buyer or not buyer[0]:
        conn.close()
        return

    current_sponsor_id = buyer[0]
    buyer_name = buyer[1] or "Novo Assinante"

    for level in range(1, 6):
        if not current_sponsor_id:
            break
        bonus = BONUS_NIVEIS.get(level, 0.0)
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bonus, current_sponsor_id))
        try:
            bot.send_message(
                current_sponsor_id,
                f"🎉 <b>Bônus de Rede Creditado!</b>\n\n"
                f"👤 <b>Origem:</b> {buyer_name} (Nível {level})\n"
                f"💰 <b>Valor Recebido:</b> R$ {bonus:.2f}\n\n"
                f"Acompanhe seu saldo digitando /painel."
            )
        except Exception:
            pass
        cursor.execute("SELECT sponsor_id FROM users WHERE user_id = ?", (current_sponsor_id,))
        row = cursor.fetchone()
        current_sponsor_id = row[0] if row else None

    conn.commit()
    conn.close()

@bot.message_handler(commands=['admin'])
def handle_admin(message: types.Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "❌ Comando exclusivo do Administrador Master.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    total_active = cursor.fetchone()[0]
    
    cursor.execute("SELECT user_id, first_name, username, phone, device, sponsor_id, is_active FROM users ORDER BY joined_at DESC LIMIT 20")
    recent_users = cursor.fetchall()
    conn.close()

    admin_text = (
        f"👑 <b>PAINEL DO ADMINISTRADOR MASTER</b> 👑\n\n"
        f"👥 <b>Total Cadastrados na Base:</b> {total_users}\n"
        f"🟢 <b>Clientes Ativos (Pagantes):</b> {total_active}\n"
        f"⏳ <b>Aguardando Assinatura:</b> {total_users - total_active}\n\n"
        f"📋 <b>Últimos Clientes Cadastrados (Rede):</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    for u in recent_users:
        u_id, fname, uname, phone, dev, sponsor, active = u
        status_icon = "✅ Ativo" if active == 1 else "⏳ Pendente"
        sponsor_text = f"Indicação ID: {sponsor}" if sponsor else "Cadastro Direto (Raiz)"
        admin_text += (
            f"👤 <b>{fname}</b> (@{uname or 'sem'})\n"
            f"🆔 ID: <code>{u_id}</code> | Status: {status_icon}\n"
            f"📱 Tel: {phone or 'Não inf.'} | TV: {dev or 'Não inf.'}\n"
            f"🔗 {sponsor_text}\n"
            f"----------------------------------------\n"
        )

    bot.send_message(message.chat.id, admin_text)

@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    sponsor_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            potential_sponsor = int(args[1].replace("ref_", ""))
            if potential_sponsor != user_id:
                sponsor_id = potential_sponsor
        except ValueError:
            pass

    existing_user = get_user(user_id)
    if not existing_user:
        register_user(user_id, first_name, username, sponsor_id)
        if sponsor_id:
            try:
                bot.send_message(
                    sponsor_id,
                    f"🤝 <b>Novo Convidado na sua Rede!</b>\n\n"
                    f"O usuário <b>{first_name}</b> acabou de entrar pelo seu link de convite."
                )
            except Exception:
                pass

    welcome_text = (
        f"👑 <b>BEM-VINDO À KAN PRIME TV</b> 👑\n"
        f"<i>Streaming Premium e Renda Recorrente</i>\n\n"
        f"Olá, <b>{first_name}</b>!\n"
        f"Canais em alta resolução, filmes e séries para Smart TV, Celular, TV Box e PC.\n\n"
        f"💰 <b>Mensalidade:</b> R$ {PRECO_MENSALIDADE:.2f}\n"
        f"🎁 <b>Ganhe R$ 8,00</b> por cada amigo que você indicar!\n\n"
        f"Selecione uma opção abaixo para começar:"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_assinar = types.InlineKeyboardButton("📺 Assinar Agora (R$ 35,00)", callback_data="assinar_passo1")
    btn_painel = types.InlineKeyboardButton("💼 Meu Painel de Afiliado", callback_data="abrir_painel")
    btn_suporte = types.InlineKeyboardButton("💬 Falar com Suporte", callback_data="abrir_suporte")
    markup.add(btn_assinar, btn_painel, btn_suporte)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "assinar_passo1")
def callback_escolher_dispositivo(call: types.CallbackQuery):
    text = (
        "📺 <b>QUAL APARELHO VOCÊ VAI USAR?</b>\n\n"
        "Selecione o seu aparelho principal:"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("Smart TV Samsung", callback_data="dev_Samsung")
    b2 = types.InlineKeyboardButton("Smart TV LG", callback_data="dev_LG")
    b3 = types.InlineKeyboardButton("TV Box / Fire Stick", callback_data="dev_TVBox")
    b4 = types.InlineKeyboardButton("Celular Android/iOS", callback_data="dev_Mobile")
    b5 = types.InlineKeyboardButton("Computador / PC", callback_data="dev_PC")
    b6 = types.InlineKeyboardButton("Outra Marca", callback_data="dev_Outro")
    markup.add(b1, b2, b3, b4, b5, b6)

    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dev_"))
def callback_coletar_contato(call: types.CallbackQuery):
    device_chosen = call.data.replace("dev_", "")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET device = ? WHERE user_id = ?", (device_chosen, call.from_user.id))
    conn.commit()
    conn.close()

    msg = bot.send_message(
        call.message.chat.id,
        f"📱 Aparelho: <b>{device_chosen}</b>\n\n"
        f"Digite seu <b>WhatsApp com DDD</b> (ex: <code>11987654321</code>) para enviarmos os dados de instalação:"
    )
    bot.register_next_step_handler(msg, process_phone_step, device_chosen)

def process_phone_step(message: types.Message, device_chosen: str):
    phone = message.text.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    user_id = message.from_user.id
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO orders (user_id, amount, device, phone, status, created_at)
        VALUES (?, ?, ?, ?, 'PENDENTE', ?)
    """, (user_id, PRECO_MENSALIDADE, device_chosen, phone, now))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    pix_text = (
        f"💳 <b>PEDIDO GERADO COM SUCESSO! (Nº #{order_id})</b>\n\n"
        f"👤 <b>Cliente:</b> {message.from_user.first_name}\n"
        f"📺 <b>Aparelho:</b> {device_chosen}\n"
        f"📱 <b>WhatsApp:</b> {phone}\n"
        f"💰 <b>Valor:</b> R$ {PRECO_MENSALIDADE:.2f}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 <b>CHAVE PIX OFICIAL (Toque para copiar):</b>\n\n"
        f"<code>{CHAVE_PIX_OFICIAL}</code>\n\n"
        f"<i>Abra o aplicativo do seu banco, faça a transferência PIX no valor de R$ {PRECO_MENSALIDADE:.2f} e clique no botão abaixo para confirmar:</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_confirmar = types.InlineKeyboardButton("✅ Já Realizei o Pagamento PIX", callback_data=f"confirmar_pix_{order_id}")
    markup.add(btn_confirmar)

    bot.send_message(message.chat.id, pix_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirmar_pix_"))
def callback_confirmar_pagamento(call: types.CallbackQuery):
    order_id = int(call.data.replace("confirmar_pix_", ""))
    user_id = call.from_user.id
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, device, phone, status FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    
    if not order or order[3] == "PAGO":
        bot.answer_callback_query(call.id, "Este pedido já foi registrado!")
        conn.close()
        return

    cursor.execute("UPDATE orders SET status = 'PAGO' WHERE id = ?", (order_id,))
    cursor.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    distribute_commissions(user_id)

    bot.edit_message_text(
        "🎉 <b>PAGAMENTO CONFIRMADO!</b>\n\n"
        "Seu pedido foi registrado em nossa fila de atendimento!\n"
        "Nosso suporte master entrará em contato em instantes no seu WhatsApp para ativar seus canais.\n\n"
        "💡 <i>Você já pode indicar amigos e ganhar R$ 8,00 por indicação! Digite /painel para ver seu link.</i>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )

    device = order[1]
    phone = order[2]
    msg_padrao = f"Olá! Aqui é o suporte KAN PRIME TV. Recebemos seu pagamento de R$ 35,00 para {device}. Vamos fazer sua instalação agora!"
    link_whatsapp = f"https://wa.me/55{phone}?text={urllib.parse.quote(msg_padrao)}"

    admin_alert = (
        f"🚨 <b>NOVA INSTALAÇÃO PENDENTE! (Pedido #{order_id})</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Cliente:</b> {call.from_user.first_name}\n"
        f"📱 <b>WhatsApp:</b> {phone}\n"
        f"📺 <b>Aparelho:</b> {device}\n"
        f"💰 <b>Status:</b> ✅ PAGO (R$ {PRECO_MENSALIDADE:.2f})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    markup_admin = types.InlineKeyboardMarkup(row_width=1)
    btn_wa = types.InlineKeyboardButton("📲 Chamar no WhatsApp", url=link_whatsapp)
    markup_admin.add(btn_wa)

    try:
        bot.send_message(ADMIN_CHAT_ID, admin_alert, reply_markup=markup_admin)
    except Exception as e:
        logging.error(f"Erro ao notificar admin: {e}")

@bot.message_handler(commands=['painel'])
@bot.callback_query_handler(func=lambda call: call.data == "abrir_painel")
def handle_painel(event):
    is_callback = isinstance(event, types.CallbackQuery)
    user_id = event.from_user.id
    chat_id = event.message.chat.id if is_callback else event.chat.id

    user = get_user(user_id)
    if not user:
        register_user(user_id, event.from_user.first_name, event.from_user.username)
        user = get_user(user_id)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE sponsor_id = ?", (user_id,))
    total_diretos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE sponsor_id = ? AND is_active = 1", (user_id,))
    diretos_ativos = cursor.fetchone()[0]
    conn.close()

    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"

    painel_text = (
        f"💼 <b>PAINEL DO AFILIADO - KAN PRIME TV</b>\n\n"
        f"👤 <b>Nome:</b> {user['first_name']}\n"
        f"🟢 <b>Status:</b> {'Ativo ✅' if user['is_active'] else 'Aguardando Assinatura ⏳'}\n"
        f"💰 <b>Saldo Disponível:</b> R$ {user['balance']:.2f}\n\n"
        f"👥 <b>Sua Rede:</b>\n"
        f"• Indicados Diretos: <b>{total_diretos}</b> ({diretos_ativos} ativos)\n"
        f"• Ganho por Direto: <b>R$ {BONUS_NIVEIS[1]:.2f} / mês</b>\n\n"
        f"🔗 <b>Seu Link de Indicação:</b>\n"
        f"<code>{referral_link}</code>"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_saque = types.InlineKeyboardButton("💸 Solicitar Saque PIX", callback_data="solicitar_saque")
    markup.add(btn_saque)

    if is_callback:
        bot.edit_message_text(painel_text, chat_id=chat_id, message_id=event.message.message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, painel_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "solicitar_saque")
def callback_solicitar_saque(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    if not user or user["balance"] < 50.00:
        bot.answer_callback_query(call.id, f"Saldo mínimo para saque é R$ 50,00. Saldo atual: R$ {user['balance']:.2f}.", show_alert=True)
        return

    msg = bot.send_message(
        call.message.chat.id,
        f"💸 Saldo disponível: <b>R$ {user['balance']:.2f}</b>\n\nDigite a sua Chave PIX:"
    )
    bot.register_next_step_handler(msg, process_withdrawal_pix, user["balance"])

def process_withdrawal_pix(message: types.Message, amount: float):
    pix_key = message.text.strip()
    user_id = message.from_user.id

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO withdrawals (user_id, amount, pix_key, requested_at) VALUES (?, ?, ?, ?)", (user_id, amount, pix_key, now))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"✅ Saque solicitado no valor de R$ {amount:.2f} para a chave PIX: {pix_key}")
    bot.send_message(ADMIN_CHAT_ID, f"💸 Pedido de Saque:\nUsuário: {message.from_user.first_name} (ID: {user_id})\nValor: R$ {amount:.2f}\nChave PIX: {pix_key}")

@bot.callback_query_handler(func=lambda call: call.data == "abrir_suporte")
def callback_suporte(call: types.CallbackQuery):
    bot.edit_message_text("💬 Para suporte, entre em contato direto com o administrador.", chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == "__main__":
    print("🚀 BOT KAN PRIME TV INICIADO COM MENU DE COMANDOS!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Erro de conexão detectado: {e}. Reconectando em 5 segundos...")
            import time
            time.sleep(5)
