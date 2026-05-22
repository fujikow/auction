import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

COR_TEMA = discord.Color.from_rgb(13, 148, 230) 
COR_ERRO = discord.Color.red()

leilao_atual = {
    'ativo': False,
    'item': None,
    'qtd_participantes': 0,
    'fim': None,
    'maior_lance': 0,
    'ganhador': None,
    'canal_id': None,
    'thread_id': None
}

LANGUAGES = {
    'pt': {
        'in_progress': "Já existe um leilão em andamento!",
        'need_participants': "Informe a divisão! Ex: `!iniciar_leilao \"Item\" 5`",
        'started': "**Item:** {item} | **Divisão:** {qtd} membros\n**Fim:** 24h após o último lance. Use `!lance <valor>`",
        'no_active': "Não há nenhum leilão ativo no momento.",
        'higher_bid': "{author}, lance mínimo: **{min_bid}** (+1% sobre {current_bid}).",
        'bid_accepted': "🔨 {author} apostou **{amount}** em **{item}**!\n⏳ *Relógio reiniciado para 24h!*",
        'outbid_dm': "⚠️ Você foi ultrapassado em **{item}**! Novo lance: **{new_amount}**.",
        'no_bids': "O leilão de **{item}** encerrou sem lances. 😢",
        'ended': "**Item:** {item} | **Ganhador:** {winner} ({amount})\n📉 *Taxa do Jogo (1%): -{tax}*\n💰 {qtd} membros recebem **{split_amount}** cada.",
        'invalid_value': "Valor inválido. Ex: `500k`",
        'cancelled': "🛑 O leilão de **{item}** foi cancelado.",
        'timeleft': "⏳ Faltam **{horas}h {minutos}m** para o fim do leilão."
    },
    'en': {
        'in_progress': "There's already an active auction!",
        'need_participants': "Specify division! Ex: `!start_auction \"Item\" 5`",
        'started': "**Item:** {item} | **Split:** {qtd} members\n**End:** 24h after last bid. Use `!bid <amount>`",
        'no_active': "No active auction at the moment.",
        'higher_bid': "{author}, minimum bid: **{min_bid}** (+1% over {current_bid}).",
        'bid_accepted': "🔨 {author} bid **{amount}** for **{item}**!\n⏳ *Clock reset to 24h!*",
        'outbid_dm': "⚠️ You've been outbid on **{item}**! New bid: **{new_amount}**.",
        'no_bids': "Auction for **{item}** ended with no bids. 😢",
        'ended': "**Item:** {item} | **Winner:** {winner} ({amount})\n📉 *Game Tax (1%): -{tax}*\n💰 {qtd} members receive **{split_amount}** each.",
        'invalid_value': "Invalid amount. Ex: `500k`",
        'cancelled': "🛑 Auction for **{item}** was cancelled.",
        'timeleft': "⏳ **{horas}h {minutos}m** left until auction ends."
    },
    'vi': {
        'in_progress': "Đang có một phiên đấu giá diễn ra!",
        'need_participants': "Chỉ định số người chia! VD: `!batdaudaugia \"Vật phẩm\" 5`",
        'started': "**Vật phẩm:** {item} | **Chia cho:** {qtd} người\n**Kết thúc:** 24h sau lượt đặt cuối. Dùng `!datcuoc <giá>`",
        'no_active': "Hiện không có đấu giá nào.",
        'higher_bid': "{author}, mức tối thiểu: **{min_bid}** (+1% của {current_bid}).",
        'bid_accepted': "🔨 {author} đặt **{amount}** cho **{item}**!\n⏳ *Gia hạn thành 24h!*",
        'outbid_dm': "⚠️ Bạn đã bị vượt giá cho **{item}**! Giá mới: **{new_amount}**.",
        'no_bids': "Đấu giá **{item}** kết thúc không có lượt đặt. 😢",
        'ended': "**Vật phẩm:** {item} | **Thắng:** {winner} ({amount})\n📉 *Thuế (1%): -{tax}*\n💰 {qtd} người nhận **{split_amount}** mỗi người.",
        'invalid_value': "Giá trị không hợp lệ. VD: `500k`",
        'cancelled': "🛑 Đấu giá cho **{item}** đã bị hủy.",
        'timeleft': "⏳ Còn lại **{horas}h {minutos}m** cho đến khi kết thúc."
    }
}

