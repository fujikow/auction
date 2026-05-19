import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from dotenv import load_dotenv
from keep_alive import keep_alive

# Carrega o token com segurança do arquivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuração do Bot e Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Cor padrão dos Embeds (Azul)
COR_TEMA = discord.Color.from_rgb(13, 148, 230) 

# Estado Global do Leilão
leilao_atual = {
    'ativo': False,
    'item': None,
    'qtd_participantes': 0,
    'fim': None,
    'maior_lance': 0,
    'ganhador': None,
    'canal_id': None,
    'lang': 'pt'
}

# Dicionário de Traduções
LANGUAGES = {
    'pt': {
        'in_progress': "Já existe um leilão em andamento!",
        'need_participants': "Informe a quantidade de pessoas para dividir! Ex: `!iniciar_leilao \"Item Excelente\" 5`",
        'started_title': "🎉 LEILÃO INICIADO! 🎉",
        'started_desc': "**Item:** {item}\n**Divisão:** {qtd} participantes\n**Fim:** 24 horas a partir do último lance!\n\nUse `!lance <valor>` ou `!bid <valor>` para apostar.",
        'no_active': "Não há nenhum leilão ativo no momento.",
        'higher_bid': "{author}, o lance mínimo agora é **{min_bid}** (+1% sobre o atual de {current_bid}).",
        'bid_accepted': "🔨 **LANCE ACEITO!** {author} apostou **{amount}** pelo item **{item}**!\n⏳ *O relógio foi reiniciado para 24 horas!*",
        'outbid_dm': "⚠️ **Leilão:** Você foi ultrapassado no item **{item}**! O novo lance maior é de **{new_amount}**. Volte ao servidor para cobrir a oferta!",
        'no_bids': "O leilão do item **{item}** foi encerrado sem nenhum lance. 😢",
        'ended_title': "🎊 LEILÃO ENCERRADO! 🎊",
        'ended_desc': "**Item:** {item}\n**Ganhador:** {winner} com **{amount}**!\n\n💰 **Divisão:**\nTotal de Participantes: {qtd}\nCada membro recebe: **{split_amount}**",
        'invalid_value': "Insira um valor válido. Ex: `500`, `500k` ou `500 k`"
    },
    'en': {
        'in_progress': "There is already an auction in progress!",
        'need_participants': "Specify the number of participants! Ex: `!start_auction \"Excellent Item\" 5`",
        'started_title': "🎉 AUCTION STARTED! 🎉",
        'started_desc': "**Item:** {item}\n**Division:** {qtd} participants\n**End:** 24 hours from the last bid!\n\nUse `!bid <amount>` to place a bid.",
        'no_active': "No active auction at the moment.",
        'higher_bid': "{author}, the minimum bid is now **{min_bid}** (+1% over the current {current_bid}).",
        'bid_accepted': "🔨 **BID ACCEPTED!** {author} bid **{amount}** for **{item}**!\n⏳ *The clock has been reset to 24 hours!*",
        'outbid_dm': "⚠️ **Auction:** You have been outbid on **{item}**! The new highest bid is **{new_amount}**. Return to the server to outbid them!",
        'no_bids': "The auction for **{item}** ended with no bids. 😢",
        'ended_title': "🎊 AUCTION ENDED! 🎊",
        'ended_desc': "**Item:** {item}\n**Winner:** {winner} with **{amount}**!\n\n💰 **Division:**\nTotal Participants: {qtd}\nEach member receives: **{split_amount}**",
        'invalid_value': "Enter a valid amount. Ex: `500`, `500k` or `500 k`"
    },
    'vi': {
        'in_progress': "Đã có một cuộc đấu giá đang diễn ra!",
        'need_participants': "Chỉ định số lượng người tham gia! VD: `!batdaudaugia \"Vật phẩm\" 5`",
        'started_title': "🎉 BẮT ĐẦU ĐẤU GIÁ! 🎉",
        'started_desc': "**Vật phẩm:** {item}\n**Chia cho:** {qtd} người\n**Kết thúc:** 24 giờ kể từ lần đặt cược cuối!\n\nSử dụng `!datcuoc <giá_trị>` để đặt cược.",
        'no_active': "Hiện không có cuộc đấu giá nào.",
        'higher_bid': "{author}, mức giá tối thiểu hiện là **{min_bid}** (+1% so với mức hiện tại {current_bid}).",
        'bid_accepted': "🔨 **CHẤP NHẬN ĐẶT CƯỢC!** {author} đặt **{amount}** cho **{item}**!\n⏳ *Đồng hồ đã được đặt lại thành 24 giờ!*",
        'outbid_dm': "⚠️ **Đấu giá:** Bạn đã bị trả giá cao hơn cho **{item}**! Mức giá mới là **{new_amount}**. Hãy quay lại máy chủ để đặt cược!",
        'no_bids': "Cuộc đấu giá cho **{item}** kết thúc mà không có lượt đặt cược. 😢",
        'ended_title': "🎊 KẾT THÚC ĐẤU GIÁ! 🎊",
        'ended_desc': "**Vật phẩm:** {item}\n**Người thắng:** {winner} với **{amount}**!\n\n💰 **Chia Lợi Nhuận:**\nTổng người tham gia: {qtd}\nMỗi người nhận: **{split_amount}**",
        'invalid_value': "Nhập số tiền hợp lệ. VD: `500`, `500k` hoặc `500 k`"
    }
}

# --- EVENTOS ---
@bot.event
async def on_ready():
    print(f'✅ Bot conectado com sucesso como {bot.user}')
    verificar_leilao.start()

# --- COMANDOS ---
@bot.command(name='iniciar_leilao', aliases=['start_auction', 'batdaudaugia'])
@commands.has_any_role(1488536207091830835, 1487999133351542825, 1488536371537907752) 
async def iniciar_leilao(ctx, item: str, qtd_participantes: int = 0):
    global leilao_atual
    
    comando = ctx.invoked_with.lower()
    if comando == 'start_auction': lang = 'en'
    elif comando == 'batdaudaugia': lang = 'vi'
    else: lang = 'pt'

    textos = LANGUAGES[lang]
    
    if leilao_atual['ativo']:
        await ctx.send(textos['in_progress'])
        return
        
    if qtd_participantes <= 0:
        await ctx.send(textos['need_participants'])
        return

    leilao_atual.update({
        'ativo': True,
        'item': item,
        'qtd_participantes': qtd_participantes,
        'fim': datetime.now() + timedelta(hours=24),
        'maior_lance': 0,
        'ganhador': None,
        'canal_id': ctx.channel.id,
        'lang': lang
    })
    
    embed = discord.Embed(
        title=textos['started_title'],
        description=textos['started_desc'].format(item=item, qtd=qtd_participantes),
        color=COR_TEMA
    )
    await ctx.send(embed=embed)

@iniciar_leilao.error
async def iniciar_leilao_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ Você não tem permissão. É necessário o cargo de `Organizador`.")

# O comando continua aceitando !lance, !bid e !datcuoc
@bot.command(name='lance', aliases=['bid', 'datcuoc'])
async def lance(ctx, *, valor_str: str):
    global leilao_atual
    lang = leilao_atual.get('lang', 'pt')
    textos = LANGUAGES[lang]
    
    if not leilao_atual['ativo']:
        await ctx.send(textos['no_active'])
        return

    valor_limpo = valor_str.lower().replace(" ", "")
    multiplicador = 1000 if valor_limpo.endswith('k') else 1
    if multiplicador == 1000:
        valor_limpo = valor_limpo[:-1]
        
    try:
        valor = float(valor_limpo) * multiplicador
    except ValueError:
        await ctx.send(f"{ctx.author.mention}, {textos['invalid_value']}")
        return

    # --- REGRA DO INCREMENTO DE 1% ---
    if leilao_atual['maior_lance'] == 0:
        lance_minimo = 1 # O primeiro lance só precisa ser maior que zero
    else:
        # Calcula 1% a mais do lance atual (1.01)
        lance_minimo = leilao_atual['maior_lance'] * 1.01

    if valor < lance_minimo:
        lance_atual_fmt = f"{leilao_atual['maior_lance']:,.0f}".replace(",", ".")
        lance_minimo_fmt = f"{lance_minimo:,.0f}".replace(",", ".")
        await ctx.send(textos['higher_bid'].format(
            author=ctx.author.mention, 
            min_bid=lance_minimo_fmt, 
            current_bid=lance_atual_fmt
        ))
        return
    # ---------------------------------

    antigo_ganhador = leilao_atual['ganhador']
    leilao_atual['maior_lance'] = valor
    leilao_atual['ganhador'] = ctx.author

    # Renova o tempo para 24h
    leilao_atual['fim'] = datetime.now() + timedelta(hours=24)

    valor_fmt = f"{valor:,.0f}".replace(",", ".")
    
    if antigo_ganhador is not None and antigo_ganhador != ctx.author:
        try:
            texto_dm = textos['outbid_dm'].format(item=leilao_atual['item'], new_amount=valor_fmt)
            await antigo_ganhador.send(texto_dm)
        except discord.Forbidden:
            pass 

    await ctx.send(textos['bid_accepted'].format(
        author=ctx.author.mention, amount=valor_fmt, item=leilao_atual['item']
    ))

# --- ROTINAS DE FUNDO ---
@tasks.loop(seconds=10)
async def verificar_leilao():
    global leilao_atual
    if not leilao_atual['ativo'] or datetime.now() < leilao_atual['fim']:
        return

    canal = bot.get_channel(leilao_atual['canal_id'])
    lang = leilao_atual.get('lang', 'pt')
    textos = LANGUAGES[lang]
    
    leilao_atual['ativo'] = False
    
    if leilao_atual['ganhador'] is None:
        await canal.send(textos['no_bids'].format(item=leilao_atual['item']))
        return

    valor_total = leilao_atual['maior_lance']
    parte_por_pessoa = valor_total / leilao_atual['qtd_participantes']

    valor_total_fmt = f"{valor_total:,.0f}".replace(",", ".")
    parte_pessoa_fmt = f"{parte_por_pessoa:,.0f}".replace(",", ".")

    embed = discord.Embed(
        title=textos['ended_title'],
        description=textos['ended_desc'].format(
            item=leilao_atual['item'], 
            winner=leilao_atual['ganhador'].mention, 
            amount=valor_total_fmt,
            qtd=leilao_atual['qtd_participantes'],
            split_amount=parte_pessoa_fmt
        ),
        color=COR_TEMA
    )
    await canal.send(embed=embed)

# --- EXECUÇÃO ---
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)