def gerar_mensagem_tri(chave, **kwargs):
    pt = f"🇧🇷 {LANGUAGES['pt'][chave].format(**kwargs)}"
    en = f"🇺🇸 {LANGUAGES['en'][chave].format(**kwargs)}"
    vi = f"🇻🇳 {LANGUAGES['vi'][chave].format(**kwargs)}"
    return f"{pt}\n\n{en}\n\n{vi}"

CARGOS_ORG = (1488536207091830835, 1487999133351542825, 1488536371537907752)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado: {bot.user}')
    if not verificar_leilao.is_running():
        verificar_leilao.start()

@bot.command(name='iniciar_leilao', aliases=['start_auction', 'batdaudaugia'])
@commands.has_any_role(*CARGOS_ORG) 
async def iniciar_leilao(ctx, item: str, qtd_participantes: int = 0):
    global leilao_atual
    
    if leilao_atual['ativo']:
        await ctx.send(gerar_mensagem_tri('in_progress'))
        return
        
    if qtd_participantes <= 0:
        await ctx.send(gerar_mensagem_tri('need_participants'))
        return

    embed = discord.Embed(
        title="🎉 LEILÃO INICIADO | AUCTION STARTED | BẮT ĐẦU ĐẤU GIÁ 🎉",
        description=gerar_mensagem_tri('started', item=item, qtd=qtd_participantes),
        color=COR_TEMA
    )
    
    mensagem_painel = await ctx.send(embed=embed)
    topico = await mensagem_painel.create_thread(name=f"🔨 Leilão: {item}", auto_archive_duration=1440)

    leilao_atual.update({
        'ativo': True,
        'item': item,
        'qtd_participantes': qtd_participantes,
        'fim': datetime.now() + timedelta(hours=24),
        'maior_lance': 0,
        'ganhador': None,
        'canal_id': ctx.channel.id,
        'thread_id': topico.id
    })

@iniciar_leilao.error
async def iniciar_leilao_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ Acesso Negado / Access Denied / Truy cập bị từ chối")

@bot.command(name='cancelar_leilao', aliases=['cancel_auction', 'huydaugia'])
@commands.has_any_role(*CARGOS_ORG) 
async def cancelar_leilao(ctx):
    global leilao_atual
    
    if not leilao_atual['ativo']:
        await ctx.send(gerar_mensagem_tri('no_active'))
        return

    nome_item = leilao_atual['item']
    id_topico = leilao_atual['thread_id']
    leilao_atual['ativo'] = False
    
    embed = discord.Embed(
        title="🛑 LEILÃO CANCELADO | CANCELLED | HỦY BỎ",
        description=gerar_mensagem_tri('cancelled', item=nome_item),
        color=COR_ERRO
    )
    
    topico = bot.get_channel(id_topico)
    if topico:
        await topico.send(embed=embed)
        await topico.edit(locked=True, archived=True)
    
    await ctx.send(embed=embed)

@bot.command(name='tempo', aliases=['timeleft', 'thoigian'])
async def tempo_restante(ctx):
    if not leilao_atual['ativo']:
        await ctx.send(gerar_mensagem_tri('no_active'))
        return

    restante = leilao_atual['fim'] - datetime.now()
    horas, resto = divmod(int(restante.total_seconds()), 3600)
    minutos, _ = divmod(resto, 60)

    await ctx.send(gerar_mensagem_tri('timeleft', horas=horas, minutos=minutos))

@bot.command(name='lance', aliases=['bid', 'datcuoc'])
async def lance(ctx, *, valor_str: str):
    global leilao_atual
    
    if not leilao_atual['ativo']:
        await ctx.send(gerar_mensagem_tri('no_active'))
        return

    if ctx.channel.id != leilao_atual['thread_id']:
        aviso = "⚠️ 🇧🇷 Lances apenas no tópico oficial!\n🇺🇸 Bids only in the official thread!\n🇻🇳 Chỉ đặt cược trong chủ đề chính thức!"
        await ctx.message.delete()
        await ctx.send(aviso, delete_after=10)
        return

    valor_limpo = valor_str.lower().replace(" ", "")
    multiplicador = 1000 if valor_limpo.endswith('k') else 1
    if multiplicador == 1000:
        valor_limpo = valor_limpo[:-1]
        
    try:
        valor = float(valor_limpo) * multiplicador
    except ValueError:
        await ctx.send(f"{ctx.author.mention}\n" + gerar_mensagem_tri('invalid_value'))
        return

    lance_minimo = 1 if leilao_atual['maior_lance'] == 0 else leilao_atual['maior_lance'] * 1.01

    if valor < lance_minimo:
        lance_atual_fmt = f"{leilao_atual['maior_lance']:,.0f}".replace(",", ".")
        lance_minimo_fmt = f"{lance_minimo:,.0f}".replace(",", ".")
        await ctx.send(gerar_mensagem_tri('higher_bid', author=ctx.author.mention, min_bid=lance_minimo_fmt, current_bid=lance_atual_fmt))
        return

    antigo_ganhador = leilao_atual['ganhador']
    leilao_atual['maior_lance'] = valor
    leilao_atual['ganhador'] = ctx.author
    leilao_atual['fim'] = datetime.now() + timedelta(hours=24)

    valor_fmt = f"{valor:,.0f}".replace(",", ".")
    
    if antigo_ganhador is not None and antigo_ganhador != ctx.author:
        try:
            texto_dm = gerar_mensagem_tri('outbid_dm', item=leilao_atual['item'], new_amount=valor_fmt)
            await antigo_ganhador.send(texto_dm)
        except discord.Forbidden:
            pass 

    await ctx.send(gerar_mensagem_tri('bid_accepted', author=ctx.author.mention, amount=valor_fmt, item=leilao_atual['item']))

@tasks.loop(seconds=10)
async def verificar_leilao():
    global leilao_atual
    if not leilao_atual['ativo'] or datetime.now() < leilao_atual['fim']:
        return

    topico = bot.get_channel(leilao_atual['thread_id'])
    leilao_atual['ativo'] = False
    
    if leilao_atual['ganhador'] is None:
        if topico:
            await topico.send(gerar_mensagem_tri('no_bids', item=leilao_atual['item']))
            await topico.edit(locked=True, archived=True)
        return

    # === CÁLCULO ATUALIZADO DA TAXA DE 1% ===
    valor_total = leilao_atual['maior_lance']
    taxa_jogo = valor_total * 0.01
    valor_liquido = valor_total - taxa_jogo
    parte_por_pessoa = valor_liquido / leilao_atual['qtd_participantes']

    valor_total_fmt = f"{valor_total:,.0f}".replace(",", ".")
    taxa_fmt = f"{taxa_jogo:,.0f}".replace(",", ".")
    parte_pessoa_fmt = f"{parte_por_pessoa:,.0f}".replace(",", ".")

    embed = discord.Embed(
        title="🎊 LEILÃO ENCERRADO | AUCTION ENDED | KẾT THÚC ĐẤU GIÁ 🎊",
        description=gerar_mensagem_tri('ended', 
            item=leilao_atual['item'], 
            winner=leilao_atual['ganhador'].mention, 
            amount=valor_total_fmt,
            tax=taxa_fmt,
            qtd=leilao_atual['qtd_participantes'],
            split_amount=parte_pessoa_fmt
        ),
        color=COR_TEMA
    )
    
    if topico:
        await topico.send(embed=embed)
        await topico.edit(locked=True, archived=True)

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)